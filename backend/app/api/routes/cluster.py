# ============================================================================
# MCP Cloud Orchestrator - 클러스터 API 라우터
# ============================================================================
# 설명: 클러스터 상태 및 노드 관리 API 엔드포인트
# ============================================================================

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from models.node import NodeInfo, NodeStatus, NodeWithStatus, NodeRole
from models.cluster import ClusterStatus
from services.node_manager import node_manager
from services.health_monitor import health_monitor
from core.exceptions import NodeNotFoundException


# 라우터 생성
router = APIRouter(
    prefix="/cluster",
    tags=["클러스터"],
    responses={404: {"description": "리소스를 찾을 수 없음"}}
)


@router.get(
    "/status",
    response_model=ClusterStatus,
    summary="클러스터 상태 조회",
    description="17개 분산 노드의 현재 상태를 종합적으로 조회합니다."
)
async def get_cluster_status(
    include_nodes: bool = Query(
        default=False,
        description="개별 노드 상세 정보 포함 여부"
    )
) -> ClusterStatus:
    """
    클러스터 전체 상태를 반환합니다.
    
    - **include_nodes**: True로 설정하면 각 노드의 상세 정보도 포함됩니다.
    
    이 API는 asyncio.gather를 사용하여 17개 노드를 동시에 체크하므로
    빠른 응답 시간을 보장합니다.
    """
    return await health_monitor.get_cluster_status(include_nodes=include_nodes)


@router.get(
    "/nodes",
    response_model=list[NodeInfo],
    summary="전체 노드 목록 조회",
    description="클러스터에 등록된 모든 노드의 기본 정보를 조회합니다."
)
async def get_all_nodes(
    role: Optional[NodeRole] = Query(
        default=None,
        description="특정 역할의 노드만 필터링"
    )
) -> list[NodeInfo]:
    """
    모든 노드의 기본 정보를 반환합니다.
    
    - **role**: 특정 역할 (master, worker, storage)로 필터링할 수 있습니다.
    """
    if role:
        return await node_manager.get_nodes_by_role(role)
    return await node_manager.get_all_nodes()


@router.get(
    "/nodes/{node_id}",
    response_model=NodeInfo,
    summary="특정 노드 정보 조회",
    description="노드 ID로 특정 노드의 상세 정보를 조회합니다."
)
async def get_node(node_id: str) -> NodeInfo:
    """
    특정 노드의 기본 정보를 반환합니다.
    
    - **node_id**: 조회할 노드의 고유 식별자
    """
    try:
        return await node_manager.get_node(node_id)
    except NodeNotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.get(
    "/nodes/{node_id}/health",
    response_model=NodeStatus,
    summary="특정 노드 헬스체크",
    description="특정 노드에 대한 실시간 헬스체크를 수행합니다."
)
async def check_node_health(node_id: str) -> NodeStatus:
    """
    특정 노드의 헬스 상태를 실시간으로 체크합니다.
    
    - **node_id**: 체크할 노드의 고유 식별자
    
    TCP 연결을 통해 노드의 응답 여부와 응답 시간을 측정합니다.
    """
    try:
        node = await node_manager.get_node(node_id)
        return await health_monitor.check_node_health(node)
    except NodeNotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.post(
    "/nodes",
    response_model=NodeInfo,
    status_code=201,
    summary="새 노드 등록",
    description="클러스터에 새 노드를 등록합니다."
)
async def create_node(node: NodeInfo) -> NodeInfo:
    """
    새 노드를 클러스터에 등록합니다.
    
    등록된 노드는 헬스 모니터링 대상에 자동으로 포함됩니다.
    """
    return await node_manager.add_node(node)


@router.put(
    "/nodes/{node_id}",
    response_model=NodeInfo,
    summary="노드 정보 수정",
    description="기존 노드의 정보를 수정합니다."
)
async def update_node(node_id: str, node: NodeInfo) -> NodeInfo:
    """
    기존 노드의 정보를 수정합니다.
    
    - **node_id**: 수정할 노드의 고유 식별자
    """
    try:
        return await node_manager.update_node(node_id, node)
    except NodeNotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.delete(
    "/nodes/{node_id}",
    status_code=204,
    summary="노드 삭제",
    description="클러스터에서 노드를 제거합니다."
)
async def delete_node(node_id: str) -> None:
    """
    클러스터에서 노드를 삭제합니다.
    
    - **node_id**: 삭제할 노드의 고유 식별자
    
    주의: 삭제된 노드는 헬스 모니터링 대상에서 제외됩니다.
    """
    try:
        await node_manager.delete_node(node_id)
    except NodeNotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.post(
    "/health-check",
    response_model=list[NodeWithStatus],
    summary="전체 노드 헬스체크",
    description="모든 노드에 대한 실시간 헬스체크를 수행합니다."
)
async def check_all_nodes_health() -> list[NodeWithStatus]:
    """
    클러스터의 모든 노드에 대해 동시에 헬스체크를 수행합니다.
    
    asyncio.gather를 사용하여 17개 노드를 병렬로 체크하므로
    전체 응답 시간이 크게 단축됩니다.
    """
    return await health_monitor.check_all_nodes()
