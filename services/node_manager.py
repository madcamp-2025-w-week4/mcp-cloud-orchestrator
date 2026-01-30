# ============================================================================
# MCP Cloud Orchestrator - 노드 관리 서비스
# ============================================================================
# 설명: 17개 Tailscale 노드의 정보를 관리하는 서비스
#       JSON 파일 기반 저장소 사용
# ============================================================================

import json
import aiofiles
from pathlib import Path
from typing import Optional
from datetime import datetime

from models.node import NodeInfo, NodeRole
from core.config import settings
from core.exceptions import NodeNotFoundException, DataFileException


class NodeManager:
    """
    노드 관리 서비스 클래스
    
    17개 분산 CPU 노드의 정보를 JSON 파일에서 로드/저장하고
    CRUD 작업을 지원합니다.
    """
    
    def __init__(self, nodes_file_path: str = None):
        """
        NodeManager 초기화
        
        Args:
            nodes_file_path: 노드 정보 JSON 파일 경로 (기본값: 설정에서 로드)
        """
        self.nodes_file_path = Path(nodes_file_path or settings.nodes_file_path)
        self._nodes_cache: dict[str, NodeInfo] = {}
        self._last_loaded: Optional[datetime] = None
    
    async def _ensure_file_exists(self) -> None:
        """노드 파일이 존재하는지 확인하고, 없으면 생성합니다."""
        if not self.nodes_file_path.exists():
            # 디렉토리 생성
            self.nodes_file_path.parent.mkdir(parents=True, exist_ok=True)
            # 빈 노드 목록으로 초기화
            await self._save_nodes({})
    
    async def _load_nodes(self) -> dict[str, NodeInfo]:
        """
        JSON 파일에서 노드 정보를 로드합니다.
        
        Returns:
            dict[str, NodeInfo]: 노드 ID를 키로 하는 노드 정보 딕셔너리
        """
        await self._ensure_file_exists()
        
        try:
            async with aiofiles.open(self.nodes_file_path, mode='r', encoding='utf-8') as f:
                content = await f.read()
                data = json.loads(content)
                
                nodes = {}
                for node_id, node_data in data.get("nodes", {}).items():
                    nodes[node_id] = NodeInfo(**node_data)
                
                self._nodes_cache = nodes
                self._last_loaded = datetime.now()
                return nodes
                
        except json.JSONDecodeError as e:
            raise DataFileException(
                file_path=str(self.nodes_file_path),
                operation="읽기",
                reason=f"JSON 파싱 오류: {str(e)}"
            )
        except Exception as e:
            raise DataFileException(
                file_path=str(self.nodes_file_path),
                operation="읽기",
                reason=str(e)
            )
    
    async def _save_nodes(self, nodes: dict[str, NodeInfo]) -> None:
        """
        노드 정보를 JSON 파일에 저장합니다.
        
        Args:
            nodes: 저장할 노드 정보 딕셔너리
        """
        try:
            data = {
                "metadata": {
                    "version": "1.0",
                    "updated_at": datetime.now().isoformat(),
                    "total_nodes": len(nodes)
                },
                "nodes": {
                    node_id: node.model_dump(mode='json')
                    for node_id, node in nodes.items()
                }
            }
            
            async with aiofiles.open(self.nodes_file_path, mode='w', encoding='utf-8') as f:
                await f.write(json.dumps(data, indent=2, ensure_ascii=False))
            
            self._nodes_cache = nodes
            
        except Exception as e:
            raise DataFileException(
                file_path=str(self.nodes_file_path),
                operation="쓰기",
                reason=str(e)
            )
    
    async def get_all_nodes(self) -> list[NodeInfo]:
        """
        모든 노드 정보를 반환합니다.
        
        Returns:
            list[NodeInfo]: 전체 노드 목록
        """
        nodes = await self._load_nodes()
        return list(nodes.values())
    
    async def get_node(self, node_id: str) -> NodeInfo:
        """
        특정 노드의 정보를 반환합니다.
        
        Args:
            node_id: 노드 고유 식별자
            
        Returns:
            NodeInfo: 노드 정보
            
        Raises:
            NodeNotFoundException: 노드를 찾을 수 없는 경우
        """
        nodes = await self._load_nodes()
        
        if node_id not in nodes:
            raise NodeNotFoundException(node_id)
        
        return nodes[node_id]
    
    async def add_node(self, node: NodeInfo) -> NodeInfo:
        """
        새 노드를 추가합니다.
        
        Args:
            node: 추가할 노드 정보
            
        Returns:
            NodeInfo: 추가된 노드 정보
        """
        nodes = await self._load_nodes()
        nodes[node.id] = node
        await self._save_nodes(nodes)
        return node
    
    async def update_node(self, node_id: str, node: NodeInfo) -> NodeInfo:
        """
        기존 노드 정보를 업데이트합니다.
        
        Args:
            node_id: 업데이트할 노드 ID
            node: 새 노드 정보
            
        Returns:
            NodeInfo: 업데이트된 노드 정보
            
        Raises:
            NodeNotFoundException: 노드를 찾을 수 없는 경우
        """
        nodes = await self._load_nodes()
        
        if node_id not in nodes:
            raise NodeNotFoundException(node_id)
        
        nodes[node_id] = node
        await self._save_nodes(nodes)
        return node
    
    async def delete_node(self, node_id: str) -> bool:
        """
        노드를 삭제합니다.
        
        Args:
            node_id: 삭제할 노드 ID
            
        Returns:
            bool: 삭제 성공 여부
            
        Raises:
            NodeNotFoundException: 노드를 찾을 수 없는 경우
        """
        nodes = await self._load_nodes()
        
        if node_id not in nodes:
            raise NodeNotFoundException(node_id)
        
        del nodes[node_id]
        await self._save_nodes(nodes)
        return True
    
    async def get_nodes_by_role(self, role: NodeRole) -> list[NodeInfo]:
        """
        특정 역할의 노드들을 반환합니다.
        
        Args:
            role: 노드 역할
            
        Returns:
            list[NodeInfo]: 해당 역할의 노드 목록
        """
        nodes = await self._load_nodes()
        return [node for node in nodes.values() if node.role == role]
    
    async def get_node_count(self) -> int:
        """
        전체 노드 수를 반환합니다.
        
        Returns:
            int: 노드 수
        """
        nodes = await self._load_nodes()
        return len(nodes)


# 싱글톤 인스턴스
node_manager = NodeManager()
