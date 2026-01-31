# ============================================================================
# MCP Cloud Orchestrator - Ray 클러스터 API 라우터
# ============================================================================
# 설명: Ray SDK 기반 실시간 클러스터 모니터링 API
# ============================================================================

from fastapi import APIRouter

from services.ray_service import ray_service


# 라우터 생성
router = APIRouter(
    prefix="/ray",
    tags=["Ray Cluster"],
    responses={500: {"description": "Ray cluster connection error"}}
)


@router.get(
    "/nodes",
    response_model=dict,
    summary="Get Ray Nodes",
    description="Get real-time status of all Ray cluster nodes using ray.nodes() API."
)
async def get_ray_nodes() -> dict:
    """
    Ray SDK로 모든 노드의 실시간 상태를 조회합니다.
    
    - NodeID, IP, Resources, Alive 상태 등
    """
    nodes = ray_service.get_nodes()
    
    return {
        "nodes": nodes,
        "count": len(nodes),
        "alive_count": len([n for n in nodes if n.get("is_alive", False)])
    }


@router.get(
    "/resources",
    response_model=dict,
    summary="Get Cluster Resources",
    description="Get total and available resources of the Ray cluster."
)
async def get_cluster_resources() -> dict:
    """
    클러스터 전체/가용 리소스를 조회합니다.
    
    - CPU, Memory, GPU, Object Store Memory
    """
    total = ray_service.get_cluster_resources()
    available = ray_service.get_available_resources()
    
    used = {
        "cpu": total.get("cpu", 0) - available.get("cpu", 0),
        "memory": total.get("memory", 0) - available.get("memory", 0),
        "gpu": total.get("gpu", 0) - available.get("gpu", 0),
    }
    
    return {
        "total": total,
        "available": available,
        "used": used,
        "usage_percent": {
            "cpu": (used["cpu"] / total["cpu"] * 100) if total.get("cpu", 0) > 0 else 0,
            "memory": (used["memory"] / total["memory"] * 100) if total.get("memory", 0) > 0 else 0,
            "gpu": (used["gpu"] / total["gpu"] * 100) if total.get("gpu", 0) > 0 else 0,
        }
    }


@router.get(
    "/status",
    response_model=dict,
    summary="Get Cluster Status",
    description="Get comprehensive Ray cluster status including nodes and resources."
)
async def get_cluster_status() -> dict:
    """
    Ray 클러스터 전체 상태 요약을 조회합니다.
    
    노드 수, 리소스 현황, 사용률 등 포함
    """
    return ray_service.get_cluster_status()


@router.get(
    "/best-node",
    response_model=dict,
    summary="Find Best Node",
    description="Find the least loaded node for container deployment."
)
async def get_best_node() -> dict:
    """
    컨테이너 배포에 가장 적합한 노드를 찾습니다.
    
    가용 CPU가 가장 많은 노드를 반환
    """
    best_node = ray_service.find_least_loaded_node()
    
    if best_node:
        return {
            "found": True,
            "node": best_node
        }
    else:
        return {
            "found": False,
            "node": None,
            "message": "No available nodes found"
        }
