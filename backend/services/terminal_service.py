# ============================================================================
# MCP Cloud Orchestrator - Terminal Service
# ============================================================================
# 설명: WebSocket을 통한 Docker exec 터미널 브릿지
# ============================================================================

import asyncio
import subprocess
from typing import Optional
from fabric import Connection


class TerminalSession:
    """
    Docker exec 세션 관리
    
    원격 노드에서 docker exec 프로세스를 관리하고
    stdin/stdout 스트림을 WebSocket으로 브릿지합니다.
    """
    
    def __init__(
        self,
        node_ip: str,
        container_id: str,
        ssh_user: str = "root"
    ):
        self.node_ip = node_ip
        self.container_id = container_id
        self.ssh_user = ssh_user
        self.process: Optional[asyncio.subprocess.Process] = None
        self._running = False
    
    async def start(self) -> bool:
        """
        터미널 세션을 시작합니다.
        SSH를 통해 원격 노드의 docker exec에 연결합니다.
        """
        try:
            # SSH를 통해 docker exec 실행
            cmd = [
                "ssh",
                "-tt",  # Force pseudo-terminal allocation
                "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=/dev/null",
                "-o", "LogLevel=ERROR",  # 경고 메시지 숨기기
                f"{self.ssh_user}@{self.node_ip}",
                f"docker exec -it {self.container_id} /bin/bash"
            ]
            
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            
            self._running = True
            return True
            
        except Exception as e:
            print(f"Failed to start terminal session: {e}")
            return False
    
    async def read(self) -> Optional[bytes]:
        """stdout에서 데이터를 읽습니다."""
        if not self.process or not self._running:
            return None
        
        try:
            data = await asyncio.wait_for(
                self.process.stdout.read(4096),
                timeout=0.1
            )
            return data if data else None
        except asyncio.TimeoutError:
            return None
        except Exception:
            return None
    
    async def write(self, data: bytes):
        """stdin에 데이터를 씁니다."""
        if not self.process or not self._running:
            return
        
        try:
            self.process.stdin.write(data)
            await self.process.stdin.drain()
        except Exception as e:
            print(f"Failed to write to terminal: {e}")
    
    async def resize(self, rows: int, cols: int):
        """터미널 크기를 조정합니다."""
        # SSH 터널에서는 resize가 자동 처리됨
        pass
    
    async def close(self):
        """터미널 세션을 종료합니다."""
        self._running = False
        if self.process:
            try:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=2.0)
            except Exception:
                self.process.kill()
    
    @property
    def is_running(self) -> bool:
        return self._running and self.process and self.process.returncode is None


class TerminalManager:
    """
    터미널 세션 매니저
    
    활성 터미널 세션들을 관리합니다.
    """
    
    def __init__(self):
        self._sessions: dict[str, TerminalSession] = {}
    
    async def create_session(
        self,
        session_id: str,
        node_ip: str,
        container_id: str
    ) -> Optional[TerminalSession]:
        """새 터미널 세션을 생성합니다."""
        # 기존 세션이 있으면 종료
        if session_id in self._sessions:
            await self._sessions[session_id].close()
        
        session = TerminalSession(node_ip, container_id)
        if await session.start():
            self._sessions[session_id] = session
            return session
        return None
    
    def get_session(self, session_id: str) -> Optional[TerminalSession]:
        """세션을 조회합니다."""
        return self._sessions.get(session_id)
    
    async def close_session(self, session_id: str):
        """세션을 종료합니다."""
        if session_id in self._sessions:
            await self._sessions[session_id].close()
            del self._sessions[session_id]
    
    async def close_all(self):
        """모든 세션을 종료합니다."""
        for session in self._sessions.values():
            await session.close()
        self._sessions.clear()


# 싱글톤 인스턴스
terminal_manager = TerminalManager()
