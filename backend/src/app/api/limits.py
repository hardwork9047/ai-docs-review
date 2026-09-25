"""Request-size guard for uploads, applied before the body is parsed.

FastAPI はエンドポイントを呼ぶ前に multipart 本文を全部受信(大きければ一時ファイルへ退避)する。
そのためハンドラ内のサイズ確認だけでは、認証の無い公開環境で巨大アップロードによる
メモリ・ディスク消費を防げない。ここで受信そのものを上限で打ち切る。
"""

import json

from starlette.types import ASGIApp, Message, Receive, Scope, Send


class UploadLimitMiddleware:
    """Reject requests to `paths` whose body exceeds `max_bytes` with HTTP 413.

    A declared `Content-Length` over the limit is rejected before any body is read.
    Bodies without a length (chunked) are counted as they arrive; once over the limit,
    reading stops, the app sees a client disconnect, and the response becomes 413.
    """

    def __init__(self, app: ASGIApp, *, max_bytes: int, paths: tuple[str, ...]) -> None:
        self.app = app
        self.max_bytes = max_bytes
        self.paths = paths

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """ASGI entry point."""
        if scope["type"] != "http" or scope["path"] not in self.paths:
            await self.app(scope, receive, send)
            return

        declared = dict(scope["headers"]).get(b"content-length")
        if declared is not None and declared.isdigit() and int(declared) > self.max_bytes:
            await self._reject(send)
            return

        received = 0
        exceeded = False
        started = False

        async def limited_receive() -> Message:
            nonlocal received, exceeded
            if exceeded:
                return {"type": "http.disconnect"}
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    # 以降は読まない。アプリには切断として伝えて本文の処理を止め、
                    # 応答は guarded_send / 例外処理で 413 に差し替える
                    exceeded = True
                    return {"type": "http.disconnect"}
            return message

        async def guarded_send(message: Message) -> None:
            nonlocal started
            if exceeded:
                if not started:
                    started = True
                    await self._reject(send)
                return
            if message["type"] == "http.response.start":
                started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, guarded_send)
        except Exception:
            if not exceeded:
                raise
        if exceeded and not started:
            await self._reject(send)

    async def _reject(self, send: Send) -> None:
        mb = self.max_bytes / (1024 * 1024)
        body = json.dumps(
            {"detail": f"アップロードの上限({mb:.0f}MB)を超えています"}, ensure_ascii=False
        ).encode()
        await send(
            {
                "type": "http.response.start",
                "status": 413,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode()),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})
