# ============================================================================
# KWS - Billing Service
# ============================================================================
# 설명: AWS/Railway 스타일 사용량 기반 가상 청구 서비스
# ============================================================================

import json
import aiofiles
from pathlib import Path
from datetime import datetime
from typing import Optional

# 요금 체계 (시간당)
PRICING = {
    "cpu_per_hour": 0.02,       # $0.02 per vCPU per hour
    "memory_per_hour": 0.01,    # $0.01 per GB per hour
    "instance_per_hour": 0.005  # $0.005 per instance per hour
}

DATA_PATH = Path(__file__).parent.parent / "data" / "billing.json"


class BillingService:
    """
    사용량 기반 청구 서비스
    
    인스턴스 가동 시간에 따라 가상 금액을 계산합니다.
    매월 1일에 자동으로 리셋됩니다.
    """
    
    def __init__(self):
        self._billing_data: dict = {}
        self._loaded = False
    
    async def _load_data(self):
        """청구 데이터를 로드합니다."""
        if self._loaded:
            return
        
        try:
            if DATA_PATH.exists():
                async with aiofiles.open(DATA_PATH, 'r') as f:
                    content = await f.read()
                    self._billing_data = json.loads(content)
            else:
                self._billing_data = {}
            self._loaded = True
        except Exception as e:
            print(f"Failed to load billing data: {e}")
            self._billing_data = {}
            self._loaded = True
    
    async def _save_data(self):
        """청구 데이터를 저장합니다."""
        try:
            async with aiofiles.open(DATA_PATH, 'w') as f:
                await f.write(json.dumps(self._billing_data, indent=2))
        except Exception as e:
            print(f"Failed to save billing data: {e}")
    
    def _get_current_month(self) -> str:
        """현재 월을 YYYY-MM 형식으로 반환합니다."""
        return datetime.now().strftime("%Y-%m")
    
    async def _ensure_user_billing(self, user_id: str) -> dict:
        """사용자의 청구 데이터를 초기화하거나 월 변경 시 리셋합니다."""
        await self._load_data()
        
        current_month = self._get_current_month()
        
        if user_id not in self._billing_data:
            self._billing_data[user_id] = {
                "billing_month": current_month,
                "usage": {
                    "cpu_hours": 0,
                    "memory_gb_hours": 0,
                    "instance_hours": 0
                },
                "total_amount": 0.00,
                "last_updated": datetime.now().isoformat()
            }
            await self._save_data()
        
        # 월이 바뀌면 리셋
        if self._billing_data[user_id].get("billing_month") != current_month:
            self._billing_data[user_id] = {
                "billing_month": current_month,
                "usage": {
                    "cpu_hours": 0,
                    "memory_gb_hours": 0,
                    "instance_hours": 0
                },
                "total_amount": 0.00,
                "last_updated": datetime.now().isoformat()
            }
            await self._save_data()
        
        return self._billing_data[user_id]
    
    async def add_usage(self, user_id: str, cpu: int, memory_gb: int, hours: float = 1.0):
        """
        사용량을 추가합니다.
        
        Args:
            user_id: 사용자 ID
            cpu: vCPU 수
            memory_gb: 메모리 GB
            hours: 사용 시간 (기본 1시간)
        """
        billing = await self._ensure_user_billing(user_id)
        
        billing["usage"]["cpu_hours"] += cpu * hours
        billing["usage"]["memory_gb_hours"] += memory_gb * hours
        billing["usage"]["instance_hours"] += hours
        
        # 금액 재계산
        billing["total_amount"] = (
            billing["usage"]["cpu_hours"] * PRICING["cpu_per_hour"] +
            billing["usage"]["memory_gb_hours"] * PRICING["memory_per_hour"] +
            billing["usage"]["instance_hours"] * PRICING["instance_per_hour"]
        )
        billing["last_updated"] = datetime.now().isoformat()
        
        await self._save_data()
    
    async def get_billing_summary(self, user_id: str) -> dict:
        """
        사용자의 청구 요약을 반환합니다.
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            dict: 청구 요약
        """
        billing = await self._ensure_user_billing(user_id)
        
        # 월말까지 남은 일수 계산
        now = datetime.now()
        if now.month == 12:
            next_month = datetime(now.year + 1, 1, 1)
        else:
            next_month = datetime(now.year, now.month + 1, 1)
        days_remaining = (next_month - now).days
        
        return {
            "billing_month": billing["billing_month"],
            "usage": {
                "cpu_hours": round(billing["usage"]["cpu_hours"], 2),
                "memory_gb_hours": round(billing["usage"]["memory_gb_hours"], 2),
                "instance_hours": round(billing["usage"]["instance_hours"], 2)
            },
            "breakdown": {
                "cpu_cost": round(billing["usage"]["cpu_hours"] * PRICING["cpu_per_hour"], 2),
                "memory_cost": round(billing["usage"]["memory_gb_hours"] * PRICING["memory_per_hour"], 2),
                "instance_cost": round(billing["usage"]["instance_hours"] * PRICING["instance_per_hour"], 2)
            },
            "total_amount": round(billing["total_amount"], 2),
            "currency": "USD",
            "days_remaining": days_remaining,
            "pricing": PRICING
        }
    
    async def record_instance_start(self, user_id: str, cpu: int, memory_gb: int):
        """인스턴스 시작 시 초기 1시간 사용량을 기록합니다."""
        await self.add_usage(user_id, cpu, memory_gb, hours=1.0)
    
    async def record_hourly_usage(self, user_id: str, cpu: int, memory_gb: int):
        """시간당 사용량을 기록합니다 (스케줄러에서 호출)."""
        await self.add_usage(user_id, cpu, memory_gb, hours=1.0)


# 싱글톤 인스턴스
billing_service = BillingService()
