# ============================================================================
# MCP Cloud Orchestrator - 노드 모델
# ============================================================================
# 설명: Tailscale 노드 정보 및 상태를 나타내는 Pydantic 모델
# ============================================================================

from pydantic import BaseModel, Field, IPvAnyAddress
from typing import Optional
from datetime import datetime
from enum import Enum


class NodeRole(str, Enum):
    """노드 역할 정의"""
    MASTER = "master"      # 마스터 노드
    WORKER = "worker"      # 워커 노드
    STORAGE = "storage"    # 스토리지 노드


class NodeHealth(str, Enum):
    """노드 헬스 상태 정의"""
    HEALTHY = "healthy"          # 정상
    UNHEALTHY = "unhealthy"      # 비정상
    UNKNOWN = "unknown"          # 알 수 없음
    CHECKING = "checking"        # 확인 중


class NodeInfo(BaseModel):
    """
    노드 기본 정보 모델
    
    17개 Tailscale 노드의 기본 정보를 저장합니다.
    """
    
    id: str = Field(..., description="노드 고유 식별자", examples=["node-01"])
    hostname: str = Field(..., description="호스트명", examples=["cpu-worker-01"])
    tailscale_ip: str = Field(..., description="Tailscale VPN IP 주소", examples=["100.64.0.1"])
    
    # 선택적 정보
    role: NodeRole = Field(default=NodeRole.WORKER, description="노드 역할")
    description: Optional[str] = Field(default=None, description="노드 설명")
    cpu_cores: Optional[int] = Field(default=None, description="CPU 코어 수")
    memory_gb: Optional[float] = Field(default=None, description="메모리 용량 (GB)")
    
    # 메타데이터
    created_at: datetime = Field(default_factory=datetime.now, description="등록 시간")
    tags: list[str] = Field(default_factory=list, description="태그 목록")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "node-01",
                "hostname": "cpu-worker-01",
                "tailscale_ip": "100.64.0.1",
                "role": "worker",
                "description": "GPU 없는 CPU 전용 워커 노드",
                "cpu_cores": 8,
                "memory_gb": 32.0,
                "tags": ["production", "high-memory"]
            }
        }


class NodeStatus(BaseModel):
    """
    노드 상태 모델
    
    헬스체크 결과를 포함한 노드의 현재 상태를 나타냅니다.
    """
    
    node_id: str = Field(..., description="노드 고유 식별자")
    health: NodeHealth = Field(default=NodeHealth.UNKNOWN, description="헬스 상태")
    is_online: bool = Field(default=False, description="온라인 여부")
    
    # 헬스체크 결과
    response_time_ms: Optional[float] = Field(default=None, description="응답 시간 (밀리초)")
    last_check_at: Optional[datetime] = Field(default=None, description="마지막 헬스체크 시간")
    error_message: Optional[str] = Field(default=None, description="오류 메시지")
    
    # 리소스 정보 (확장용)
    cpu_usage_percent: Optional[float] = Field(default=None, description="CPU 사용률 (%)")
    memory_usage_percent: Optional[float] = Field(default=None, description="메모리 사용률 (%)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "node_id": "node-01",
                "health": "healthy",
                "is_online": True,
                "response_time_ms": 12.5,
                "last_check_at": "2026-01-30T05:20:00Z",
                "error_message": None
            }
        }


class NodeWithStatus(BaseModel):
    """
    노드 정보와 상태를 결합한 모델
    """
    
    info: NodeInfo = Field(..., description="노드 기본 정보")
    status: NodeStatus = Field(..., description="노드 현재 상태")
