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
from app.api import cluster_router, instances_router, auth_router, dashboard_router, ray_router, terminal_router
from services.health_monitor import health_monitor
from services.ray_service import ray_service
from services.docker_orchestrator import docker_orchestrator


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
    print(f"🎯 Ray Dashboard: http://100.117.45.28:8265")
    print("=" * 60)
    
    yield
    
    # 종료 시 실행
    print("\n🛑 서버 종료 중...")
    await health_monitor.close()
    docker_orchestrator.close_all_connections()
    ray_service.disconnect()
    print("✅ 리소스 정리 완료")


# FastAPI 애플리케이션 생성
app = FastAPI(
    title=settings.app_name,
    description="""
    ## MCP Cloud Orchestrator API
    
    User-Facing Self-Service Portal for container instance management.
    Similar to AWS EC2 Console - request, manage, and monitor container instances.
    
    ### Features
    
    - **Instance Management**: Launch, stop, start, terminate instances
    - **Resource Quotas**: CPU/Memory quota tracking per user
    - **Cluster Monitoring**: Real-time node health status
    - **Port Allocation**: Automatic unique port assignment (8000+)
    
    ### Authentication
    
    Use `X-User-ID` header to identify the user (demo: `user-demo-001`)
    """,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS 미들웨어 설정
# Production: Tailscale Funnel을 통한 접근 허용
ALLOWED_ORIGINS = [
    "https://kws.p-e.kr",
    "http://kws.p-e.kr",
    "https://camp-gpu-16.tailab95b0.ts.net",
    "http://camp-gpu-16.tailab95b0.ts.net",
    "http://localhost:5174",
    "http://localhost:80",
    "http://127.0.0.1:5174",
    "http://100.117.45.28:5174",
    "http://100.117.45.28",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(cluster_router)
app.include_router(instances_router)
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(ray_router)
app.include_router(terminal_router)


@app.get("/", tags=["Root"])
async def root():
    """
    루트 엔드포인트 - API 정보 반환
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "User-Facing Self-Service Portal for Container Instances",
        "docs_url": "/docs",
        "ray_dashboard": "http://100.117.45.28:8265",
        "endpoints": {
            "instances": "/instances",
            "auth": "/auth",
            "dashboard": "/dashboard",
            "cluster": "/cluster",
            "ray": "/ray"
        }
    }


@app.get("/health", tags=["Health"])
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
