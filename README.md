# MCP Cloud Orchestrator

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.128.0-009688.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> LLM 제어가 가능한 경량 클라우드 인프라 오케스트레이터 (Model Context Protocol 기반)

Tailscale VPN을 통해 연결된 **17개 이상의 분산 CPU 노드**를 관리하고, 자동화된 리소스 할당, 실시간 모니터링, 그리고 원활한 장애 조치 기능을 제공합니다.

---

## 📋 주요 기능

- **노드 관리**: 17개 Tailscale 노드 등록, 조회, 수정, 삭제
- **비동기 헬스체크**: `asyncio.gather`를 활용한 동시 헬스 모니터링
- **클러스터 상태 모니터링**: 전체 클러스터 가용성 및 헬스 상태 조회
- **RESTful API**: FastAPI 기반의 완전한 API 문서 (Swagger UI)
- **MCP 통합**: Model Context Protocol을 통한 AI 제어 지원 (확장 예정)

---

## 🏗️ 프로젝트 구조

```
mcp-cloud-orchestrator/
├── setup.sh                 # 개발 환경 설정 스크립트
├── requirements.txt         # Python 의존성 목록
├── main.py                  # 애플리케이션 진입점
│
├── app/                     # FastAPI 애플리케이션
│   ├── __init__.py
│   ├── dependencies.py      # 의존성 주입
│   └── api/
│       └── routes/
│           └── cluster.py   # 클러스터 API 엔드포인트
│
├── core/                    # 핵심 설정 및 유틸리티
│   ├── __init__.py
│   ├── config.py           # Pydantic Settings 기반 환경 설정
│   └── exceptions.py       # 커스텀 예외 클래스
│
├── services/               # 비즈니스 로직 서비스
│   ├── __init__.py
│   ├── node_manager.py     # 노드 관리 서비스 (JSON 기반)
│   └── health_monitor.py   # 비동기 헬스 모니터링 서비스
│
├── models/                 # Pydantic 데이터 모델
│   ├── __init__.py
│   ├── node.py            # 노드 정보 및 상태 모델
│   └── cluster.py         # 클러스터 상태 모델
│
├── mcp/                   # MCP 프로토콜 모듈 (확장 예정)
│   └── __init__.py
│
└── data/                  # 데이터 저장소
    └── nodes.json         # 17개 Tailscale 노드 정보
```

---

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 개발 환경 설정 스크립트 실행 (가상환경 생성 + 의존성 설치)
chmod +x setup.sh
./setup.sh
```

### 2. 서버 실행

```bash
# 가상환경 활성화
source venv/bin/activate

# 서버 시작
python main.py
```

서버가 시작되면 다음과 같은 메시지가 출력됩니다:

```
============================================================
🚀 MCP Cloud Orchestrator v0.1.0 시작
📍 서버 주소: http://0.0.0.0:8000
📚 API 문서: http://0.0.0.0:8000/docs
============================================================
```

### 3. API 문서 확인

브라우저에서 다음 URL에 접속하여 Swagger UI를 확인할 수 있습니다:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 📡 API 엔드포인트

### 기본 엔드포인트

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| GET | `/` | API 정보 조회 |
| GET | `/health` | 서버 헬스체크 |

### 클러스터 API

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| GET | `/cluster/status` | 클러스터 전체 상태 조회 (17개 노드 동시 헬스체크) |
| GET | `/cluster/nodes` | 등록된 모든 노드 목록 조회 |
| GET | `/cluster/nodes/{node_id}` | 특정 노드 정보 조회 |
| GET | `/cluster/nodes/{node_id}/health` | 특정 노드 헬스체크 |
| POST | `/cluster/nodes` | 새 노드 등록 |
| PUT | `/cluster/nodes/{node_id}` | 노드 정보 수정 |
| DELETE | `/cluster/nodes/{node_id}` | 노드 삭제 |
| POST | `/cluster/health-check` | 전체 노드 헬스체크 실행 |

### API 사용 예시

```bash
# 클러스터 상태 조회
curl http://localhost:8000/cluster/status

