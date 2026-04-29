import os
import httpx
import asyncio
import websockets
import logging
from typing import Callable
from sqlalchemy.orm import Session
from fastapi import APIRouter, Request, WebSocket, Depends, Query, WebSocketDisconnect
from fastapi.responses import JSONResponse, Response
from providence_data import BrowserDataService
from .deps import get_session_factory

logger = logging.getLogger("proxy")

router = APIRouter()

def _rewrite_cdp_host_references(content: bytes, replaced: str, target: str) -> bytes:
    return content.replace(replaced.encode(), target.encode())

# def _public_origin_bytes(request: Request) -> bytes:
#     forwarded_host = request.headers.get("x-forwarded-host")
#     if forwarded_host:
#         scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
#         return f"{scheme}://{forwarded_host}".encode()
#     return f"{request.url.scheme}://{request.url.netloc}".encode()

@router.api_route("/browser/{path:path}", methods=["GET", "POST"])
def proxy_http(
    request: Request,
    path: str,
    browser_id: str = Query(...),
    session_factory: Callable[[], Session] = Depends(get_session_factory),
) -> Response:
    session = session_factory()
    browser_data_service = BrowserDataService()

    browser = browser_data_service.get_browser_by_id(session, browser_id)

    if browser is None:
        return JSONResponse(status_code=404, content={"detail": "Browser not found"})
    
    if browser.browser_job is None:
        return JSONResponse(status_code=404, content={"detail": "Browser job not found"})

    browser_job = browser.browser_job
    status = browser_job.status
    if status != "running":
        return JSONResponse(status_code=404, content={"detail": "Browser job not running"})

    job_name = browser_job.meta.get("job_name", None)
    namespace = browser_job.meta.get("namespace", None)

    service = f"{job_name}.{namespace}.svc.cluster.local:8002"
    proxy_service = os.getenv("EDGE_PROXY_ENDPOINT")
    endpoint = f"http://{service}"
    url = f"{endpoint}/{path}" if path else f"{endpoint}/"

    try:
        with httpx.Client() as client:
            rp_resp = client.request(
                method=request.method,
                url=url,
                # params=request.query_params,
                headers={
                    k: v
                    for k, v in request.headers.items()
                    if k.lower() != "host"
                },
            )
    except httpx.RequestError as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Failed to connect CDP ({endpoint}): {e!s}"},
        )
    content = _rewrite_cdp_host_references(rp_resp.content, service, proxy_service)
    return Response(content=content, status_code=rp_resp.status_code)


@router.websocket("/devtools/{path:path}")
async def proxy_ws(
    websocket: WebSocket,
    path: str,
    browser_id: str,
) -> None:
    await websocket.accept()

    session_factory = websocket.app.state.session_factory

    session = session_factory()
    browser_data_service = BrowserDataService()

    browser = await asyncio.to_thread(browser_data_service.get_browser_by_id, session, browser_id)
    session.close()

    if browser is None:
        await websocket.close(code=1008, reason="Browser not found")
        return
    if browser.browser_job is None:
        await websocket.close(code=1008, reason="Browser job not found")
        return
    
    browser_job = browser.browser_job
    status = browser_job.status
    if status != "running":
        await websocket.close(code=1008, reason="Browser job not running")
        session.close()
        return

    job_name = browser_job.meta.get("job_name", None)
    namespace = browser_job.meta.get("namespace", None)

    target_url = f"ws://{job_name}.{namespace}.svc.cluster.local:8002/devtools/{path}"
    # target_url = f"ws://192.168.5.192:30080/devtools/{path}"

    async with websockets.connect(target_url) as target_ws:
        async def forward_to_chrome() -> None:
            async for message in websocket.iter_text():
                await target_ws.send(message)

        async def forward_to_client() -> None:
            async for message in target_ws:
                await websocket.send_text(message)

        await asyncio.gather(forward_to_chrome(), forward_to_client())

@router.websocket("/websockify")
async def proxy_vnc_ws(
    websocket: WebSocket,
    browser_id: str,
) -> None:
    await websocket.accept()

    session_factory = websocket.app.state.session_factory

    session = session_factory()
    browser_data_service = BrowserDataService()

    browser = await asyncio.to_thread(browser_data_service.get_browser_by_id, session, browser_id)
    session.close()

    if browser is None:
        await websocket.close(code=1008, reason="Browser not found")
        return
    if browser.browser_job is None:
        await websocket.close(code=1008, reason="Browser job not found")
        return

    browser_job = browser.browser_job
    status = browser_job.status
    if status != "running":
        await websocket.close(code=1008, reason="Browser job not running")
        session.close()
        return

    job_name = browser_job.meta.get("job_name", None)
    namespace = browser_job.meta.get("namespace", None)

    target_url = f"ws://{job_name}.{namespace}.svc.cluster.local:6080/websockify"
    # target_url = f"ws://192.168.5.192:31010/websockify"

    async with websockets.connect(target_url) as target_ws:
        async def client_to_upstream() -> None:
            try:
                while True:
                    msg = await websocket.receive()
                    if msg["type"] == "websocket.disconnect":
                        break
                    if msg["type"] != "websocket.receive":
                        continue    
                    if "bytes" in msg and msg.get("bytes") is not None:
                        await target_ws.send(msg["bytes"])
                    elif "text" in msg and msg.get("text") is not None:
                        await target_ws.send(msg["text"])
            except WebSocketDisconnect:
                pass

        async def upstream_to_client() -> None:
            async for message in target_ws:
                if isinstance(message, bytes):
                    await websocket.send_bytes(message)
                else:
                    await websocket.send_text(message)

        client_task = asyncio.create_task(client_to_upstream())
        upstream_task = asyncio.create_task(upstream_to_client())
        try:
            _, pending = await asyncio.wait(
                (client_task, upstream_task),
                return_when=asyncio.FIRST_COMPLETED,
            )
            for t in pending:
                t.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
        finally:
            for t in (client_task, upstream_task):
                if not t.done():
                    t.cancel()
