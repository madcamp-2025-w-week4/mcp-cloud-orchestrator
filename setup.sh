#!/bin/bash
# ============================================================================
# MCP Cloud Orchestrator - 개발 환경 설정 스크립트
# ============================================================================
# 설명: Python 가상환경 생성 및 필수 의존성 설치
# 작성: Senior Cloud Infrastructure Engineer
# ============================================================================

set -e  # 오류 발생 시 스크립트 중단

echo "=============================================="
echo "MCP Cloud Orchestrator 개발 환경 설정 시작"
echo "=============================================="

# 색상 정의 (터미널 출력용)
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # 색상 초기화

# 1단계: Python 가상환경 생성
echo -e "${YELLOW}[1/4] Python 가상환경 생성 중...${NC}"
if [ -d "venv" ]; then
    echo "기존 가상환경이 발견되었습니다. 삭제 후 재생성합니다."
    rm -rf venv
fi
python3 -m venv venv
echo -e "${GREEN}✓ 가상환경 생성 완료${NC}"

# 2단계: 가상환경 활성화
echo -e "${YELLOW}[2/4] 가상환경 활성화 중...${NC}"
source venv/bin/activate
echo -e "${GREEN}✓ 가상환경 활성화 완료${NC}"

# 3단계: pip 업그레이드
echo -e "${YELLOW}[3/4] pip 업그레이드 중...${NC}"
pip install --upgrade pip --quiet
echo -e "${GREEN}✓ pip 업그레이드 완료${NC}"

# 4단계: 필수 패키지 설치
echo -e "${YELLOW}[4/4] 필수 패키지 설치 중...${NC}"
pip install -r requirements.txt
echo -e "${GREEN}✓ 패키지 설치 완료${NC}"

echo ""
echo "=============================================="
echo -e "${GREEN}✓ 개발 환경 설정이 완료되었습니다!${NC}"
echo "=============================================="
echo ""
echo "다음 명령어로 서버를 시작하세요:"
echo "  source venv/bin/activate"
echo "  python main.py"
echo ""
echo "API 문서 확인:"
echo "  http://localhost:8000/docs"
echo "=============================================="
