# ============================================================================
# MCP Cloud Orchestrator - 핵심 설정 모듈
# ============================================================================
# 설명: Pydantic Settings를 활용한 환경 설정 관리
# ============================================================================

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """
    애플리케이션 환경 설정 클래스
    
    환경변수 또는 .env 파일에서 설정값을 로드합니다.
    """
    
    # 앱 기본 설정
    app_name: str = Field(default="MCP Cloud Orchestrator", description="애플리케이션 이름")
    app_version: str = Field(default="0.1.0", description="애플리케이션 버전")
    debug: bool = Field(default=False, description="디버그 모드 활성화 여부")
    
    # 서버 설정
    host: str = Field(default="0.0.0.0", description="서버 바인딩 호스트")
    port: int = Field(default=8000, description="서버 포트")
    
    # 노드 관리 설정
    nodes_file_path: str = Field(default="data/nodes.json", description="노드 정보 JSON 파일 경로")
    
    # 헬스체크 설정
    health_check_timeout: float = Field(default=5.0, description="헬스체크 타임아웃 (초)")
    health_check_interval: int = Field(default=30, description="헬스체크 주기 (초)")
    
    # Tailscale 설정
    tailscale_network: str = Field(default="100.64.0.0/10", description="Tailscale 네트워크 CIDR")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    설정 인스턴스를 반환합니다 (캐싱 적용).
    
    Returns:
        Settings: 애플리케이션 설정 인스턴스
    """
    return Settings()


# 전역 설정 인스턴스
settings = get_settings()
