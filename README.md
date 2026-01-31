# MCP Cloud Orchestrator

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.0+-61DAFB.svg)](https://reactjs.org)
[![Tailwind](https://img.shields.io/badge/Tailwind-3.4+-38B2AC.svg)](https://tailwindcss.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **User-Facing Self-Service Portal** for container instance management  
> Similar to AWS EC2 Console - request, manage, and monitor container instances

Tailscale VPN을 통해 연결된 **18개 분산 노드** (1 Master + 17 Workers)를 관리하고, 
사용자가 직접 컨테이너 인스턴스를 요청, 관리, 모니터링할 수 있는 셀프서비스 포털입니다.

---

## 📋 주요 기능

### Backend (FastAPI + Ray SDK)
- **Ray 클러스터 통합**: `ray.nodes()`로 실시간 노드 모니터링
- **Docker 오케스트레이션**: SSH로 원격 노드에 컨테이너 배포
- **인스턴스 관리**: 생성, 조회, 중지, 시작, 종료
- **포트 할당**: 노드별 자동 포트 할당 (8000-9000)
- **쿼터 관리**: 사용자별 CPU/RAM 제한 및 모니터링
- **지능형 노드 선택**: Ray 기반 가장 여유있는 노드 자동 선택

### Frontend (React + Tailwind CSS - English UI)
- **Dashboard**: Ray 클러스터 리소스 (CPU/GPU/Memory 사용량)
- **Instance Table**: Instance ID, Node Name, IP:Port, Status
- **Launch Wizard**: 이미지 선택 + CPU/RAM 설정 + 리뷰
- **Ray Dashboard 링크**: 사이드바에서 바로 접속
- **AWS Console 스타일**: 프로페셔널한 데이터 밀집 UI

---

## 🏗️ 클러스터 구성

| 역할 | 호스트명 | Tailscale IP |
|------|----------|--------------|
| **Master** | camp-gpu-16 | 100.117.45.28 |
| Worker | camp-61 | 100.112.111.30 |
| Worker | camp-62 | 100.74.193.12 |
| Worker | camp-64 | 100.119.242.41 |
| Worker | camp-65 | 100.67.220.41 |
| Worker | camp-66 | 100.83.132.110 |
| Worker | camp-68 | 100.104.2.109 |
| Worker | camp-69 | 100.126.50.128 |
| Worker | camp-70 | 100.64.115.13 |
| Worker | camp-72 | 100.116.93.104 |
| Worker | camp-73 | 100.99.12.56 |
| Worker | camp-74 | 100.81.63.9 |
| Worker | camp-75 | 100.74.1.74 |
| Worker | camp-76 | 100.113.187.81 |
| Worker | camp-77 | 100.77.10.106 |
| Worker | camp-78 | 100.86.244.76 |
| Worker | camp-79 | 100.90.20.37 |
| Worker | camp-80 | 100.113.169.101 |

---

## ⚠️ 접속 요구사항

> **중요**: 이 시스템에 접속하려면 **Tailscale VPN**에 연결되어 있어야 합니다.

클러스터의 모든 노드는 Tailscale VPN을 통해 연결되어 있습니다. 포털에 접속하기 전에:

1. [Tailscale](https://tailscale.com)을 설치합니다
2. 조직의 Tailscale 네트워크에 로그인합니다
3. VPN이 연결된 상태에서 아래 URL로 접속합니다:
   - **프론트엔드**: http://100.117.45.28:5174
   - **백엔드 API**: http://100.117.45.28:8000
   - **API 문서**: http://100.117.45.28:8000/docs
   - **Ray Dashboard**: http://100.117.45.28:8265

---

## 🌐 프로덕션 배포 (Nginx + Tailscale Funnel)

Nginx 리버스 프록시를 사용하여 **단일 공개 URL**로 다중 사용자 접근을 지원합니다.

### 공개 접속 URL
```
https://camp-gpu-16.tailab95b0.ts.net/
```

### 아키텍처
```
Internet → Tailscale Funnel (Port 80)
                ↓
            Nginx Reverse Proxy
           /           \
      /api/*           /*
         ↓              ↓
    Backend:8000   Frontend:5174
```

### 배포 방법

```bash
# 1. Nginx 배포 스크립트 실행
cd /root/mcp-cloud-orchestrator
sudo ./deploy.sh

# 2. Backend 시작
cd backend && source venv/bin/activate && python main.py &

# 3. Frontend 시작
cd frontend && npm run dev &

# 4. Tailscale Funnel 시작 (공개 접근 활성화)
sudo tailscale funnel 80
```

### 라우팅 규칙
| URL 패턴 | 라우팅 대상 |
|----------|-------------|
| `/api/*` | Backend (localhost:8000) |
| `/*` | Frontend (localhost:5174) |

---

## 🚀 빠른 시작

### 0. Ray 클러스터 설정 (필수)

Backend를 실행하기 전에 Ray 클러스터가 실행 중이어야 합니다.

**Master 노드에서 Ray Head 시작:**
```bash
# Master 서버 (camp-gpu-16)에서 실행
ray start --head --port=6379 --dashboard-host=0.0.0.0 --dashboard-port=8265
```

**각 Worker 노드에서 Ray 연결:**
```bash
# 각 Worker 서버에서 실행 (Master IP를 Tailscale IP로 지정)
ray start --address='100.117.45.28:6379'
```

**Ray 클러스터 상태 확인:**
```bash
# 연결된 노드 확인
ray status

# Ray Dashboard 접속
# http://100.117.45.28:8265
```

### 1. Backend 설정 및 실행

```bash
# 프로젝트 디렉토리로 이동
cd /root/mcp-cloud-orchestrator/backend

# Python 가상환경 생성 (처음 한 번만)
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 서버 실행
python main.py
```

서버가 시작되면:
```
============================================================
🚀 MCP Cloud Orchestrator v0.1.0 시작
📍 서버 주소: http://0.0.0.0:8000
📚 API 문서: http://0.0.0.0:8000/docs
============================================================
Ray connected: {'CPU': 108.0, 'memory': ...}
```

### 2. Frontend 설정 및 실행

```bash
# 새 터미널에서 frontend 디렉토리로 이동
cd /root/mcp-cloud-orchestrator/frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

프론트엔드 서버가 시작되면:
- **URL**: http://localhost:5173

---

## 📡 API 엔드포인트

### 인증 API
| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| POST | `/auth/login` | 로그인 |
| GET | `/auth/me` | 현재 사용자 정보 |
| GET | `/auth/quota` | 쿼터 정보 |

### 인스턴스 API
| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| POST | `/instances` | 인스턴스 생성 |
| GET | `/instances` | 인스턴스 목록 |
| GET | `/instances/{id}` | 인스턴스 상세 |
| POST | `/instances/{id}/stop` | 인스턴스 중지 |
| POST | `/instances/{id}/start` | 인스턴스 시작 |
| DELETE | `/instances/{id}` | 인스턴스 종료 |

### 대시보드 API
| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| GET | `/dashboard/summary` | 대시보드 요약 |
| GET | `/dashboard/health` | 클러스터 헬스 |
| GET | `/dashboard/nodes/status` | 노드 상태 목록 |
| GET | `/dashboard/images` | 사용 가능한 이미지 |

### 클러스터 API
| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| GET | `/cluster/status` | 클러스터 전체 상태 |
| GET | `/cluster/nodes` | 노드 목록 |
| POST | `/cluster/health-check` | 전체 헬스체크 |

---

## 💡 API 사용 예시

```bash
# 로그인
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "demo"}'

# 인스턴스 생성
curl -X POST http://localhost:8000/instances \
  -H "Content-Type: application/json" \
  -H "X-User-ID: user-demo-001" \
  -d '{"name": "my-server", "image": "ubuntu:22.04", "cpu": 2, "memory": 4}'

# 인스턴스 목록 조회
curl http://localhost:8000/instances \
  -H "X-User-ID: user-demo-001"

# 인스턴스 중지
curl -X POST http://localhost:8000/instances/{instance_id}/stop \
  -H "X-User-ID: user-demo-001"

# 인스턴스 종료
curl -X DELETE http://localhost:8000/instances/{instance_id} \
  -H "X-User-ID: user-demo-001"

# 대시보드 요약
curl http://localhost:8000/dashboard/summary \
  -H "X-User-ID: user-demo-001"
```

---

## 🔐 기본 사용자

| 사용자 | 비밀번호 | 설명 |
|--------|----------|------|
| `demo` | `demo` | 데모 사용자 (인스턴스 5개 제한) |
| `admin` | `admin` | 관리자 (인스턴스 20개 제한) |

---

## 🛠️ 기술 스택

### Backend
| 구성 요소 | 기술 | 용도 |
|----------|------|------|
| 웹 프레임워크 | FastAPI | 비동기 REST API |
| ASGI 서버 | Uvicorn | 고성능 비동기 서버 |
| 데이터 검증 | Pydantic | 타입 안전한 데이터 모델 |
| HTTP 클라이언트 | httpx | 비동기 HTTP 요청 |
| 비동기 I/O | aiofiles | 비동기 파일 처리 |

### Frontend
| 구성 요소 | 기술 | 용도 |
|----------|------|------|
| UI 라이브러리 | React 18 | 컴포넌트 기반 UI |
| 빌드 도구 | Vite | 빠른 개발 서버 |
| CSS 프레임워크 | Tailwind CSS | 유틸리티 우선 스타일링 |
| HTTP 클라이언트 | Axios | API 통신 |
| 아이콘 | Lucide React | SVG 아이콘 |

---

## 📊 프로젝트 구조

```
mcp-cloud-orchestrator/
├── backend/
│   ├── main.py                    # FastAPI 진입점
│   ├── requirements.txt           # Python 의존성
│   ├── app/
│   │   └── api/routes/            # API 라우터
│   │       ├── auth.py            # 인증 API
│   │       ├── instances.py       # 인스턴스 API
│   │       ├── dashboard.py       # 대시보드 API
│   │       └── cluster.py         # 클러스터 API
│   ├── models/                    # Pydantic 모델
│   │   ├── instance.py
│   │   ├── user.py
│   │   ├── node.py
│   │   └── cluster.py
│   ├── services/                  # 비즈니스 로직
│   │   ├── instance_manager.py    # 인스턴스 관리
│   │   ├── auth_service.py        # 인증 서비스
│   │   ├── port_allocator.py      # 포트 할당
│   │   ├── quota_service.py       # 쿼터 관리
│   │   └── health_monitor.py      # 헬스 모니터링
│   ├── data/                      # JSON 저장소
│   │   ├── nodes.json
│   │   ├── instances.json
│   │   ├── users.json
│   │   └── port_allocations.json
│   └── core/                      # 설정 및 예외
│       ├── config.py
│       └── exceptions.py
│
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── tailwind.config.js
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── index.css              # Tailwind + 커스텀 스타일
        ├── api/
        │   └── client.js          # Axios API 클라이언트
        └── components/
            ├── layout/            # Sidebar, Header
            ├── dashboard/         # DashboardView, StatsCard, QuotaWidget
            ├── instances/         # InstancesView, StatusBadge
            ├── wizard/            # LaunchWizard
            └── nodes/             # NodesView
```

---

## ⚡ AWS-Style 리소스 검증

인스턴스 생성 시 **클러스터 실제 용량을 검증**합니다. 요청한 리소스를 제공할 수 있는 Worker 노드가 없으면 `InsufficientCapacity` 에러를 반환합니다.

### 용량 API
```bash
# 클러스터 가용 용량 조회
curl http://localhost:8000/dashboard/capacity
```

응답 예시:
```json
{
  "max_cpu": 4,
  "max_memory_gb": 2,
  "cpu_options": [1, 2, 4],
  "memory_options": [2]
}
```

### InsufficientCapacity 에러
```json
{
  "error": "InsufficientCapacity",
  "message": "Requested 8 vCPU and 16 GB RAM, but max available is 4 vCPU and 2 GB RAM.",
  "max_cpu_available": 4,
  "max_memory_available": 2
}
```

> **참고**: Launch Wizard UI는 실제 가용 리소스만 선택 가능하도록 동적으로 옵션을 표시합니다.

---

## 🖥️ Web Terminal

인스턴스 목록에서 **Terminal 아이콘**을 클릭하면 브라우저에서 직접 터미널 접속:

- **WebSocket 기반** 실시간 통신
- **xterm.js** + Catppuccin Mocha 테마
- `docker exec`를 통한 컨테이너 접속

---

## 📝 라이선스

MIT License

---

## 🤝 기여

버그 리포트, 기능 제안, Pull Request를 환영합니다!

