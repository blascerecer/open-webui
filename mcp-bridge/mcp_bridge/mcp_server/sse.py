import asyncio
from anyio import BrokenResourceError
from fastapi.responses import StreamingResponse
from .sse_transport import SseServerTransport
from fastapi import APIRouter, Request
from pydantic import ValidationError
from loguru import logger

from .server import server, options

router = APIRouter(prefix="/sse")

sse = SseServerTransport("/mcp-server/sse/messages")


@router.get("/", response_class=StreamingResponse)
async def handle_sse(request: Request):
    logger.info("new incoming SSE connection established")
    async with sse.connect_sse(request) as streams:
        try:
            await server.run(streams[0], streams[1], options)
        except BrokenResourceError:
            pass
        except asyncio.CancelledError:
            pass
        except ValidationError:
            pass
        except Exception:
            raise
    await request.close()


@router.post("/messages")
async def handle_messages(request: Request):
    logger.info("incoming SSE message received")
    await sse.handle_post_message(request.scope, request.receive, request._send)
    await request.close()
