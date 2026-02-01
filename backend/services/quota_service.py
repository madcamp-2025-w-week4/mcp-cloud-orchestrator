# ============================================================================
# MCP Cloud Orchestrator - 쿼터 서비스
# ============================================================================
# 설명: 사용자별 리소스 쿼터 관리 및 모니터링 서비스
# ============================================================================

from typing import Optional
from datetime import datetime

from models.user import User, UserQuota
from models.instance import Instance, InstanceStatus
from services.auth_service import auth_service


class QuotaService:
    """
    쿼터 서비스 클래스
    
    사용자별 CPU/RAM 사용량을 추적하고 쿼터를 적용합니다.
    """
    
    async def check_quota(self, user_id: str, requested_cpu: int, requested_memory: int) -> dict:
        """
        사용자가 요청한 리소스가 쿼터 내인지 확인합니다.
        
        NOTE: 제한은 더 이상 적용되지 않습니다 (사용량 기반 청구 방식).
        항상 허용하고, 사용량만 기록합니다.
        
        Args:
            user_id: 사용자 ID
            requested_cpu: 요청 CPU 코어 수
            requested_memory: 요청 메모리 (GB)
            
        Returns:
            dict: 쿼터 확인 결과 (항상 allowed: True)
        """
        user = await auth_service.get_user_by_id(user_id)
        
        if not user:
            # 사용자가 없어도 허용 (데모 모드)
            return {
                "allowed": True,
                "user_id": user_id,
                "note": "Usage-based billing mode"
            }
        
        quota = user.quota
        
        # 제한 없이 항상 허용 (사용량 기반 청구)
        return {
            "allowed": True,
            "current_instances": quota.used_instances,
            "current_cpu": quota.used_cpu,
            "current_memory": quota.used_memory,
            "note": "Usage-based billing - no limits applied"
        }
    
    async def allocate_resources(self, user_id: str, cpu: int, memory: int) -> bool:
        """
        사용자에게 리소스를 할당합니다 (쿼터 사용량 증가).
        
        Args:
            user_id: 사용자 ID
            cpu: CPU 코어 수
            memory: 메모리 (GB)
            
        Returns:
            bool: 성공 여부
        """
        user = await auth_service.get_user_by_id(user_id)
        
        if not user:
            return False
        
        new_quota = UserQuota(
            max_instances=user.quota.max_instances,
            max_cpu=user.quota.max_cpu,
            max_memory=user.quota.max_memory,
            used_instances=user.quota.used_instances + 1,
            used_cpu=user.quota.used_cpu + cpu,
            used_memory=user.quota.used_memory + memory
        )
        
        return await auth_service.update_user_quota(user_id, new_quota)
    
    async def release_resources(self, user_id: str, cpu: int, memory: int) -> bool:
        """
        사용자의 리소스를 해제합니다 (쿼터 사용량 감소).
        
        Args:
            user_id: 사용자 ID
            cpu: CPU 코어 수
            memory: 메모리 (GB)
            
        Returns:
            bool: 성공 여부
        """
        user = await auth_service.get_user_by_id(user_id)
        
        if not user:
            return False
        
        new_quota = UserQuota(
            max_instances=user.quota.max_instances,
            max_cpu=user.quota.max_cpu,
            max_memory=user.quota.max_memory,
            used_instances=max(0, user.quota.used_instances - 1),
            used_cpu=max(0, user.quota.used_cpu - cpu),
            used_memory=max(0, user.quota.used_memory - memory)
        )
        
        return await auth_service.update_user_quota(user_id, new_quota)
    
    async def get_user_quota(self, user_id: str) -> Optional[UserQuota]:
        """
        사용자의 현재 쿼터 정보를 반환합니다.
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            Optional[UserQuota]: 쿼터 정보 (없으면 None)
        """
        user = await auth_service.get_user_by_id(user_id)
        
        if not user:
            return None
        
        return user.quota
    
    async def get_quota_summary(self, user_id: str) -> Optional[dict]:
        """
        사용자의 쿼터 요약 정보를 반환합니다.
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            Optional[dict]: 쿼터 요약
        """
        quota = await self.get_user_quota(user_id)
        
        if not quota:
            return None
        
        return {
            "instances": {
                "used": quota.used_instances,
                "max": quota.max_instances,
                "available": quota.available_instances
            },
            "cpu": {
                "used": quota.used_cpu,
                "max": quota.max_cpu,
                "available": quota.available_cpu,
                "usage_percent": quota.cpu_usage_percent
            },
            "memory": {
                "used": quota.used_memory,
                "max": quota.max_memory,
                "available": quota.available_memory,
                "usage_percent": quota.memory_usage_percent
            }
        }


# 싱글톤 인스턴스
quota_service = QuotaService()
