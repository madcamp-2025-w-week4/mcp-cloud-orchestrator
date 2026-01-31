# MCP Cloud Orchestrator - 사용자 안내서 (WALKTHROUGH)

## 개요

MCP Cloud Orchestrator는 Ray 클러스터 위에 구축된 사용자 셀프서비스 컨테이너 관리 포털입니다.
AWS EC2 Console과 유사한 방식으로 컨테이너 인스턴스를 생성, 관리, 모니터링할 수 있습니다.

---

## 사전 요구사항

1. **Tailscale VPN** 연결 필수
   - 모든 클러스터 노드는 Tailscale VPN을 통해 연결됩니다
   - [https://tailscale.com](https://tailscale.com) 에서 설치 후 조직 네트워크에 로그인

2. **접속 URL**
   - 프론트엔드: `http://100.117.45.28:5174`
   - API 문서: `http://100.117.45.28:8000/docs`
   - Ray Dashboard: `http://100.117.45.28:8265`

---

## 사용자 흐름

### 1️⃣ 로그인

현재 데모 모드로 운영되며, 기본 사용자 ID(`user-demo-001`)가 자동 할당됩니다.

### 2️⃣ Dashboard 확인

로그인 후 Dashboard에서 다음 정보를 확인할 수 있습니다:

- **Instance 현황**: 실행 중/중지됨/대기 중 인스턴스 수
- **Node 현황**: 클러스터 노드 수 및 가용성
- **Ray Cluster Resources**: CPU/Memory/GPU 전체 및 사용량
- **Your Quota**: 할당된 리소스 한도 및 사용량

### 3️⃣ 인스턴스 생성 (Launch Instance)

1. **"Launch Instance"** 버튼 클릭
2. **Step 1 - Select Image**: 원하는 컨테이너 이미지 선택
   - Ubuntu 22.04, Python 3.11, Node.js 20, Nginx 등
3. **Step 2 - Configure Resources**: CPU/Memory 설정
   - 쿼터 한도 내에서 선택
4. **Step 3 - Review & Launch**: 설정 확인 후 생성

생성된 인스턴스는 자동으로:
- 가장 여유있는 워커 노드에 배치 (Ray SDK 기반)
- 고유 포트 할당 (8000번부터)
- Docker 컨테이너로 실행

### 4️⃣ 인스턴스 접속

생성된 인스턴스의 **Public Endpoint**로 접속합니다:

```
http://{Node_IP}:{Port}
예: http://100.104.2.109:8001
```

Instances 테이블에서 IP:Port 정보를 확인할 수 있습니다.

### 5️⃣ 인스턴스 관리

**Instances** 페이지에서 다음 작업을 수행할 수 있습니다:

| 액션 | 설명 |
|------|------|
| **Stop** | 실행 중인 인스턴스 중지 |
| **Start** | 중지된 인스턴스 재시작 |
| **Terminate** | 인스턴스 영구 삭제 |

### 6️⃣ Ray Dashboard

사이드바의 **Ray Dashboard** 링크를 클릭하면 Ray 클러스터의 상세 상태를 확인할 수 있습니다:
- 노드별 리소스 사용량
- Actor/Task 상태
- 클러스터 로그

---

## 리소스 쿼터

각 사용자에게 기본 쿼터가 할당됩니다:

| 리소스 | 기본 한도 |
|--------|----------|
| Instances | 5개 |
| CPU | 16 코어 |
| Memory | 32 GB |

쿼터 초과 시 새 인스턴스 생성이 거부됩니다.

---

## 아키텍처

```
사용자 → Frontend (React) → Backend (FastAPI) → Ray Cluster
                                              ↓
                                    Docker Container 배포
                                              ↓
                                    Worker Node (camp-61~80)
```

- **Backend**: FastAPI + Ray SDK + Fabric (SSH)
- **Frontend**: React + Tailwind CSS
- **Orchestration**: Ray 기반 노드 선택, Docker 컨테이너 배포

---

## 문제 해결

### 연결이 안 될 때
1. Tailscale VPN 연결 상태 확인
2. `ping 100.117.45.28` 테스트
3. 방화벽 설정 확인

### 인스턴스 생성 실패
1. 쿼터 사용량 확인 (Dashboard → Resource Quota)
2. 클러스터 노드 상태 확인 (Nodes 페이지)
3. 백엔드 로그 확인

---

## 관련 링크

- [README.md](./README.md) - 프로젝트 개요 및 설치 가이드
- [Ray Dashboard](http://100.117.45.28:8265) - Ray 클러스터 모니터링
- [API 문서](http://100.117.45.28:8000/docs) - OpenAPI/Swagger
