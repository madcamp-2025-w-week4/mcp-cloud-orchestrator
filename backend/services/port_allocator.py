# ============================================================================
# MCP Cloud Orchestrator - 포트 할당 서비스
# ============================================================================
# 설명: 노드별 포트 할당 및 관리 서비스
#       각 노드에서 8000번 포트부터 순차적으로 할당
# ============================================================================

import json
import aiofiles
from pathlib import Path
from typing import Optional
from datetime import datetime

from core.config import settings


class PortAllocator:
    """
    포트 할당 서비스 클래스
    
    여러 사용자가 동일한 노드를 공유할 때 포트 충돌을 방지합니다.
    각 노드별로 8000번부터 시작하여 순차적으로 포트를 할당합니다.
    """
    
    # 포트 범위 설정
    PORT_START = 8000
    PORT_END = 9999
    
    def __init__(self, allocations_file_path: str = None):
        """
        PortAllocator 초기화
        
        Args:
            allocations_file_path: 포트 할당 정보 JSON 파일 경로
        """
        self.allocations_file_path = Path(
            allocations_file_path or 
            str(Path(settings.nodes_file_path).parent / "port_allocations.json")
        )
        self._allocations_cache: dict = {}
    
    async def _ensure_file_exists(self) -> None:
        """포트 할당 파일이 존재하는지 확인하고, 없으면 생성합니다."""
        if not self.allocations_file_path.exists():
            self.allocations_file_path.parent.mkdir(parents=True, exist_ok=True)
            initial_data = {
                "metadata": {
                    "version": "1.0",
                    "updated_at": datetime.now().isoformat(),
                    "description": "노드별 포트 할당 현황"
                },
                "allocations": {},
                "next_port_per_node": {}
            }
            async with aiofiles.open(self.allocations_file_path, mode='w', encoding='utf-8') as f:
                await f.write(json.dumps(initial_data, indent=2, ensure_ascii=False))
    
    async def _load_allocations(self) -> dict:
        """포트 할당 정보를 로드합니다."""
        await self._ensure_file_exists()
        
        async with aiofiles.open(self.allocations_file_path, mode='r', encoding='utf-8') as f:
            content = await f.read()
            self._allocations_cache = json.loads(content)
            return self._allocations_cache
    
    async def _save_allocations(self, data: dict) -> None:
        """포트 할당 정보를 저장합니다."""
        data["metadata"]["updated_at"] = datetime.now().isoformat()
        
        async with aiofiles.open(self.allocations_file_path, mode='w', encoding='utf-8') as f:
            await f.write(json.dumps(data, indent=2, ensure_ascii=False))
        
        self._allocations_cache = data
    
    async def allocate_port(self, node_id: str, instance_id: str) -> int:
        """
        노드에 새 포트를 할당합니다.
        
        Args:
            node_id: 노드 ID
            instance_id: 인스턴스 ID
            
        Returns:
            int: 할당된 포트 번호
            
        Raises:
            ValueError: 사용 가능한 포트가 없는 경우
        """
        data = await self._load_allocations()
        
        # 노드별 다음 포트 번호 초기화
        if "next_port_per_node" not in data:
            data["next_port_per_node"] = {}
        if node_id not in data["next_port_per_node"]:
            data["next_port_per_node"][node_id] = self.PORT_START
        
        # 할당 정보 초기화
        if "allocations" not in data:
            data["allocations"] = {}
        if node_id not in data["allocations"]:
            data["allocations"][node_id] = {}
        
        # 사용 가능한 포트 찾기
        port = data["next_port_per_node"][node_id]
        used_ports = set(data["allocations"][node_id].values())
        
        while port in used_ports and port <= self.PORT_END:
            port += 1
        
        if port > self.PORT_END:
            # 해제된 포트 찾기
            for p in range(self.PORT_START, self.PORT_END + 1):
                if p not in used_ports:
                    port = p
                    break
            else:
                raise ValueError(f"노드 {node_id}에 사용 가능한 포트가 없습니다.")
        
        # 포트 할당
        data["allocations"][node_id][instance_id] = port
        data["next_port_per_node"][node_id] = port + 1
        
        await self._save_allocations(data)
        return port
    
    async def release_port(self, node_id: str, instance_id: str) -> Optional[int]:
        """
        할당된 포트를 해제합니다.
        
        Args:
            node_id: 노드 ID
            instance_id: 인스턴스 ID
            
        Returns:
            Optional[int]: 해제된 포트 번호 (없으면 None)
        """
        data = await self._load_allocations()
        
        if node_id not in data.get("allocations", {}):
            return None
        
        if instance_id not in data["allocations"][node_id]:
            return None
        
        port = data["allocations"][node_id].pop(instance_id)
        await self._save_allocations(data)
        return port
    
    async def get_allocated_port(self, node_id: str, instance_id: str) -> Optional[int]:
        """
        인스턴스에 할당된 포트를 조회합니다.
        
        Args:
            node_id: 노드 ID
            instance_id: 인스턴스 ID
            
        Returns:
            Optional[int]: 할당된 포트 번호 (없으면 None)
        """
        data = await self._load_allocations()
        
        return data.get("allocations", {}).get(node_id, {}).get(instance_id)
    
    async def get_node_port_usage(self, node_id: str) -> dict:
        """
        노드의 포트 사용 현황을 반환합니다.
        
        Args:
            node_id: 노드 ID
            
        Returns:
            dict: 포트 사용 현황
        """
        data = await self._load_allocations()
        
        node_allocations = data.get("allocations", {}).get(node_id, {})
        
        return {
            "node_id": node_id,
            "allocated_count": len(node_allocations),
            "available_count": (self.PORT_END - self.PORT_START + 1) - len(node_allocations),
            "allocations": node_allocations
        }


# 싱글톤 인스턴스
port_allocator = PortAllocator()
