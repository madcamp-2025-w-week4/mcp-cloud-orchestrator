# ============================================================================
# MCP Cloud Orchestrator - Docker Container Orchestrator
# ============================================================================
# 설명: 원격 노드에서 Docker 컨테이너 라이프사이클 관리
# ============================================================================

import asyncio
import subprocess
import socket
from typing import Optional
from fabric import Connection
from invoke import UnexpectedExit
import json


class DockerOrchestrator:
    """
    Docker 컨테이너 오케스트레이터
    
    Fabric/SSH를 통해 원격 노드에서 Docker 컨테이너를 
    배포, 중지, 삭제합니다.
    로컬 노드에서는 직접 subprocess로 실행합니다.
    """
    
    def __init__(self, ssh_user: str = "root"):
        """
        Args:
            ssh_user: SSH 접속 사용자 (기본: root)
        """
        self.ssh_user = ssh_user
        self._connections: dict[str, Connection] = {}
        self._local_ips = self._get_local_ips()
    
    def _get_local_ips(self) -> set[str]:
        """로컬 IP 목록을 가져옵니다."""
        local_ips = {"127.0.0.1", "localhost"}
        try:
            # 모든 로컬 IP 수집
            result = subprocess.run(
                ["hostname", "-I"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                local_ips.update(result.stdout.strip().split())
            # Tailscale IP 수집
            result = subprocess.run(
                ["tailscale", "ip", "-4"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                local_ips.add(result.stdout.strip())
        except Exception as e:
            print(f"Failed to get local IPs: {e}")
        return local_ips
    
    def _is_local(self, node_ip: str) -> bool:
        """주어진 IP가 로컬인지 확인합니다."""
        return node_ip in self._local_ips
    
    def _get_connection(self, node_ip: str) -> Connection:
        """노드에 대한 SSH 연결을 가져오거나 생성합니다."""
        if node_ip not in self._connections:
            self._connections[node_ip] = Connection(
                host=node_ip,
                user=self.ssh_user,
                connect_kwargs={"look_for_keys": True}
            )
        return self._connections[node_ip]
    
    async def _run_command(self, node_ip: str, cmd: str) -> tuple[bool, str]:
        """
        커맨드를 로컬 또는 원격에서 실행합니다.
        
        Returns:
            (성공 여부, 출력 또는 에러)
        """
        loop = asyncio.get_event_loop()
        
        if self._is_local(node_ip):
            # 로컬에서 직접 실행
            try:
                result = await loop.run_in_executor(
                    None,
                    lambda: subprocess.run(
                        cmd, shell=True, capture_output=True, text=True, timeout=60
                    )
                )
                if result.returncode == 0:
                    return True, result.stdout.strip()
                else:
                    return False, result.stderr.strip() or result.stdout.strip()
            except Exception as e:
                return False, str(e)
        else:
            # SSH로 원격 실행
            try:
                conn = self._get_connection(node_ip)
                result = await loop.run_in_executor(
                    None,
                    lambda: conn.run(cmd, hide=True)
                )
                return True, result.stdout.strip()
            except UnexpectedExit as e:
                return False, str(e)
            except Exception as e:
                return False, str(e)
    
    async def deploy_container(
        self,
        node_ip: str,
        image: str,
        port: int,
        container_name: str,
        cpu_limit: float = 1.0,
        memory_limit: str = "1g",
        env_vars: Optional[dict] = None,
        user_id: Optional[str] = None,
        instance_id: Optional[str] = None
    ) -> dict:
        """
        원격 노드에 Docker 컨테이너를 배포합니다.
        
        Args:
            node_ip: 대상 노드 IP
            image: Docker 이미지 (예: ubuntu:22.04, nginx:latest)
            port: 호스트 포트 (8000-9000)
            container_name: 컨테이너 이름
            cpu_limit: CPU 제한 (코어 수)
            memory_limit: 메모리 제한 (예: "1g", "512m")
            env_vars: 환경 변수 딕셔너리
            user_id: 사용자 ID (영구 볼륨용)
            instance_id: 인스턴스 ID (영구 볼륨용)
        
        Returns:
            배포 결과 딕셔너리 (container_id, status 등)
        """
        try:
            # 환경 변수 구성
            env_str = ""
            if env_vars:
                env_str = " ".join([f"-e {k}={v}" for k, v in env_vars.items()])
            
            # 영구 볼륨 마운트 설정
            volume_str = ""
            workspace_path = None
            if user_id and instance_id:
                workspace_path = f"/home/mroot/user_data/{user_id}/{instance_id}"
                # 워크스페이스 디렉토리 생성
                success, _ = await self._run_command(node_ip, f"mkdir -p {workspace_path}")
                if not success:
                    print(f"Warning: Failed to create workspace directory: {workspace_path}")
                volume_str = f"-v {workspace_path}:/workspace"
            
            # 노드의 실제 CPU 수 확인 및 제한
            actual_cpu = cpu_limit
            nproc_success, nproc_output = await self._run_command(node_ip, "nproc")
            if nproc_success and nproc_output.isdigit():
                max_cpus = int(nproc_output)
                if cpu_limit > max_cpus:
                    print(f"Warning: Requested {cpu_limit} CPUs but node has {max_cpus}. Limiting to {max_cpus}.")
                    actual_cpu = float(max_cpus)
            
            # Docker run 명령 구성
            # --network host: 호스트 네트워크 사용 (브리지 네트워크 문제 해결)
            # --init: PID 1 문제 해결
            # -t: 터미널 할당 (웹 터미널용)
            # sleep infinity: 컨테이너 유지
            cmd = (
                f"docker run -d "
                f"--name {container_name} "
                f"--network host "
                f"--cpus={actual_cpu} "
                f"--memory={memory_limit} "
                f"{volume_str} "
                f"{env_str} "
                f"--init "
                f"-t "
                f"{image} "
                f"sleep infinity"
            ).strip()
            
            # 명령 실행 (_run_command가 로컬/원격 구분)
            success, output = await self._run_command(node_ip, cmd)
            
            if success:
                container_id = output[:12] if output else "unknown"
                return {
                    "success": True,
                    "container_id": container_id,
                    "node_ip": node_ip,
                    "port": port,
                    "image": image,
                    "status": "running",
                    "workspace_path": workspace_path
                }
            else:
                return {
                    "success": False,
                    "error": output,
                    "node_ip": node_ip
                }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "node_ip": node_ip
            }
    
    async def stop_container(self, node_ip: str, container_id: str) -> dict:
        """
        컨테이너를 중지합니다.
        
        Args:
            node_ip: 노드 IP
            container_id: 컨테이너 ID 또는 이름
        
        Returns:
            작업 결과 딕셔너리
        """
        try:
            conn = self._get_connection(node_ip)
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: conn.run(f"docker stop {container_id}", hide=True)
            )
            
            return {"success": True, "container_id": container_id, "status": "stopped"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def start_container(self, node_ip: str, container_id: str) -> dict:
        """
        중지된 컨테이너를 시작합니다.
        
        Args:
            node_ip: 노드 IP
            container_id: 컨테이너 ID 또는 이름
        
        Returns:
            작업 결과 딕셔너리
        """
        try:
            conn = self._get_connection(node_ip)
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: conn.run(f"docker start {container_id}", hide=True)
            )
            
            return {"success": True, "container_id": container_id, "status": "running"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def remove_container(self, node_ip: str, container_id: str, force: bool = True) -> dict:
        """
        컨테이너를 삭제합니다.
        
        Args:
            node_ip: 노드 IP
            container_id: 컨테이너 ID 또는 이름
            force: 강제 삭제 여부
        
        Returns:
            작업 결과 딕셔너리
        """
        try:
            conn = self._get_connection(node_ip)
            
            force_flag = "-f" if force else ""
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: conn.run(f"docker rm {force_flag} {container_id}", hide=True)
            )
            
            return {"success": True, "container_id": container_id, "status": "removed"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_container_status(self, node_ip: str, container_id: str) -> dict:
        """
        컨테이너 상태를 조회합니다.
        
        Args:
            node_ip: 노드 IP
            container_id: 컨테이너 ID 또는 이름
        
        Returns:
            컨테이너 상태 딕셔너리
        """
        try:
            conn = self._get_connection(node_ip)
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: conn.run(
                    f"docker inspect --format='{{{{json .State}}}}' {container_id}",
                    hide=True
                )
            )
            
            state = json.loads(result.stdout.strip())
            
            return {
                "success": True,
                "container_id": container_id,
                "status": state.get("Status", "unknown"),
                "running": state.get("Running", False),
                "started_at": state.get("StartedAt"),
                "finished_at": state.get("FinishedAt"),
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def list_containers(self, node_ip: str) -> list[dict]:
        """
        노드의 모든 컨테이너를 조회합니다.
        
        Args:
            node_ip: 노드 IP
        
        Returns:
            컨테이너 목록
        """
        try:
            conn = self._get_connection(node_ip)
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: conn.run(
                    "docker ps -a --format='{{.ID}}|{{.Names}}|{{.Image}}|{{.Status}}|{{.Ports}}'",
                    hide=True
                )
            )
            
            containers = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    parts = line.split("|")
                    if len(parts) >= 4:
                        containers.append({
                            "id": parts[0],
                            "name": parts[1],
                            "image": parts[2],
                            "status": parts[3],
                            "ports": parts[4] if len(parts) > 4 else "",
                        })
            
            return containers
            
        except Exception as e:
            return []
    
    def close_all_connections(self):
        """모든 SSH 연결을 닫습니다."""
        for conn in self._connections.values():
            try:
                conn.close()
            except Exception:
                pass
        self._connections.clear()


# 싱글톤 인스턴스
docker_orchestrator = DockerOrchestrator()
