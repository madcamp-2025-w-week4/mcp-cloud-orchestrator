# ============================================================================
# MCP Cloud Orchestrator - 인스턴스 관리 서비스
# ============================================================================
# 설명: 사용자 컨테이너 인스턴스의 CRUD 및 생명주기 관리
# ============================================================================

import json
import aiofiles
import random
from pathlib import Path
from typing import Optional
from datetime import datetime

from models.instance import Instance, InstanceCreate, InstanceStatus, InstanceSummary
from models.node import NodeRole
from services.node_manager import node_manager
from services.port_allocator import port_allocator
from services.quota_service import quota_service
from core.config import settings
from core.exceptions import MCPOrchestratorException


class InstanceNotFoundException(MCPOrchestratorException):
    """인스턴스를 찾을 수 없을 때 발생하는 예외"""
    
    def __init__(self, instance_id: str):
        super().__init__(
            message=f"Instance not found: {instance_id}",
            detail=f"The requested instance '{instance_id}' does not exist."
        )
        self.instance_id = instance_id


class QuotaExceededException(MCPOrchestratorException):
    """쿼터 초과 시 발생하는 예외"""
    
    def __init__(self, reason: str):
        super().__init__(
            message="Quota exceeded",
            detail=reason
        )


class InstanceManager:
    """
    인스턴스 관리 서비스 클래스
    
    사용자 인스턴스의 생성, 조회, 중지, 종료를 관리합니다.
    소유권 기반 접근 제어를 적용합니다.
    """
    
    def __init__(self, instances_file_path: str = None):
        """
        InstanceManager 초기화
        
        Args:
            instances_file_path: 인스턴스 정보 JSON 파일 경로
        """
        self.instances_file_path = Path(
            instances_file_path or 
            str(Path(settings.nodes_file_path).parent / "instances.json")
        )
        self._instances_cache: dict = {}
    
    async def _ensure_file_exists(self) -> None:
        """인스턴스 파일이 존재하는지 확인하고, 없으면 생성합니다."""
        if not self.instances_file_path.exists():
            self.instances_file_path.parent.mkdir(parents=True, exist_ok=True)
            initial_data = {
                "metadata": {
                    "version": "1.0",
                    "updated_at": datetime.now().isoformat(),
                    "description": "인스턴스 데이터 저장소"
                },
                "instances": {}
            }
            async with aiofiles.open(self.instances_file_path, mode='w', encoding='utf-8') as f:
                await f.write(json.dumps(initial_data, indent=2, ensure_ascii=False))
    
    async def _load_instances(self) -> dict:
        """인스턴스 정보를 로드합니다."""
        await self._ensure_file_exists()
        
        async with aiofiles.open(self.instances_file_path, mode='r', encoding='utf-8') as f:
            content = await f.read()
            data = json.loads(content)
            self._instances_cache = data
            return data
    
    async def _save_instances(self, data: dict) -> None:
        """인스턴스 정보를 저장합니다."""
        data["metadata"]["updated_at"] = datetime.now().isoformat()
        
        async with aiofiles.open(self.instances_file_path, mode='w', encoding='utf-8') as f:
            await f.write(json.dumps(data, indent=2, ensure_ascii=False))
        
        self._instances_cache = data
    
    async def _select_node(self) -> str:
        """
        인스턴스를 배치할 워커 노드를 선택합니다.
        
        현재는 랜덤 선택, 추후 로드 밸런싱 로직 추가 가능
        
        Returns:
            str: 선택된 노드 ID
        """
        workers = await node_manager.get_nodes_by_role(NodeRole.WORKER)
        
        if not workers:
            raise MCPOrchestratorException(
                message="No available worker nodes",
                detail="There are no worker nodes registered in the cluster."
            )
        
        # 랜덤 선택 (추후 로드 밸런싱으로 개선 가능)
        selected = random.choice(workers)
        return selected.id
    
    async def create_instance(self, user_id: str, request: InstanceCreate) -> Instance:
        """
        새 인스턴스를 생성합니다.
        
        Args:
            user_id: 사용자 ID
            request: 인스턴스 생성 요청
            
        Returns:
            Instance: 생성된 인스턴스
            
        Raises:
            QuotaExceededException: 쿼터 초과 시
        """
        # 쿼터 확인
        quota_check = await quota_service.check_quota(user_id, request.cpu, request.memory)
        
        if not quota_check["allowed"]:
            raise QuotaExceededException(quota_check.get("reason", "Quota exceeded"))
        
        # 노드 선택
        node_id = await self._select_node()
        node = await node_manager.get_node(node_id)
        
        # 인스턴스 생성
        instance = Instance(
            name=request.name,
            image=request.image,
            user_id=user_id,
            node_id=node_id,
            port=0,  # 임시값, 아래에서 할당
            cpu=request.cpu,
            memory=request.memory,
            status=InstanceStatus.PENDING,
            public_ip=node.tailscale_ip,
            created_at=datetime.now()
        )
        
        # 포트 할당
        port = await port_allocator.allocate_port(node_id, instance.id)
        instance.port = port
        
        # 쿼터 사용량 업데이트
        await quota_service.allocate_resources(user_id, request.cpu, request.memory)
        
        # 인스턴스 상태를 RUNNING으로 변경 (실제로는 Docker 컨테이너 시작 후)
        instance.status = InstanceStatus.RUNNING
        instance.started_at = datetime.now()
        
        # 저장
        data = await self._load_instances()
        data["instances"][instance.id] = instance.model_dump(mode='json')
        await self._save_instances(data)
        
        return instance
    
    async def get_instance(self, instance_id: str, user_id: str = None) -> Instance:
        """
        인스턴스 정보를 조회합니다.
        
        Args:
            instance_id: 인스턴스 ID
            user_id: 사용자 ID (소유권 확인용, None이면 확인 안함)
            
        Returns:
            Instance: 인스턴스 정보
            
        Raises:
            InstanceNotFoundException: 인스턴스가 없거나 접근 권한이 없을 때
        """
        data = await self._load_instances()
        
        instance_data = data.get("instances", {}).get(instance_id)
        if not instance_data:
            raise InstanceNotFoundException(instance_id)
        
        instance = Instance(**instance_data)
        
        # 소유권 확인
        if user_id and instance.user_id != user_id:
            raise InstanceNotFoundException(instance_id)
        
        return instance
    
    async def get_user_instances(self, user_id: str) -> list[Instance]:
        """
        사용자의 모든 인스턴스를 조회합니다.
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            list[Instance]: 인스턴스 목록
        """
        data = await self._load_instances()
        
        instances = []
        for instance_data in data.get("instances", {}).values():
            if instance_data.get("user_id") == user_id:
                # terminated 상태가 아닌 것만
                if instance_data.get("status") != InstanceStatus.TERMINATED:
                    instances.append(Instance(**instance_data))
        
        # 생성 시간 역순 정렬
        instances.sort(key=lambda x: x.created_at, reverse=True)
        return instances
    
    async def get_all_instances(self) -> list[Instance]:
        """
        모든 인스턴스를 조회합니다 (관리자용).
        
        Returns:
            list[Instance]: 전체 인스턴스 목록
        """
        data = await self._load_instances()
        
        instances = []
        for instance_data in data.get("instances", {}).values():
            if instance_data.get("status") != InstanceStatus.TERMINATED:
                instances.append(Instance(**instance_data))
        
        instances.sort(key=lambda x: x.created_at, reverse=True)
        return instances
    
    async def stop_instance(self, instance_id: str, user_id: str) -> Instance:
        """
        인스턴스를 중지합니다.
        
        Args:
            instance_id: 인스턴스 ID
            user_id: 사용자 ID
            
        Returns:
            Instance: 업데이트된 인스턴스
        """
        instance = await self.get_instance(instance_id, user_id)
        
        if instance.status not in [InstanceStatus.RUNNING, InstanceStatus.PENDING]:
            raise MCPOrchestratorException(
                message="Cannot stop instance",
                detail=f"Instance is in '{instance.status}' state."
            )
        
        instance.status = InstanceStatus.STOPPED
        instance.stopped_at = datetime.now()
        
        # 저장
        data = await self._load_instances()
        data["instances"][instance_id] = instance.model_dump(mode='json')
        await self._save_instances(data)
        
        return instance
    
    async def start_instance(self, instance_id: str, user_id: str) -> Instance:
        """
        중지된 인스턴스를 시작합니다.
        
        Args:
            instance_id: 인스턴스 ID
            user_id: 사용자 ID
            
        Returns:
            Instance: 업데이트된 인스턴스
        """
        instance = await self.get_instance(instance_id, user_id)
        
        if instance.status != InstanceStatus.STOPPED:
            raise MCPOrchestratorException(
                message="Cannot start instance",
                detail=f"Instance is in '{instance.status}' state."
            )
        
        instance.status = InstanceStatus.RUNNING
        instance.started_at = datetime.now()
        instance.stopped_at = None
        
        # 저장
        data = await self._load_instances()
        data["instances"][instance_id] = instance.model_dump(mode='json')
        await self._save_instances(data)
        
        return instance
    
    async def terminate_instance(self, instance_id: str, user_id: str) -> bool:
        """
        인스턴스를 종료(삭제)합니다.
        
        Args:
            instance_id: 인스턴스 ID
            user_id: 사용자 ID
            
        Returns:
            bool: 성공 여부
        """
        instance = await self.get_instance(instance_id, user_id)
        
        # 포트 해제
        await port_allocator.release_port(instance.node_id, instance_id)
        
        # 쿼터 해제
        await quota_service.release_resources(user_id, instance.cpu, instance.memory)
        
        # 인스턴스 상태 업데이트 (삭제 표시)
        instance.status = InstanceStatus.TERMINATED
        
        data = await self._load_instances()
        data["instances"][instance_id] = instance.model_dump(mode='json')
        await self._save_instances(data)
        
        return True
    
    async def get_instance_count(self, user_id: str = None) -> int:
        """
        인스턴스 수를 반환합니다.
        
        Args:
            user_id: 사용자 ID (없으면 전체)
            
        Returns:
            int: 인스턴스 수
        """
        if user_id:
            instances = await self.get_user_instances(user_id)
        else:
            instances = await self.get_all_instances()
        
        return len([i for i in instances if i.status == InstanceStatus.RUNNING])
    
    async def get_instance_summary(self, user_id: str = None) -> dict:
        """
        인스턴스 요약 정보를 반환합니다.
        
        Args:
            user_id: 사용자 ID (없으면 전체)
            
        Returns:
            dict: 요약 정보
        """
        if user_id:
            instances = await self.get_user_instances(user_id)
        else:
            instances = await self.get_all_instances()
        
        running = len([i for i in instances if i.status == InstanceStatus.RUNNING])
        stopped = len([i for i in instances if i.status == InstanceStatus.STOPPED])
        pending = len([i for i in instances if i.status == InstanceStatus.PENDING])
        
        return {
            "total": len(instances),
            "running": running,
            "stopped": stopped,
            "pending": pending
        }


# 싱글톤 인스턴스
instance_manager = InstanceManager()
