# ============================================================================
# MCP Cloud Orchestrator - Ray Cluster Service
# ============================================================================
# 설명: Ray SDK를 통한 클러스터 모니터링 및 리소스 관리
# ============================================================================

import ray
from typing import Optional
from datetime import datetime


class RayService:
    """
    Ray 클러스터 관리 서비스
    
    Ray SDK를 사용하여 클러스터 노드 상태, 리소스 사용량을 
    실시간으로 모니터링합니다.
    
    Ray 클러스터가 재시작되면 자동으로 재연결을 시도합니다.
    """
    
    def __init__(self, head_node_address: str = "auto"):
        """
        Ray 클러스터에 연결합니다.
        
        Args:
            head_node_address: Ray Head Node 주소 (기본: auto - 로컬 클러스터 자동 감지)
        """
        self.head_node_address = head_node_address
        self._initialized = False
    
    def _reconnect(self) -> bool:
        """Ray 클러스터에 재연결"""
        try:
            # 기존 연결 정리
            if ray.is_initialized():
                ray.shutdown()
            self._initialized = False
            
            # 재연결
            ray.init(
                address=self.head_node_address,
                ignore_reinit_error=True,
                logging_level="warning"
            )
            self._initialized = True
            print(f"Ray reconnected: {ray.cluster_resources()}")
            return True
        except Exception as e:
            print(f"Ray reconnection failed: {e}")
            self._initialized = False
            return False
    
    def _ensure_connected(self) -> bool:
        """Ray 클러스터 연결 확인 및 초기화"""
        # 이미 연결되어 있으면 True
        try:
            if ray.is_initialized():
                # 연결 상태 확인 (빠른 체크)
                ray.cluster_resources()
                self._initialized = True
                return True
        except Exception:
            # 연결이 끊어졌으면 재연결 시도
            print("Ray connection lost, attempting to reconnect...")
            return self._reconnect()
            
        # 초기화 안됐으면 연결 시도
        if not self._initialized:
            try:
                ray.init(
                    address=self.head_node_address,
                    ignore_reinit_error=True,
                    logging_level="warning"
                )
                self._initialized = True
                print(f"Ray connected: {ray.cluster_resources()}")
            except Exception as e:
                print(f"Ray connection failed: {e}")
                return False
        return ray.is_initialized()
    
    def get_nodes(self) -> list[dict]:
        """
        ray.nodes()를 사용하여 모든 노드 정보를 조회합니다.
        
        Returns:
            노드 정보 리스트 (NodeID, IP, CPU, Memory, GPU 등)
        """
        if not self._ensure_connected():
            return []
        
        try:
            nodes = ray.nodes()
            result = []
            
            for node in nodes:
                result.append({
                    "node_id": node.get("NodeID", ""),
                    "node_name": node.get("NodeName", ""),
                    "node_ip": node.get("NodeManagerAddress", "").split(":")[0] if node.get("NodeManagerAddress") else "",
                    "is_alive": node.get("Alive", False),
                    "resources": node.get("Resources", {}),
                    "resources_total": node.get("Resources", {}),
                    "labels": node.get("Labels", {}),
                })
            
            return result
        except Exception as e:
            print(f"Failed to get nodes: {e}")
            return []
    
    def get_cluster_resources(self) -> dict:
        """
        클러스터 전체 리소스 현황을 조회합니다.
        
        Returns:
            전체 리소스 (CPU, Memory, GPU 등)
        """
        if not self._ensure_connected():
            return {}
        
        try:
            resources = ray.cluster_resources()
            return {
                "cpu": resources.get("CPU", 0),
                "memory": resources.get("memory", 0) / (1024**3),  # bytes to GB
                "gpu": resources.get("GPU", 0),
                "object_store_memory": resources.get("object_store_memory", 0) / (1024**3),
            }
        except Exception as e:
            print(f"Failed to get cluster resources: {e}")
            return {}
    
    def get_available_resources(self) -> dict:
        """
        현재 사용 가능한 리소스를 조회합니다.
        
        Returns:
            사용 가능한 리소스 (CPU, Memory, GPU 등)
        """
        if not self._ensure_connected():
            return {}
        
        try:
            resources = ray.available_resources()
            return {
                "cpu": resources.get("CPU", 0),
                "memory": resources.get("memory", 0) / (1024**3),  # bytes to GB
                "gpu": resources.get("GPU", 0),
                "object_store_memory": resources.get("object_store_memory", 0) / (1024**3),
            }
        except Exception as e:
            print(f"Failed to get available resources: {e}")
            return {}
    
    def get_cluster_status(self) -> dict:
        """
        클러스터 전체 상태 요약을 반환합니다.
        
        Returns:
            클러스터 상태 요약 딕셔너리
        """
        nodes = self.get_nodes()
        total_resources = self.get_cluster_resources()
        available_resources = self.get_available_resources()
        
        alive_nodes = [n for n in nodes if n.get("is_alive", False)]
        
        # 리소스 사용량 계산
        used_cpu = total_resources.get("cpu", 0) - available_resources.get("cpu", 0)
        used_memory = total_resources.get("memory", 0) - available_resources.get("memory", 0)
        used_gpu = total_resources.get("gpu", 0) - available_resources.get("gpu", 0)
        
        return {
            "nodes": {
                "total": len(nodes),
                "alive": len(alive_nodes),
                "dead": len(nodes) - len(alive_nodes),
            },
            "resources": {
                "total": total_resources,
                "available": available_resources,
                "used": {
                    "cpu": used_cpu,
                    "memory": used_memory,
                    "gpu": used_gpu,
                }
            },
            "usage_percent": {
                "cpu": (used_cpu / total_resources.get("cpu", 1)) * 100 if total_resources.get("cpu", 0) > 0 else 0,
                "memory": (used_memory / total_resources.get("memory", 1)) * 100 if total_resources.get("memory", 0) > 0 else 0,
                "gpu": (used_gpu / total_resources.get("gpu", 1)) * 100 if total_resources.get("gpu", 0) > 0 else 0,
            },
            "is_connected": self._initialized and ray.is_initialized(),
            "head_node": self.head_node_address,
            "timestamp": datetime.now().isoformat(),
        }
    
    def find_least_loaded_node(self) -> Optional[dict]:
        """
        가장 여유있는 노드를 찾습니다.
        
        Returns:
            가장 여유있는 노드 정보 또는 None
        """
        nodes = self.get_nodes()
        alive_nodes = [n for n in nodes if n.get("is_alive", False)]
        
        if not alive_nodes:
            return None
        
        # 사용 가능한 CPU 기준으로 정렬
        def get_available_cpu(node):
            resources = node.get("resources", {})
            return resources.get("CPU", 0)
        
        sorted_nodes = sorted(alive_nodes, key=get_available_cpu, reverse=True)
        return sorted_nodes[0] if sorted_nodes else None
    
    def get_nodes_with_available_resources(self) -> list[dict]:
        """
        각 노드별 사용 가능한 리소스를 조회합니다.
        ray.available_resources()는 클러스터 전체만 반환하므로,
        ray.nodes()의 Resources와 클러스터 사용량을 비교합니다.
        
        Returns:
            노드별 가용 리소스 리스트
        """
        if not self._ensure_connected():
            return []
        
        try:
            nodes = ray.nodes()
            cluster_available = ray.available_resources()
            
            result = []
            for node in nodes:
                if not node.get("Alive", False):
                    continue
                
                # 노드의 총 리소스
                resources = node.get("Resources", {})
                node_ip = node.get("NodeManagerAddress", "").split(":")[0]
                
                # 해당 노드의 가용 리소스 계산
                # Ray는 노드별 available을 직접 제공하지 않으므로
                # 노드의 총 리소스를 사용 (보수적 추정)
                # 실제 가용량은 클러스터 전체 가용량을 참조
                cpu_total = resources.get("CPU", 0)
                memory_total = resources.get("memory", 0) / (1024**3)  # GB
                
                result.append({
                    "node_id": node.get("NodeID", ""),
                    "node_ip": node_ip,
                    "cpu_total": cpu_total,
                    "memory_total_gb": memory_total,
                    # 현재는 총 리소스를 가용으로 표시 (인스턴스 추적 별도 필요)
                    "cpu_available": cpu_total,
                    "memory_available_gb": memory_total,
                })
            
            return result
        except Exception as e:
            print(f"Failed to get nodes with resources: {e}")
            return []
    
    def find_node_with_capacity(self, required_cpu: float, required_memory_gb: float) -> Optional[dict]:
        """
        요청한 리소스를 제공할 수 있는 노드를 찾습니다.
        
        Args:
            required_cpu: 필요한 CPU 코어 수
            required_memory_gb: 필요한 메모리 (GB)
            
        Returns:
            조건을 만족하는 노드 정보 또는 None
        """
        nodes = self.get_nodes_with_available_resources()
        
        # 요청 리소스를 제공할 수 있는 노드 필터링
        capable_nodes = [
            n for n in nodes
            if n.get("cpu_available", 0) >= required_cpu
            and n.get("memory_available_gb", 0) >= required_memory_gb
        ]
        
        if not capable_nodes:
            return None
        
        # 가장 여유있는 노드 선택 (CPU 기준)
        sorted_nodes = sorted(
            capable_nodes,
            key=lambda n: n.get("cpu_available", 0),
            reverse=True
        )
        return sorted_nodes[0]
    
    def get_max_available_capacity(self) -> dict:
        """
        클러스터에서 단일 노드가 제공할 수 있는 최대 리소스를 반환합니다.
        UI에서 선택 가능한 옵션을 제한하는 데 사용됩니다.
        
        Returns:
            {"max_cpu": int, "max_memory_gb": int}
        """
        nodes = self.get_nodes_with_available_resources()
        
        if not nodes:
            return {"max_cpu": 0, "max_memory_gb": 0}
        
        max_cpu = max(n.get("cpu_available", 0) for n in nodes)
        max_memory = max(n.get("memory_available_gb", 0) for n in nodes)
        
        return {
            "max_cpu": int(max_cpu),
            "max_memory_gb": int(max_memory),
        }
    
    def disconnect(self):
        """Ray 연결 종료"""
        if self._initialized:
            try:
                ray.shutdown()
                self._initialized = False
            except Exception:
                pass


# 싱글톤 인스턴스
ray_service = RayService()

