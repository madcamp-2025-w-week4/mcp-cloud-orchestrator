# ============================================================================
# MCP Cloud Orchestrator - 인증 서비스
# ============================================================================
# 설명: 간단한 세션 기반 인증 서비스
#       프로덕션에서는 JWT 또는 OAuth 사용 권장
# ============================================================================

import json
import aiofiles
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
import uuid

from models.user import User, UserQuota, UserSession, UserLogin
from core.config import settings


class AuthService:
    """
    인증 서비스 클래스
    
    간단한 세션 기반 인증을 제공합니다.
    데모용으로, 프로덕션에서는 JWT/OAuth 사용을 권장합니다.
    """
    
    def __init__(self, users_file_path: str = None):
        """
        AuthService 초기화
        
        Args:
            users_file_path: 사용자 정보 JSON 파일 경로
        """
        self.users_file_path = Path(
            users_file_path or 
            str(Path(settings.nodes_file_path).parent / "users.json")
        )
        self._users_cache: dict = {}
        self._sessions: dict[str, UserSession] = {}
    
    async def _ensure_file_exists(self) -> None:
        """사용자 파일이 존재하는지 확인하고, 없으면 생성합니다."""
        if not self.users_file_path.exists():
            self.users_file_path.parent.mkdir(parents=True, exist_ok=True)
            initial_data = {
                "metadata": {
                    "version": "1.0",
                    "updated_at": datetime.now().isoformat(),
                    "description": "사용자 데이터 저장소"
                },
                "users": {
                    "user-demo-001": {
                        "id": "user-demo-001",
                        "username": "demo",
                        "email": "demo@example.com",
                        "password_hash": "demo",
                        "quota": {
                            "max_instances": 5,
                            "max_cpu": 16,
                            "max_memory": 32,
                            "used_instances": 0,
                            "used_cpu": 0,
                            "used_memory": 0
                        },
                        "is_active": True,
                        "created_at": datetime.now().isoformat()
                    }
                }
            }
            async with aiofiles.open(self.users_file_path, mode='w', encoding='utf-8') as f:
                await f.write(json.dumps(initial_data, indent=2, ensure_ascii=False))
    
    async def _load_users(self) -> dict:
        """사용자 정보를 로드합니다."""
        await self._ensure_file_exists()
        
        async with aiofiles.open(self.users_file_path, mode='r', encoding='utf-8') as f:
            content = await f.read()
            data = json.loads(content)
            self._users_cache = data
            return data
    
    async def _save_users(self, data: dict) -> None:
        """사용자 정보를 저장합니다."""
        data["metadata"]["updated_at"] = datetime.now().isoformat()
        
        async with aiofiles.open(self.users_file_path, mode='w', encoding='utf-8') as f:
            await f.write(json.dumps(data, indent=2, ensure_ascii=False))
        
        self._users_cache = data
    
    async def authenticate(self, username: str, password: str) -> Optional[UserSession]:
        """
        사용자를 인증하고 세션을 생성합니다.
        
        Args:
            username: 사용자 이름
            password: 비밀번호
            
        Returns:
            Optional[UserSession]: 인증 성공 시 세션, 실패 시 None
        """
        data = await self._load_users()
        
        for user_id, user_data in data.get("users", {}).items():
            if user_data.get("username") == username:
                # 간단한 비밀번호 비교 (프로덕션에서는 해시 비교 필요)
                if user_data.get("password_hash") == password:
                    if not user_data.get("is_active", True):
                        return None
                    
                    # 세션 생성
                    session = UserSession(
                        session_id=str(uuid.uuid4()),
                        user_id=user_id,
                        username=username,
                        created_at=datetime.now(),
                        expires_at=datetime.now() + timedelta(hours=24)
                    )
                    
                    self._sessions[session.session_id] = session
                    
                    # 마지막 로그인 시간 업데이트
                    user_data["last_login_at"] = datetime.now().isoformat()
                    await self._save_users(data)
                    
                    return session
        
        return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        사용자 ID로 사용자 정보를 조회합니다.
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            Optional[User]: 사용자 정보 (없으면 None)
        """
        data = await self._load_users()
        
        user_data = data.get("users", {}).get(user_id)
        if not user_data:
            return None
        
        return User(
            id=user_data.get("id"),
            username=user_data.get("username"),
            email=user_data.get("email"),
            quota=UserQuota(**user_data.get("quota", {})),
            is_active=user_data.get("is_active", True),
            created_at=datetime.fromisoformat(user_data.get("created_at", datetime.now().isoformat())),
            last_login_at=datetime.fromisoformat(user_data["last_login_at"]) if user_data.get("last_login_at") else None
        )
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """
        사용자 이름으로 사용자 정보를 조회합니다.
        
        Args:
            username: 사용자 이름
            
        Returns:
            Optional[User]: 사용자 정보 (없으면 None)
        """
        data = await self._load_users()
        
        for user_id, user_data in data.get("users", {}).items():
            if user_data.get("username") == username:
                return await self.get_user_by_id(user_id)
        
        return None
    
    async def validate_session(self, session_id: str) -> Optional[UserSession]:
        """
        세션을 검증합니다.
        
        Args:
            session_id: 세션 ID
            
        Returns:
            Optional[UserSession]: 유효한 세션, 만료됐거나 없으면 None
        """
        session = self._sessions.get(session_id)
        
        if not session:
            return None
        
        if session.expires_at and session.expires_at < datetime.now():
            del self._sessions[session_id]
            return None
        
        return session
    
    async def invalidate_session(self, session_id: str) -> bool:
        """
        세션을 무효화합니다.
        
        Args:
            session_id: 세션 ID
            
        Returns:
            bool: 성공 여부
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
    
    async def update_user_quota(self, user_id: str, quota: UserQuota) -> bool:
        """
        사용자 쿼터를 업데이트합니다.
        
        Args:
            user_id: 사용자 ID
            quota: 새 쿼터 정보
            
        Returns:
            bool: 성공 여부
        """
        data = await self._load_users()
        
        if user_id not in data.get("users", {}):
            return False
        
        data["users"][user_id]["quota"] = quota.model_dump()
        await self._save_users(data)
        return True
    
    async def get_all_users(self) -> list[User]:
        """
        모든 사용자 목록을 반환합니다.
        
        Returns:
            list[User]: 사용자 목록
        """
        data = await self._load_users()
        
        users = []
        for user_id in data.get("users", {}).keys():
            user = await self.get_user_by_id(user_id)
            if user:
                users.append(user)
        
        return users


# 싱글톤 인스턴스
auth_service = AuthService()
