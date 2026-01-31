# ============================================================================
# MCP Cloud Orchestrator - 대시보드 API 라우터
# ============================================================================
# 설명: 프론트엔드 대시보드용 통합 데이터 API
# ============================================================================

from fastapi import APIRouter, Header
from typing import Optional
from datetime import datetime

from services.instance_manager import instance_manager
from services.quota_service import quota_service
from services.health_monitor import health_monitor
from services.node_manager import node_manager
from models.node import NodeRole


# 라우터 생성
router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
    responses={404: {"description": "Resource not found"}}
)


@router.get(
    "/summary",
    response_model=dict,
    summary="Dashboard Summary",
    description="Get aggregated data for the dashboard view."
)
async def get_dashboard_summary(
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
) -> dict:
    """
    대시보드에 표시할 요약 데이터를 반환합니다.
    
    - Total Instances
    - Active Nodes
    - Resource Quota
    """
    if not x_user_id:
        x_user_id = "user-demo-001"
    
    # 인스턴스 요약
    instance_summary = await instance_manager.get_instance_summary(x_user_id)
    
    # 쿼터 정보
    quota_summary = await quota_service.get_quota_summary(x_user_id)
    
    # 노드 정보
    all_nodes = await node_manager.get_all_nodes()
    worker_nodes = await node_manager.get_nodes_by_role(NodeRole.WORKER)
    
    return {
        "instances": instance_summary,
        "quota": quota_summary,
        "nodes": {
            "total": len(all_nodes),
            "workers": len(worker_nodes),
            "master": 1
        },
        "timestamp": datetime.now().isoformat()
    }


@router.get(
    "/health",
    response_model=dict,
    summary="Cluster Health",
    description="Get the current health status of the cluster."
)
async def get_cluster_health() -> dict:
    """
    클러스터 헬스 상태를 반환합니다.
    """
    cluster_status = await health_monitor.get_cluster_status(include_nodes=False)
    
    return {
        "cluster_name": cluster_status.cluster_name,
        "health": cluster_status.health.value,
        "summary": {
            "total_nodes": cluster_status.summary.total_nodes,
            "online_nodes": cluster_status.summary.online_nodes,
            "offline_nodes": cluster_status.summary.offline_nodes,
            "availability_percent": cluster_status.summary.availability_percent
        },
        "message": cluster_status.message,
        "checked_at": cluster_status.checked_at.isoformat()
    }


@router.get(
    "/nodes/status",
    response_model=list[dict],
    summary="Node Status List",
    description="Get the status of all nodes for display."
)
async def get_nodes_status() -> list[dict]:
    """
    모든 노드의 상태를 반환합니다.
    """
    nodes_with_status = await health_monitor.check_all_nodes()
    
    result = []
    for node_with_status in nodes_with_status:
        node = node_with_status.info
        status = node_with_status.status
        
        result.append({
            "id": node.id,
            "hostname": node.hostname,
            "ip": node.tailscale_ip,
            "role": node.role.value,
            "health": status.health.value,
            "is_online": status.is_online,
            "response_time_ms": status.response_time_ms,
            "cpu_cores": node.cpu_cores,
            "memory_gb": node.memory_gb
        })
    
    return result


@router.get(
    "/images",
    response_model=list[dict],
    summary="Available Images",
    description="Get the list of available container images."
)
async def get_available_images() -> list[dict]:
    """
    사용 가능한 컨테이너 이미지 목록을 반환합니다.
    """
    return [
        {
            "id": "ubuntu:22.04",
            "name": "Ubuntu 22.04 LTS",
            "description": "Ubuntu 22.04 LTS (Jammy Jellyfish)",
            "category": "Operating System"
        },
        {
            "id": "ubuntu:20.04",
            "name": "Ubuntu 20.04 LTS",
            "description": "Ubuntu 20.04 LTS (Focal Fossa)",
            "category": "Operating System"
        },
        {
            "id": "python:3.11",
            "name": "Python 3.11",
            "description": "Python 3.11 runtime environment",
            "category": "Runtime"
        },
        {
            "id": "python:3.10",
            "name": "Python 3.10",
            "description": "Python 3.10 runtime environment",
            "category": "Runtime"
        },
        {
            "id": "node:20",
            "name": "Node.js 20",
            "description": "Node.js 20 LTS runtime",
            "category": "Runtime"
        },
        {
            "id": "node:18",
            "name": "Node.js 18",
            "description": "Node.js 18 LTS runtime",
            "category": "Runtime"
        },
        {
            "id": "nginx:latest",
            "name": "Nginx",
            "description": "High-performance web server",
            "category": "Web Server"
        },
        {
            "id": "redis:latest",
            "name": "Redis",
            "description": "In-memory data store",
            "category": "Database"
        }
    ]


@router.get(
    "/capacity",
    response_model=dict,
    summary="Cluster Capacity",
    description="Get the maximum available CPU and memory from the cluster."
)
async def get_cluster_capacity() -> dict:
    """
    등록된 Worker 노드 중 단일 노드가 제공할 수 있는 최대 리소스를 반환합니다.
    
    UI에서 리소스 선택 옵션을 동적으로 제한하는 데 사용됩니다.
    """
    from services.ray_service import ray_service
    from services.node_manager import node_manager
    from models.node import NodeRole
    
    # 등록된 Worker 노드 조회
    workers = await node_manager.get_nodes_by_role(NodeRole.WORKER)
    worker_ips = {w.tailscale_ip for w in workers}
    
    # Ray에서 노드별 리소스 조회
    ray_nodes = ray_service.get_nodes_with_available_resources()
    
    # Worker 노드들의 최대 용량 계산
    max_cpu = 0
    max_memory = 0
    for ray_node in ray_nodes:
        if ray_node.get("node_ip") in worker_ips:
            max_cpu = max(max_cpu, int(ray_node.get("cpu_available", 0)))
            max_memory = max(max_memory, int(ray_node.get("memory_available_gb", 0)))
    
    # 기본값 (Worker가 없거나 Ray 연결 안됨)
    if max_cpu == 0:
        max_cpu = 4
    if max_memory == 0:
        max_memory = 8
    
    # CPU 옵션 생성 (1, 2, 4, ... max)
    cpu_options = [c for c in [1, 2, 4, 8, 16, 32] if c <= max_cpu]
    if max_cpu not in cpu_options and max_cpu > 0:
        cpu_options.append(max_cpu)
        cpu_options.sort()
    
    # 메모리 옵션 생성 (2, 4, 8, ... max)
    memory_options = [m for m in [2, 4, 8, 16, 32, 64] if m <= max_memory]
    if max_memory not in memory_options and max_memory > 0:
        memory_options.append(max_memory)
        memory_options.sort()
    
    return {
        "max_cpu": max_cpu,
        "max_memory_gb": max_memory,
        "cpu_options": cpu_options,
        "memory_options": memory_options,
        "timestamp": datetime.now().isoformat()
    }

