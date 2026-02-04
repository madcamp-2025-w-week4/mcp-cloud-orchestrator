# MCP Cloud Orchestrator

> **Live Demo**: [https://camp-gpu-16.tailab95b0.ts.net/](https://camp-gpu-16.tailab95b0.ts.net/)

> **"클라우드 인스턴스를 손쉽게 관리하세요"** - AWS EC2 Console과 유사한 사용자 친화적 셀프서비스 포털

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://reactjs.org)
[![Ray](https://img.shields.io/badge/Ray-2.9.0-00A3E0?logo=ray&logoColor=white)](https://ray.io)
[![Tailwind](https://img.shields.io/badge/Tailwind-3.4+-38B2AC?logo=tailwindcss&logoColor=white)](https://tailwindcss.com)  

## 팀원 : PNU 21 윤민석, SNU 20 김민기
---

## 📝 목차

1. [프로젝트 소개](#-프로젝트-소개)
   - [기획 의도](#-기획-의도)
   - [주요 기능](#-주요-기능)
2. [시스템 아키텍처](#%EF%B8%8F-시스템-아키텍처)
3. [클러스터 구성](#-클러스터-구성)
4. [기술 스택](#%EF%B8%8F-기술-스택)
5. [Getting Started](#-getting-started)
   - [접속 요구사항](#접속-요구사항)
   - [Ray 클러스터 설정](#1-ray-클러스터-설정-필수)
   - [Backend 실행](#2-backend-설정-및-실행)
   - [Frontend 실행](#3-frontend-설정-및-실행)
   - [프로덕션 배포](#-프로덕션-배포)
6. [API 문서](#-api-문서)

---

## 📖 프로젝트 소개

**MCP Cloud Orchestrator**는 Tailscale VPN을 통해 연결된 **18개 분산 노드** (1 Master + 17 Workers)를 관리하고, 사용자가 직접 컨테이너 인스턴스를 요청, 관리, 모니터링할 수 있는 셀프서비스 포털입니다.

### 🎯 기획 의도

클라우드 인프라를 보다 쉽게 접근할 수 있도록, AWS EC2 Console과 유사한 직관적인 UI/UX를 제공합니다. Ray 클러스터를 활용하여 분산 노드의 리소스를 실시간으로 모니터링하고, 사용자는 웹 브라우저만으로 컨테이너 인스턴스를 생성하고 관리할 수 있습니다.

### ✨ 주요 기능

| 기능 | 설명 |
|------|------|
| **Ray 클러스터 통합** | `ray.nodes()`로 18개 노드의 CPU/GPU/Memory를 실시간으로 모니터링합니다. |
| **Docker 오케스트레이션** | SSH를 통해 원격 노드에 컨테이너를 자동으로 배포하고 관리합니다. |
| **인스턴스 생명주기 관리** | 생성, 조회, 중지, 시작, 종료까지 완벽한 인스턴스 관리를 제공합니다. |
| **웹 기반 터미널** | 브라우저에서 직접 컨테이너에 접속하여 콘솔 명령어를 실행할 수 있는 Web Terminal을 제공합니다. |
| **자동 포트 할당** | 노드별로 8000-9000 범위에서 자동으로 포트를 할당하여 충돌을 방지합니다. |
| **쿼터 관리 시스템** | 사용자별 CPU/RAM 제한을 설정하고 실시간으로 사용량을 모니터링합니다. |
| **지능형 노드 선택** | Ray 리소스 정보를 기반으로 가장 여유 있는 노드를 자동으로 선택합니다. |
| **AWS Console 스타일 UI** | 프로페셔널한 데이터 밀집형 UI로 직관적인 사용자 경험을 제공합니다. |
| **Tailscale VPN 통합** | 보안성과 편의성을 동시에 확보한 VPN 기반 네트워크를 구축합니다. |

---

## 🏗️ 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Client (Frontend)                    │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐ │
│  │ Dashboard │  │ Instances │  │   Wizard  │  │   Nodes   │ │
│  │           │  │           │  │           │  │           │ │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘ │
│        └──────────────┴──────┬───────┴──────────────┘       │
│                              │ HTTP/REST API                │
└──────────────────────────────┼──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│               FastAPI Backend (Master Node)                 │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐ │
│  │   Auth    │  │ Instance  │  │  Cluster  │  │ Dashboard │ │
│  │  Service  │  │  Manager  │  │  Manager  │  │  Service  │ │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘ │
│        │              │              │              │       │
│        │        ┌─────┴──────────────┴─────┐        │       │
│        │        │   Port Allocator         │        │       │
│        │        │   Quota Manager          │        │       │
│        │        │   Health Monitor         │        │       │
│        │        └───────────┬──────────────┘        │       │
│        │                    │                       │       │
│  ┌─────▼─────┐        ┌─────▼─────┐           ┌─────▼─────┐ │
│  │  JSON DB  │        │Ray Cluster│           │SSH Executor│ │
│  │ (Storage) │        │ (Ray SDK) │           │ (asyncssh)│ │
│  └───────────┘        └─────┬─────┘           └─────┬─────┘ │
└─────────────────────────────┼─────────────────────┬─┘       │
                              │                     │         │
                    ┌─────────▼──────────┐          │         │
                    │   Ray Head Node    │          │         │
                    │  (100.117.45.28)   │          │         │
                    └─────────┬──────────┘          │         │
                              │                     │         │
        ┌─────────────────────┴──────────────┬──────┴─────────┘
        │                                    │
┌───────▼────────┐                   ┌───────▼────────┐
│ Worker Node 1  │    ...  ...       │ Worker Node 17 │
│ Docker Runtime │                   │ Docker Runtime │
└────────────────┘                   └────────────────┘
```

## 📡 클러스터 구성

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

## 🛠️ 기술 스택

### Frontend

| 구분 | 기술 |
|------|------|
| **Language** | JavaScript (ES6+) |
| **Framework** | React 18 + Vite |
| **Styling** | Tailwind CSS |
| **HTTP Client** | Axios |
| **Icons** | Lucide React |
| **Build Tool** | Vite (Fast Dev Server) |

### Backend

| 구분 | 기술 |
|------|------|
| **Framework** | FastAPI (Python 3.10+) |
| **ASGI Server** | Uvicorn |
| **Cluster Management** | Ray SDK (ray.nodes()) |
| **Container Runtime** | Docker (via SSH) |
| **SSH Client** | asyncssh |
| **Data Validation** | Pydantic |
| **Async I/O** | aiofiles, httpx |
| **Storage** | JSON File-based DB |

### Infrastructure

| 구분 | 기술 |
|------|------|
| **VPN** | Tailscale (Mesh Network) |
| **Reverse Proxy** | Nginx |
| **Deployment** | Tailscale Funnel (Public Access) |
| **Orchestration** | Ray Cluster (18 Nodes) |

---

## 🚀 Getting Started

### 접속 요구사항

> **⚠️ 중요**: 이 시스템에 접속하려면 **Tailscale VPN**에 연결되어 있어야 합니다.

클러스터의 모든 노드는 Tailscale VPN을 통해 연결되어 있습니다. 포털에 접속하기 전에:

1. [Tailscale](https://tailscale.com)을 설치합니다
2. 조직의 Tailscale 네트워크에 로그인합니다
3. VPN이 연결된 상태에서 아래 URL로 접속합니다:
   - **프론트엔드**: http://100.117.45.28:5174
   - **백엔드 API**: http://100.117.45.28:8000
   - **API 문서**: http://100.117.45.28:8000/docs
   - **Ray Dashboard**: http://100.117.45.28:8265

### 1. Ray 클러스터 설정 (필수)

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

### 2. Backend 설정 및 실행

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

### 3. Frontend 설정 및 실행

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

### 🌐 프로덕션 배포

**공개 접속 URL**:
```
https://camp-gpu-16.tailab95b0.ts.net/
```

**배포 방법**:

```bash
# 1. Nginx 설정 배포
cd /root/mcp-cloud-orchestrator
sudo ./deploy.sh

# 2. Backend 시작 (tmux 세션 권장)
cd backend && source venv/bin/activate && python main.py

# 3. Frontend 시작 (새 tmux 세션)
cd frontend && npm run dev -- --host 0.0.0.0 --port 5174

# 4. Tailscale Funnel 시작 (공개 접근)
sudo tailscale funnel 80
```

**라우팅 규칙**:
- `/api/*` → Backend (localhost:8000)
- `/*` → Frontend (localhost:5174)

---

## 📡 API 문서

서버 실행 후 아래 URL에서 자동 생성된 문서를 확인할 수 있습니다:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 주요 엔드포인트

#### 인증 API
| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| `POST` | `/auth/login` | 로그인 및 토큰 발급 |
| `GET` | `/auth/me` | 현재 사용자 정보 |
| `GET` | `/auth/quota` | 쿼터 정보 조회 |

#### 인스턴스 API
| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| `POST` | `/instances` | 인스턴스 생성 |
| `GET` | `/instances` | 인스턴스 목록 조회 |
| `GET` | `/instances/{id}` | 인스턴스 상세 조회 |
| `POST` | `/instances/{id}/stop` | 인스턴스 중지 |
| `POST` | `/instances/{id}/start` | 인스턴스 시작 |
| `DELETE` | `/instances/{id}` | 인스턴스 종료 |

#### 대시보드 API
| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| `GET` | `/dashboard/summary` | 대시보드 요약 |
| `GET` | `/dashboard/health` | 클러스터 헬스 |
| `GET` | `/dashboard/nodes/status` | 노드 상태 목록 |
| `GET` | `/dashboard/images` | 사용 가능한 이미지 목록 |

#### 클러스터 API
| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| `GET` | `/cluster/status` | 클러스터 전체 상태 |
| `GET` | `/cluster/nodes` | 노드 목록 조회 |
| `POST` | `/cluster/health-check` | 전체 노드 헬스체크 |

### API 사용 예시

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

# 대시보드 요약
curl http://localhost:8000/dashboard/summary \
  -H "X-User-ID: user-demo-001"
```

### 기본 사용자

| 사용자 | 비밀번호 | 권한 |
|--------|----------|------|
| `demo` | `demo` | 인스턴스 5개 제한 |
| `admin` | `admin` | 인스턴스 20개 제한 |

---

