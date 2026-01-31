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
from services.ray_service import ray_service
from services.docker_orchestrator import docker_orchestrator
from core.config import settings
from core.exceptions import MCPOrchestratorException, InsufficientCapacityException


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
    
    async def _select_node_with_capacity(self, required_cpu: int, required_memory: int) -> str:
        """
        요청한 리소스를 제공할 수 있는 워커 노드를 선택합니다.
        
        Ray SDK를 통해 충분한 용량이 있는 노드를 찾습니다.
        단, 등록된 Worker 노드 중에서만 선택합니다.
        
        Args:
            required_cpu: 필요한 CPU 코어 수
            required_memory: 필요한 메모리 (GB)
            
        Returns:
            str: 선택된 노드 ID
            
        Raises:
            InsufficientCapacityException: 충분한 용량이 없을 때
        """
        # 먼저 등록된 Worker 노드 목록 조회
        workers = await node_manager.get_nodes_by_role(NodeRole.WORKER)
        
        if not workers:
            raise MCPOrchestratorException(
                message="No available worker nodes",
                detail="There are no worker nodes registered in the cluster."
            )
        
        # Worker 노드 IP 집합
        worker_ips = {w.tailscale_ip for w in workers}
        worker_by_ip = {w.tailscale_ip: w for w in workers}
        
        # Ray에서 노드별 가용 리소스 조회
        try:
            ray_nodes = ray_service.get_nodes_with_available_resources()
            
            # Worker 노드 중에서 요청 리소스를 충족하는 노드 찾기
            capable_workers = []
            for ray_node in ray_nodes:
                node_ip = ray_node.get("node_ip")
                cpu_avail = ray_node.get("cpu_available", 0)
                mem_avail = ray_node.get("memory_available_gb", 0)
                
                # Worker 노드이고 용량 충족하는 경우
                if node_ip in worker_ips and cpu_avail >= required_cpu and mem_avail >= required_memory:
                    capable_workers.append({
                        "worker": worker_by_ip[node_ip],
                        "cpu_available": cpu_avail,
                        "memory_available": mem_avail
                    })
            
            if capable_workers:
                # CPU 가장 여유로운 노드 선택
                best = max(capable_workers, key=lambda x: x["cpu_available"])
                return best["worker"].id
            
            # 용량 충족 노드 없음 - Worker 중 최대 용량 조회
            max_cpu = 0
            max_mem = 0
            for ray_node in ray_nodes:
                if ray_node.get("node_ip") in worker_ips:
                    max_cpu = max(max_cpu, ray_node.get("cpu_available", 0))
                    max_mem = max(max_mem, ray_node.get("memory_available_gb", 0))
            
            raise InsufficientCapacityException(
                requested_cpu=required_cpu,
                requested_memory=required_memory,
                max_cpu_available=int(max_cpu),
                max_memory_available=int(max_mem)
            )
            
        except InsufficientCapacityException:
            raise
        except Exception as e:
            print(f"Ray capacity check failed, using fallback: {e}")
            # Ray 실패 시 랜덤 선택 (용량 체크 불가)
            return random.choice(workers).id
    
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
            InsufficientCapacityException: 클러스터 용량 부족 시
        """
        # 쿼터 확인
        quota_check = await quota_service.check_quota(user_id, request.cpu, request.memory)
        
        if not quota_check["allowed"]:
            raise QuotaExceededException(quota_check.get("reason", "Quota exceeded"))
        
        # 용량 기반 노드 선택 (InsufficientCapacity 발생 가능)
        node_id = await self._select_node_with_capacity(request.cpu, request.memory)
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
        
        # Docker 컨테이너 배포
        try:
            deploy_result = await docker_orchestrator.deploy_container(
                node_ip=node.tailscale_ip,
                image=request.image,
                port=port,
                container_name=f"mcp-{instance.id}",
                cpu_limit=float(request.cpu),
                memory_limit=f"{request.memory}g",
                user_id=user_id,
                instance_id=instance.id
            )
            
            if deploy_result.get("success"):
                instance.status = InstanceStatus.RUNNING
                instance.started_at = datetime.now()
                instance.container_id = deploy_result.get("container_id")
            else:
                # 배포 실패 시 리소스 롤백
                await quota_service.release_resources(user_id, request.cpu, request.memory)
                await port_allocator.release_port(node_id, instance.id)
                raise MCPOrchestratorException(
                    message="Container deployment failed",
                    detail=deploy_result.get("error", "Unknown error")
                )
        except MCPOrchestratorException:
            raise
        except Exception as e:
            # 배포 실패 시 리소스 롤백
            await quota_service.release_resources(user_id, request.cpu, request.memory)
            await port_allocator.release_port(node_id, instance.id)
            raise MCPOrchestratorException(
                message="Container deployment failed",
                detail=str(e)
            )
        
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
