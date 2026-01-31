# ============================================================================
# MCP Cloud Orchestrator - 인스턴스 모델
# ============================================================================
# 설명: 사용자 컨테이너 인스턴스 정보를 나타내는 Pydantic 모델
# ============================================================================

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum
import uuid


class InstanceStatus(str, Enum):
    """인스턴스 상태 정의"""
    PENDING = "pending"          # 생성 대기 중
    RUNNING = "running"          # 실행 중
    STOPPED = "stopped"          # 중지됨
    TERMINATED = "terminated"    # 종료됨
    ERROR = "error"              # 오류 상태


class ContainerImage(str, Enum):
    """사용 가능한 컨테이너 이미지"""
    UBUNTU_22 = "ubuntu:22.04"
    UBUNTU_20 = "ubuntu:20.04"
    PYTHON_311 = "python:3.11"
    PYTHON_310 = "python:3.10"
    NODE_20 = "node:20"
    NODE_18 = "node:18"
    NGINX = "nginx:latest"
    REDIS = "redis:latest"


class InstanceCreate(BaseModel):
    """인스턴스 생성 요청 모델"""
    
    name: str = Field(..., description="인스턴스 이름", min_length=1, max_length=64)
    image: str = Field(default="ubuntu:22.04", description="컨테이너 이미지")
    cpu: int = Field(default=1, ge=1, le=8, description="CPU 코어 수")
    memory: int = Field(default=2, ge=1, le=32, description="메모리 (GB)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "my-web-server",
                "image": "ubuntu:22.04",
                "cpu": 2,
                "memory": 4
            }
        }


class Instance(BaseModel):
    """인스턴스 정보 모델"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8], description="인스턴스 고유 ID")
    name: str = Field(..., description="인스턴스 이름")
    image: str = Field(..., description="컨테이너 이미지")
    
    # 소유권 및 할당 정보
    user_id: str = Field(..., description="소유자 사용자 ID")
    node_id: str = Field(..., description="할당된 노드 ID")
    port: int = Field(..., description="할당된 포트 번호")
    
    # 리소스 사양
    cpu: int = Field(default=1, description="CPU 코어 수")
    memory: int = Field(default=2, description="메모리 (GB)")
    
    # 상태 정보
    status: InstanceStatus = Field(default=InstanceStatus.PENDING, description="인스턴스 상태")
    public_ip: Optional[str] = Field(default=None, description="공개 IP 주소")
    container_id: Optional[str] = Field(default=None, description="Docker 컨테이너 ID")
    
    # 타임스탬프
    created_at: datetime = Field(default_factory=datetime.now, description="생성 시간")
    started_at: Optional[datetime] = Field(default=None, description="시작 시간")
    stopped_at: Optional[datetime] = Field(default=None, description="중지 시간")
    
    # 메타데이터
    tags: list[str] = Field(default_factory=list, description="태그 목록")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "i-abc1234",
                "name": "my-web-server",
                "image": "ubuntu:22.04",
                "user_id": "user-001",
                "node_id": "camp-61",
                "port": 8001,
                "cpu": 2,
                "memory": 4,
                "status": "running",
                "public_ip": "100.112.111.30",
                "created_at": "2026-01-30T10:00:00Z",
                "started_at": "2026-01-30T10:00:05Z"
            }
        }
    
    @property
    def uptime_seconds(self) -> Optional[int]:
        """인스턴스 가동 시간 (초)"""
        if self.started_at and self.status == InstanceStatus.RUNNING:
            return int((datetime.now() - self.started_at).total_seconds())
        return None
    
    @property
    def access_url(self) -> Optional[str]:
        """인스턴스 접속 URL"""
        if self.public_ip and self.port:
            return f"{self.public_ip}:{self.port}"
        return None


class InstanceSummary(BaseModel):
    """인스턴스 요약 정보 (목록 표시용)"""
    
    id: str
    name: str
    image: str
    status: InstanceStatus
    access_url: Optional[str]
    cpu: int
    memory: int
    uptime_seconds: Optional[int]
    created_at: datetime
