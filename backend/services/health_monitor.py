# ============================================================================
# MCP Cloud Orchestrator - 비동기 헬스 모니터링 서비스
# ============================================================================
# 설명: asyncio를 활용하여 17개 노드의 헬스를 동시에 체크하는 서비스
# ============================================================================

import asyncio
import time
from typing import Optional
from datetime import datetime

import httpx

from models.node import NodeInfo, NodeStatus, NodeHealth, NodeWithStatus
from models.cluster import ClusterStatus, ClusterSummary, ClusterHealth
from services.node_manager import node_manager
from core.config import settings


class HealthMonitor:
    """
    비동기 헬스 모니터링 서비스
    
    asyncio.gather를 사용하여 17개 이상의 노드를 동시에 헬스체크합니다.
    효율적인 네트워크 I/O를 위해 완전한 비동기 방식으로 구현되었습니다.
    """
    
    def __init__(self, timeout: float = None):
        """
        HealthMonitor 초기화
        
        Args:
            timeout: 헬스체크 타임아웃 (초, 기본값: 설정에서 로드)
        """
        self.timeout = timeout or settings.health_check_timeout
        self._http_client: Optional[httpx.AsyncClient] = None
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        """HTTP 클라이언트 인스턴스를 반환합니다 (재사용)."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                limits=httpx.Limits(max_connections=50, max_keepalive_connections=20)
            )
        return self._http_client
    
    async def close(self) -> None:
        """HTTP 클라이언트를 정리합니다."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
    
    async def check_node_health(self, node: NodeInfo) -> NodeStatus:
        """
        단일 노드의 헬스를 체크합니다.
        
        TCP 연결을 통해 노드의 응답 여부와 응답 시간을 측정합니다.
        
        Args:
            node: 체크할 노드 정보
            
        Returns:
            NodeStatus: 노드 상태 결과
        """
        start_time = time.perf_counter()
        
        try:
            # TCP 연결 시도 (기본 포트 22 - SSH)
            # 실제 환경에서는 각 노드에 헬스체크 엔드포인트가 있을 수 있음
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(node.tailscale_ip, 22),
                timeout=self.timeout
            )
            
            # 연결 성공
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            
            # 연결 종료
            writer.close()
            await writer.wait_closed()
            
            return NodeStatus(
                node_id=node.id,
                health=NodeHealth.HEALTHY,
                is_online=True,
                response_time_ms=round(elapsed_ms, 2),
                last_check_at=datetime.now(),
                error_message=None
            )
            
        except asyncio.TimeoutError:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return NodeStatus(
                node_id=node.id,
                health=NodeHealth.UNHEALTHY,
                is_online=False,
                response_time_ms=round(elapsed_ms, 2),
                last_check_at=datetime.now(),
                error_message="연결 시간 초과"
            )
            
        except ConnectionRefusedError:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            # 연결 거부는 노드가 온라인이지만 SSH가 비활성화된 경우
            return NodeStatus(
                node_id=node.id,
                health=NodeHealth.HEALTHY,  # 연결 거부는 노드가 살아있다는 의미
                is_online=True,
                response_time_ms=round(elapsed_ms, 2),
                last_check_at=datetime.now(),
                error_message="SSH 포트 연결 거부 (노드는 온라인)"
            )
            
        except OSError as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return NodeStatus(
                node_id=node.id,
                health=NodeHealth.UNHEALTHY,
                is_online=False,
                response_time_ms=round(elapsed_ms, 2),
                last_check_at=datetime.now(),
                error_message=f"네트워크 오류: {str(e)}"
            )
            
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return NodeStatus(
                node_id=node.id,
                health=NodeHealth.UNKNOWN,
                is_online=False,
                response_time_ms=round(elapsed_ms, 2),
                last_check_at=datetime.now(),
                error_message=f"알 수 없는 오류: {str(e)}"
            )
    
    async def check_all_nodes(self) -> list[NodeWithStatus]:
        """
        모든 노드의 헬스를 동시에 체크합니다.
        
        asyncio.gather를 사용하여 17개 노드를 병렬로 체크하므로
        전체 체크 시간이 크게 단축됩니다.
        
        Returns:
            list[NodeWithStatus]: 모든 노드의 정보와 상태
        """
        # 모든 노드 정보 로드
        nodes = await node_manager.get_all_nodes()
        
        if not nodes:
            return []
        
        # 모든 노드에 대해 동시에 헬스체크 실행
        health_checks = [self.check_node_health(node) for node in nodes]
        statuses = await asyncio.gather(*health_checks, return_exceptions=True)
        
        # 결과 조합
        results = []
        for node, status in zip(nodes, statuses):
            if isinstance(status, Exception):
                # 예외 발생 시 오류 상태로 처리
                status = NodeStatus(
                    node_id=node.id,
                    health=NodeHealth.UNKNOWN,
                    is_online=False,
                    last_check_at=datetime.now(),
                    error_message=f"헬스체크 실패: {str(status)}"
                )
            
            results.append(NodeWithStatus(info=node, status=status))
        
        return results
    
    async def get_cluster_status(self, include_nodes: bool = False) -> ClusterStatus:
        """
        클러스터 전체 상태를 반환합니다.
        
        Args:
            include_nodes: 개별 노드 상세 정보 포함 여부
            
        Returns:
            ClusterStatus: 클러스터 상태
        """
        # 모든 노드 헬스체크
        nodes_with_status = await self.check_all_nodes()
        
        # 통계 계산
        total = len(nodes_with_status)
        online = sum(1 for n in nodes_with_status if n.status.is_online)
        offline = total - online
        healthy = sum(1 for n in nodes_with_status if n.status.health == NodeHealth.HEALTHY)
        unhealthy = sum(1 for n in nodes_with_status if n.status.health == NodeHealth.UNHEALTHY)
        
        summary = ClusterSummary(
            total_nodes=total,
            online_nodes=online,
            offline_nodes=offline,
            healthy_nodes=healthy,
            unhealthy_nodes=unhealthy
        )
        
        # 클러스터 헬스 상태 결정
        cluster_health = ClusterStatus.calculate_health(summary)
        
        # 상태 메시지 생성
        if cluster_health == ClusterHealth.HEALTHY:
            message = "모든 노드가 정상 작동 중입니다."
        elif cluster_health == ClusterHealth.DEGRADED:
            message = f"일부 노드에 문제가 있습니다. ({unhealthy}개 비정상)"
        elif cluster_health == ClusterHealth.CRITICAL:
            message = f"다수의 노드가 오프라인입니다. ({offline}개 오프라인)"
        else:
            message = "클러스터에 연결된 노드가 없습니다."
        
        return ClusterStatus(
            cluster_name="mcp-cluster",
            health=cluster_health,
            summary=summary,
            checked_at=datetime.now(),
            nodes=nodes_with_status if include_nodes else None,
            message=message
        )


# 싱글톤 인스턴스
health_monitor = HealthMonitor()
