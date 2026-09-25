"""Request-size guard for uploads, applied before the body is parsed.

FastAPI はエンドポイントを呼ぶ前に multipart 本文を全部受信(大きければ一時ファイルへ退避)する。
そのためハンドラ内のサイズ確認だけでは、認証の無い公開環境で巨大アップロードによる
メモリ・ディスク消費を防げない。ここで受信そのものを上限で打ち切る。
"""

from starlette.types import ASGIApp, Receive, Scope, Send


class UploadLimitMiddleware:
    """Reject requests to `paths` whose body exceeds `max_bytes` with HTTP 413.

    A declared `Content-Length` over the limit is rejected before any body is read.
    Bodies without a length (chunked) are counted as they arrive; once over the limit,
    reading stops and the response is replaced by 413.
    """

    def __init__(self, app: ASGIApp, *, max_bytes: int, paths: tuple[str, ...]) -> None:
        self.app = app
        self.max_bytes = max_bytes
        self.paths = paths

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """ASGI entry point."""
        raise NotImplementedError
