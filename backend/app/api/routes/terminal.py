# ============================================================================
# MCP Cloud Orchestrator - Terminal WebSocket Route
# ============================================================================
# 설명: WebSocket 기반 터미널 엔드포인트
# ============================================================================

import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from services.terminal_service import terminal_manager
from services.instance_manager import instance_manager

router = APIRouter(prefix="/ws", tags=["terminal"])


@router.websocket("/terminal/{instance_id}")
async def terminal_websocket(websocket: WebSocket, instance_id: str):
    """
    WebSocket 터미널 엔드포인트
    
    xterm.js 클라이언트와 Docker exec 프로세스를 브릿지합니다.
    
    Protocol:
    - Client -> Server: 터미널 입력 (raw bytes)
    - Server -> Client: 터미널 출력 (raw bytes)
    - 특수 메시지: {"type": "resize", "rows": N, "cols": N}
    """
    await websocket.accept()
    
    # 인스턴스 정보 조회
    instance = await instance_manager.get_instance(instance_id)
    if not instance:
        await websocket.close(code=4004, reason="Instance not found")
        return
    
    if not instance.container_id:
        await websocket.close(code=4005, reason="Container not running")
        return
    
    # 노드 정보 조회
    from services.node_manager import node_manager
    node = await node_manager.get_node(instance.node_id)
    if not node:
        await websocket.close(code=4006, reason="Node not found")
        return
    
    # 터미널 세션 생성
    session = await terminal_manager.create_session(
        session_id=instance_id,
        node_ip=node.tailscale_ip,
        container_id=instance.container_id
    )
    
    if not session:
        await websocket.close(code=4007, reason="Failed to create terminal session")
        return
    
    try:
        # 읽기 태스크: Docker -> WebSocket
        async def read_loop():
            while session.is_running:
                data = await session.read()
                if data:
                    await websocket.send_bytes(data)
                await asyncio.sleep(0.01)
        
        read_task = asyncio.create_task(read_loop())
        
        # 쓰기 루프: WebSocket -> Docker
        while True:
            try:
                data = await websocket.receive()
                
                if "bytes" in data:
                    await session.write(data["bytes"])
                elif "text" in data:
                    text = data["text"]
                    # JSON 메시지 처리 (resize 등)
                    if text.startswith("{"):
                        import json
                        try:
                            msg = json.loads(text)
                            if msg.get("type") == "resize":
                                await session.resize(
                                    rows=msg.get("rows", 24),
                                    cols=msg.get("cols", 80)
                                )
                        except json.JSONDecodeError:
                            pass
                    else:
                        await session.write(text.encode())
                        
            except WebSocketDisconnect:
                break
                
    finally:
        read_task.cancel()
        await terminal_manager.close_session(instance_id)


# Router export
terminal_router = router