# 클러스터 상태 조회 (노드 상세 정보 포함)
curl "http://localhost:8000/cluster/status?include_nodes=true"

# 모든 노드 목록 조회
curl http://localhost:8000/cluster/nodes

# 역할별 노드 필터링 (worker 노드만)
curl "http://localhost:8000/cluster/nodes?role=worker"

# 특정 노드 헬스체크
curl http://localhost:8000/cluster/nodes/node-01/health
```

---

## ⚙️ 환경 설정

### 환경 변수

`core/config.py`에서 다음 설정들을 환경 변수 또는 `.env` 파일로 변경할 수 있습니다:

| 변수명 | 기본값 | 설명 |
|--------|--------|------|
| `APP_NAME` | MCP Cloud Orchestrator | 애플리케이션 이름 |
| `APP_VERSION` | 0.1.0 | 애플리케이션 버전 |
| `DEBUG` | False | 디버그 모드 |
| `HOST` | 0.0.0.0 | 서버 바인딩 호스트 |
| `PORT` | 8000 | 서버 포트 |
| `NODES_FILE_PATH` | data/nodes.json | 노드 정보 파일 경로 |
| `HEALTH_CHECK_TIMEOUT` | 5.0 | 헬스체크 타임아웃 (초) |

### .env 파일 예시

```env
DEBUG=true
PORT=8080
HEALTH_CHECK_TIMEOUT=3.0
```

---

## 📊 노드 데이터 설정

`data/nodes.json` 파일을 수정하여 실제 Tailscale 노드 정보를 등록합니다:

```json
{
  "nodes": {
    "node-01": {
      "id": "node-01",
      "hostname": "your-hostname",
      "tailscale_ip": "100.x.x.x",
      "role": "master",
      "description": "마스터 노드",
      "cpu_cores": 16,
      "memory_gb": 64.0,
      "tags": ["production", "control-plane"]
    }
  }
}
```

### 노드 역할 (role)

- `master`: 클러스터 제어 담당
- `worker`: 범용 컴퓨팅 워커
- `storage`: 분산 스토리지 노드

---

## 🔧 기술 스택

| 구성 요소 | 기술 | 용도 |
|----------|------|------|
| 웹 프레임워크 | FastAPI | 비동기 REST API |
| ASGI 서버 | Uvicorn | 고성능 비동기 서버 |
| 데이터 검증 | Pydantic | 타입 안전한 데이터 모델 |
| 설정 관리 | pydantic-settings | 환경 변수 기반 설정 |
| HTTP 클라이언트 | httpx | 비동기 HTTP 요청 |
| SSH 관리 | Fabric | 원격 명령 실행 |
| 컨테이너 관리 | Docker SDK | 컨테이너 오케스트레이션 |
| 비동기 I/O | aiofiles | 비동기 파일 처리 |

---

## 📈 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                     Master Server                            │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              MCP Cloud Orchestrator                     │ │
│  │  ┌──────────┐  ┌──────────────┐  ┌──────────────────┐  │ │
│  │  │ FastAPI  │  │ Node Manager │  │ Health Monitor   │  │ │
│  │  │   API    │→ │   Service    │→ │ (asyncio.gather) │  │ │
│  │  └──────────┘  └──────────────┘  └──────────────────┘  │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                    Tailscale VPN Network
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   ┌────▼────┐           ┌────▼────┐           ┌────▼────┐
   │ Node 01 │           │ Node 02 │    ...    │ Node 17 │
   │ Master  │           │ Worker  │           │ Storage │
   └─────────┘           └─────────┘           └─────────┘
```

---

## 🛠️ 개발

### 의존성 추가

```bash
source venv/bin/activate
pip install <패키지명>
pip freeze > requirements.txt
```

### 디버그 모드 실행

```bash
DEBUG=true python main.py
```

---

## 📝 라이선스

MIT License

---

## 🤝 기여

버그 리포트, 기능 제안, Pull Request를 환영합니다!
