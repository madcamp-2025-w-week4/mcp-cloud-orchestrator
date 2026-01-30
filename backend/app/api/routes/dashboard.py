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
