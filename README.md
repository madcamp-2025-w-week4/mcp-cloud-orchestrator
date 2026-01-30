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

### Backend (FastAPI)
- **인스턴스 관리**: 생성, 조회, 중지, 시작, 종료
- **사용자 인증**: 세션 기반 인증 및 소유권 관리
- **포트 할당**: 노드별 자동 포트 할당 (8000번부터)
- **쿼터 관리**: 사용자별 CPU/RAM 제한 및 모니터링
- **클러스터 헬스**: 실시간 노드 상태 확인

### Frontend (React + Tailwind CSS)
- **Dashboard**: 인스턴스/노드/쿼터 요약 표시
- **Instance Table**: 상태, IP:Port, 업타임, 액션 버튼
- **Launch Wizard**: 3단계 인스턴스 생성 마법사
- **Nodes View**: 클러스터 노드 상태 모니터링
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

## 🚀 빠른 시작

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

## 📝 라이선스

MIT License

---

## 🤝 기여

버그 리포트, 기능 제안, Pull Request를 환영합니다!
