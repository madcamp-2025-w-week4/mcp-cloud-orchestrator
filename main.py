# ============================================================================
# MCP Cloud Orchestrator - 애플리케이션 진입점
# ============================================================================
# 설명: FastAPI 애플리케이션 초기화 및 서버 실행
# 작성: Senior Cloud Infrastructure Engineer
# ============================================================================

import sys
from pathlib import Path
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from core.config import settings
from app.api import cluster_router
from services.health_monitor import health_monitor


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 수명주기 관리
    
    시작 시 리소스 초기화, 종료 시 정리 작업을 수행합니다.
    """
    # 시작 시 실행
    print("=" * 60)
    print(f"🚀 {settings.app_name} v{settings.app_version} 시작")
    print(f"📍 서버 주소: http://{settings.host}:{settings.port}")
    print(f"📚 API 문서: http://{settings.host}:{settings.port}/docs")
    print("=" * 60)
    
    yield
    
    # 종료 시 실행
    print("\n🛑 서버 종료 중...")
    await health_monitor.close()
    print("✅ 리소스 정리 완료")


# FastAPI 애플리케이션 생성
app = FastAPI(
    title=settings.app_name,
    description="""
    ## MCP Cloud Orchestrator API
    
    Tailscale VPN을 통해 연결된 17개 분산 CPU 노드를 관리하는 
    고가용성 클라우드 오케스트레이터입니다.
    
    ### 주요 기능
    
    - **클러스터 상태 모니터링**: 전체 클러스터의 헬스 상태 조회
    - **노드 관리**: 노드 등록, 수정, 삭제
    - **비동기 헬스체크**: 17개 노드 동시 헬스체크
    
    ### 기술 스택
    
    - FastAPI + Uvicorn (비동기 웹 프레임워크)
    - asyncio (동시성 처리)
    - Tailscale (VPN 네트워크)
    """,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(cluster_router)


@app.get("/", tags=["루트"])
async def root():
    """
    루트 엔드포인트 - API 정보 반환
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "MCP 기반 클라우드 오케스트레이터",
        "docs_url": "/docs",
        "cluster_status_url": "/cluster/status"
    }


@app.get("/health", tags=["헬스"])
async def health():
    """
    서버 헬스체크 엔드포인트
    """
    return {"status": "healthy", "service": settings.app_name}


if __name__ == "__main__":
    # 개발 서버 실행
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
