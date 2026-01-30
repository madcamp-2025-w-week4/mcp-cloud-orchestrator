# ============================================================================
# MCP Cloud Orchestrator - 커스텀 예외 모듈
# ============================================================================
# 설명: 애플리케이션 전용 예외 클래스 정의
# ============================================================================


class MCPOrchestratorException(Exception):
    """MCP Orchestrator 기본 예외 클래스"""
    
    def __init__(self, message: str, detail: str = None):
        self.message = message
        self.detail = detail
        super().__init__(self.message)


class NodeNotFoundException(MCPOrchestratorException):
    """노드를 찾을 수 없을 때 발생하는 예외"""
    
    def __init__(self, node_id: str):
        super().__init__(
            message=f"노드를 찾을 수 없습니다: {node_id}",
            detail=f"요청된 노드 ID '{node_id}'가 클러스터에 등록되어 있지 않습니다."
        )
        self.node_id = node_id


class NodeConnectionException(MCPOrchestratorException):
    """노드 연결 실패 시 발생하는 예외"""
    
    def __init__(self, node_id: str, ip_address: str, reason: str = None):
        super().__init__(
            message=f"노드 연결 실패: {node_id} ({ip_address})",
            detail=reason or "네트워크 연결을 확인하세요."
        )
        self.node_id = node_id
        self.ip_address = ip_address


class HealthCheckException(MCPOrchestratorException):
    """헬스체크 실패 시 발생하는 예외"""
    
    def __init__(self, node_id: str, reason: str = None):
        super().__init__(
            message=f"헬스체크 실패: {node_id}",
            detail=reason or "노드가 응답하지 않습니다."
        )
        self.node_id = node_id


class DataFileException(MCPOrchestratorException):
    """데이터 파일 처리 오류 시 발생하는 예외"""
    
    def __init__(self, file_path: str, operation: str, reason: str = None):
        super().__init__(
            message=f"데이터 파일 {operation} 오류: {file_path}",
            detail=reason or "파일 접근 권한을 확인하세요."
        )
        self.file_path = file_path
        self.operation = operation
