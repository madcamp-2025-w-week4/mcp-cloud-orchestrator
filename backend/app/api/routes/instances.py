# ============================================================================
# MCP Cloud Orchestrator - 인스턴스 API 라우터
# ============================================================================
# 설명: 사용자 인스턴스 관리 API 엔드포인트
# ============================================================================

from fastapi import APIRouter, HTTPException, Header, Query
from typing import Optional

from models.instance import Instance, InstanceCreate, InstanceSummary, InstanceStatus
from services.instance_manager import instance_manager, InstanceNotFoundException, QuotaExceededException
from core.exceptions import MCPOrchestratorException


# 라우터 생성
router = APIRouter(
    prefix="/instances",
    tags=["Instances"],
    responses={
        404: {"description": "Instance not found"},
        403: {"description": "Access denied"},
        400: {"description": "Bad request"}
    }
)


def get_user_id(x_user_id: Optional[str] = Header(None, alias="X-User-ID")) -> str:
    """
    요청에서 사용자 ID를 추출합니다.
    
    프로덕션에서는 JWT 토큰에서 추출해야 합니다.
    """
    if not x_user_id:
        # 기본 사용자 (데모용)
        return "user-demo-001"
    return x_user_id


@router.post(
    "",
    response_model=Instance,
    status_code=201,
    summary="Launch Instance",
    description="Launch a new container instance with the specified configuration."
)
async def create_instance(
    request: InstanceCreate,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
) -> Instance:
    """
    새 인스턴스를 생성합니다.
    
    - **name**: 인스턴스 이름
    - **image**: 컨테이너 이미지 (예: ubuntu:22.04)
    - **cpu**: CPU 코어 수 (1-8)
    - **memory**: 메모리 GB (1-32)
    """
    user_id = get_user_id(x_user_id)
    
    try:
        instance = await instance_manager.create_instance(user_id, request)
        return instance
    except QuotaExceededException as e:
        raise HTTPException(status_code=400, detail=e.detail)
    except MCPOrchestratorException as e:
        raise HTTPException(status_code=500, detail=e.message)


@router.get(
    "",
    response_model=list[Instance],
    summary="List Instances",
    description="List all instances owned by the current user."
)
async def list_instances(
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    status: Optional[InstanceStatus] = Query(None, description="Filter by status")
) -> list[Instance]:
    """
    사용자의 모든 인스턴스를 조회합니다.
    
    - **status**: 상태별 필터링 (running, stopped, pending)
    """
    user_id = get_user_id(x_user_id)
    
    instances = await instance_manager.get_user_instances(user_id)
    
    if status:
        instances = [i for i in instances if i.status == status]
    
    return instances


@router.get(
    "/summary",
    response_model=dict,
    summary="Instance Summary",
    description="Get a summary of instance counts by status."
)
async def get_instance_summary(
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
) -> dict:
    """
    사용자의 인스턴스 요약 정보를 반환합니다.
    """
    user_id = get_user_id(x_user_id)
    
    return await instance_manager.get_instance_summary(user_id)


@router.get(
    "/{instance_id}",
    response_model=Instance,
    summary="Get Instance",
    description="Get details of a specific instance."
)
async def get_instance(
    instance_id: str,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
) -> Instance:
    """
    특정 인스턴스의 상세 정보를 조회합니다.
    
    - **instance_id**: 인스턴스 ID
    """
    user_id = get_user_id(x_user_id)
    
    try:
        return await instance_manager.get_instance(instance_id, user_id)
    except InstanceNotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.post(
    "/{instance_id}/stop",
    response_model=Instance,
    summary="Stop Instance",
    description="Stop a running instance."
)
async def stop_instance(
    instance_id: str,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
) -> Instance:
    """
    실행 중인 인스턴스를 중지합니다.
    
    - **instance_id**: 인스턴스 ID
    """
    user_id = get_user_id(x_user_id)
    
    try:
        return await instance_manager.stop_instance(instance_id, user_id)
    except InstanceNotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except MCPOrchestratorException as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.post(
    "/{instance_id}/start",
    response_model=Instance,
    summary="Start Instance",
    description="Start a stopped instance."
)
async def start_instance(
    instance_id: str,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
) -> Instance:
    """
    중지된 인스턴스를 시작합니다.
    
    - **instance_id**: 인스턴스 ID
    """
    user_id = get_user_id(x_user_id)
    
    try:
        return await instance_manager.start_instance(instance_id, user_id)
    except InstanceNotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except MCPOrchestratorException as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.delete(
    "/{instance_id}",
    status_code=204,
    summary="Terminate Instance",
    description="Terminate and delete an instance permanently."
)
async def terminate_instance(
    instance_id: str,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
) -> None:
    """
    인스턴스를 종료하고 삭제합니다.
    
    - **instance_id**: 인스턴스 ID
    
    주의: 이 작업은 되돌릴 수 없습니다.
    """
    user_id = get_user_id(x_user_id)
    
    try:
        await instance_manager.terminate_instance(instance_id, user_id)
    except InstanceNotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
