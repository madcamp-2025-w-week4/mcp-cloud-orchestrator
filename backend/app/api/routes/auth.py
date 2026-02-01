# ============================================================================
# MCP Cloud Orchestrator - 인증 API 라우터
# ============================================================================
# 설명: 사용자 인증 및 세션 관리 API 엔드포인트
# ============================================================================

from fastapi import APIRouter, HTTPException, Header
from typing import Optional

from models.user import UserLogin, UserSession, UserPublic, UserQuota
from services.auth_service import auth_service
from services.quota_service import quota_service


# 라우터 생성
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "User not found"}
    }
)


@router.post(
    "/login",
    response_model=UserSession,
    summary="User Login",
    description="Authenticate user and create a session."
)
async def login(credentials: UserLogin) -> UserSession:
    """
    사용자를 인증하고 세션을 생성합니다.
    
    - **username**: 사용자 이름
    - **password**: 비밀번호
    """
    session = await auth_service.authenticate(credentials.username, credentials.password)
    
    if not session:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )
    
    return session


@router.get(
    "/me",
    response_model=UserPublic,
    summary="Get Current User",
    description="Get information about the currently authenticated user."
)
async def get_current_user(
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
) -> UserPublic:
    """
    현재 인증된 사용자 정보를 반환합니다.
    """
    if not x_user_id:
        x_user_id = "user-demo-001"  # 기본 데모 사용자
    
    user = await auth_service.get_user_by_id(x_user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserPublic(
        id=user.id,
        username=user.username,
        quota=user.quota,
        is_active=user.is_active
    )


@router.get(
    "/quota",
    response_model=dict,
    summary="Get Resource Quota",
    description="Get the current user's resource quota and usage."
)
async def get_quota(
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
) -> dict:
    """
    현재 사용자의 리소스 쿼터 및 사용량을 반환합니다.
    """
    if not x_user_id:
        x_user_id = "user-demo-001"  # 기본 데모 사용자
    
    summary = await quota_service.get_quota_summary(x_user_id)
    
    if not summary:
        raise HTTPException(status_code=404, detail="User not found")
    
    return summary


@router.post(
    "/logout",
    status_code=204,
    summary="User Logout",
    description="Invalidate the current session."
)
async def logout(
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
) -> None:
    """
    현재 세션을 무효화합니다.
    """
    if x_session_id:
        await auth_service.invalidate_session(x_session_id)


@router.get(
    "/billing",
    response_model=dict,
    summary="Get Billing Summary",
    description="Get the current user's usage-based billing information."
)
async def get_billing(
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
) -> dict:
    """
    현재 사용자의 청구 요약을 반환합니다.
    
    AWS/Railway 스타일 사용량 기반 청구:
    - CPU: $0.02/hour per vCPU
    - Memory: $0.01/hour per GB
    - Instance: $0.005/hour per instance
    """
    from services.billing_service import billing_service
    
    if not x_user_id:
        x_user_id = "user-demo-001"
    
    summary = await billing_service.get_billing_summary(x_user_id)
    return summary
