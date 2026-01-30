# ============================================================================
# MCP Cloud Orchestrator - 의존성 주입 모듈
# ============================================================================
# 설명: FastAPI 의존성 주입을 위한 공통 의존성 정의
# ============================================================================

from typing import Generator
from core.config import Settings, get_settings
from services.node_manager import NodeManager, node_manager
from services.health_monitor import HealthMonitor, health_monitor


def get_settings_dependency() -> Settings:
    """설정 인스턴스를 반환하는 의존성"""
    return get_settings()


def get_node_manager() -> NodeManager:
    """노드 매니저 인스턴스를 반환하는 의존성"""
    return node_manager


def get_health_monitor() -> HealthMonitor:
    """헬스 모니터 인스턴스를 반환하는 의존성"""
    return health_monitor
