# ============================================================================
# MCP Cloud Orchestrator - 사용자 모델
# ============================================================================
# 설명: 사용자 정보 및 인증을 위한 Pydantic 모델
# ============================================================================

from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
import uuid


class UserQuota(BaseModel):
    """사용자 리소스 쿼터 모델"""
    
    max_instances: int = Field(default=5, description="최대 인스턴스 수")
    max_cpu: int = Field(default=16, description="최대 CPU 코어 수")
    max_memory: int = Field(default=32, description="최대 메모리 (GB)")
    
    # 현재 사용량
    used_instances: int = Field(default=0, description="사용 중인 인스턴스 수")
    used_cpu: int = Field(default=0, description="사용 중인 CPU 코어 수")
    used_memory: int = Field(default=0, description="사용 중인 메모리 (GB)")
    
    @property
    def available_instances(self) -> int:
        return max(0, self.max_instances - self.used_instances)
    
    @property
    def available_cpu(self) -> int:
        return max(0, self.max_cpu - self.used_cpu)
    
    @property
    def available_memory(self) -> int:
        return max(0, self.max_memory - self.used_memory)
    
    @property
    def cpu_usage_percent(self) -> float:
        if self.max_cpu == 0:
            return 0.0
        return round((self.used_cpu / self.max_cpu) * 100, 1)
    
    @property
    def memory_usage_percent(self) -> float:
        if self.max_memory == 0:
            return 0.0
        return round((self.used_memory / self.max_memory) * 100, 1)


class User(BaseModel):
    """사용자 정보 모델"""
    
    id: str = Field(default_factory=lambda: f"user-{str(uuid.uuid4())[:8]}", description="사용자 고유 ID")
    username: str = Field(..., description="사용자 이름", min_length=3, max_length=32)
    email: Optional[str] = Field(default=None, description="이메일 주소")
    
    # 쿼터 정보
    quota: UserQuota = Field(default_factory=UserQuota, description="리소스 쿼터")
    
    # 상태
    is_active: bool = Field(default=True, description="계정 활성화 여부")
    
    # 타임스탬프
    created_at: datetime = Field(default_factory=datetime.now, description="생성 시간")
    last_login_at: Optional[datetime] = Field(default=None, description="마지막 로그인 시간")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "user-abc1234",
                "username": "developer",
                "email": "dev@example.com",
                "quota": {
                    "max_instances": 5,
                    "max_cpu": 16,
                    "max_memory": 32,
                    "used_instances": 2,
                    "used_cpu": 4,
                    "used_memory": 8
                },
                "is_active": True
            }
        }


class UserLogin(BaseModel):
    """로그인 요청 모델"""
    
    username: str = Field(..., description="사용자 이름")
    password: str = Field(..., description="비밀번호")


class UserSession(BaseModel):
    """사용자 세션 모델"""
    
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="세션 ID")
    user_id: str = Field(..., description="사용자 ID")
    username: str = Field(..., description="사용자 이름")
    created_at: datetime = Field(default_factory=datetime.now, description="세션 생성 시간")
    expires_at: Optional[datetime] = Field(default=None, description="세션 만료 시간")


class UserPublic(BaseModel):
    """공개 사용자 정보 (민감 정보 제외)"""
    
    id: str
    username: str
    quota: UserQuota
    is_active: bool
