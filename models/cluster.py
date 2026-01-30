# ============================================================================
# MCP Cloud Orchestrator - 클러스터 모델
# ============================================================================
# 설명: 클러스터 전체 상태를 나타내는 Pydantic 모델
# ============================================================================

from pydantic import BaseModel, Field, computed_field
from typing import Optional
from datetime import datetime
from enum import Enum

from .node import NodeWithStatus, NodeHealth


class ClusterHealth(str, Enum):
    """클러스터 전체 헬스 상태"""
    HEALTHY = "healthy"              # 모든 노드 정상
    DEGRADED = "degraded"            # 일부 노드 비정상
    CRITICAL = "critical"            # 다수 노드 비정상
    OFFLINE = "offline"              # 전체 오프라인


class ClusterSummary(BaseModel):
    """
    클러스터 상태 요약 모델
    """
    
    total_nodes: int = Field(..., description="전체 노드 수")
    online_nodes: int = Field(..., description="온라인 노드 수")
    offline_nodes: int = Field(..., description="오프라인 노드 수")
    healthy_nodes: int = Field(..., description="정상 노드 수")
    unhealthy_nodes: int = Field(..., description="비정상 노드 수")
    
    @computed_field
    @property
    def availability_percent(self) -> float:
        """가용성 백분율 계산"""
        if self.total_nodes == 0:
            return 0.0
        return round((self.online_nodes / self.total_nodes) * 100, 2)


class ClusterStatus(BaseModel):
    """
    클러스터 전체 상태 모델
    
    17개 노드의 현재 상태를 종합적으로 나타냅니다.
    """
    
    cluster_name: str = Field(default="mcp-cluster", description="클러스터 이름")
    health: ClusterHealth = Field(..., description="클러스터 헬스 상태")
    summary: ClusterSummary = Field(..., description="상태 요약")
    
    # 타임스탬프
    checked_at: datetime = Field(default_factory=datetime.now, description="상태 확인 시간")
    
    # 노드 상세 정보 (선택적)
    nodes: Optional[list[NodeWithStatus]] = Field(default=None, description="노드 상세 목록")
    
    # 메시지
    message: Optional[str] = Field(default=None, description="상태 메시지")
    
    class Config:
        json_schema_extra = {
            "example": {
                "cluster_name": "mcp-cluster",
                "health": "healthy",
                "summary": {
                    "total_nodes": 17,
                    "online_nodes": 17,
                    "offline_nodes": 0,
                    "healthy_nodes": 17,
                    "unhealthy_nodes": 0
                },
                "checked_at": "2026-01-30T05:20:00Z",
                "message": "모든 노드가 정상 작동 중입니다."
            }
        }

    @classmethod
    def calculate_health(cls, summary: ClusterSummary) -> ClusterHealth:
        """
        요약 정보를 기반으로 클러스터 헬스 상태를 계산합니다.
        
        Args:
            summary: 클러스터 요약 정보
            
        Returns:
            ClusterHealth: 계산된 헬스 상태
        """
        if summary.total_nodes == 0:
            return ClusterHealth.OFFLINE
        
        availability = summary.availability_percent
        
        if availability >= 100:
            return ClusterHealth.HEALTHY
        elif availability >= 80:
            return ClusterHealth.DEGRADED
        elif availability > 0:
            return ClusterHealth.CRITICAL
        else:
            return ClusterHealth.OFFLINE
