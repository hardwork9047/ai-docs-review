"""Modal で Ollama(gemma4:e2b)を GPU サーバとして公開する。

Colab + Cloudflare Quick Tunnel の代わりに使う。URL は固定、使われていない間は自動停止する。

初回だけ(モデルを Volume に保存):
    uvx modal run deploy/modal_ollama.py::pull

公開(URL が表示される。これを REVIEW_OLLAMA_URL に設定する):
    uvx modal deploy deploy/modal_ollama.py

エンドポイントは proxy auth 付き。呼び出し側は Modal ダッシュボードで作った Proxy Auth Token を
`Modal-Key` / `Modal-Secret` ヘッダーで送る(アプリでは REVIEW_OLLAMA_HEADERS に JSON で設定)。

費用の考え方:
- GPU は T4(Starter の無料枠 $30/月 で約 50 時間)。モデルは 5B / 4bit なので T4 で足りる
- max_containers=1: 同時アクセスでも GPU コンテナは 1 台だけ(Ollama が順番に処理する)
- scaledown_window: 最後のリクエストから 5 分で停止。次回はコールドスタート(数十秒)
- アプリの生存確認は /api/live を使い、Ollama を定期的に起こさない(render.yaml)
"""

import json
import subprocess
import time
import urllib.request

import modal

MODEL = "gemma4:e2b"
PORT = 11434
MODELS_DIR = "/models"

app = modal.App("buchou-review-ollama")

models = modal.Volume.from_name("buchou-review-ollama-models", create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("curl", "ca-certificates", "zstd")
    .run_commands("curl -fsSL https://ollama.com/install.sh | sh")
    .env(
        {
            "OLLAMA_HOST": f"0.0.0.0:{PORT}",
            "OLLAMA_MODELS": MODELS_DIR,
            # アプリの REVIEW_NUM_CTX と揃える(違うと初回にモデルを読み直して遅くなる)
            "OLLAMA_CONTEXT_LENGTH": "8192",
            # コンテナが生きている間はモデルを GPU に置いたままにする
            "OLLAMA_KEEP_ALIVE": "-1",
        }
    )
)


def _start_ollama() -> subprocess.Popen[bytes]:
    """Start `ollama serve` and wait until its HTTP API answers."""
    proc = subprocess.Popen(["ollama", "serve"])
    for _ in range(60):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/version", timeout=1)
            return proc
        except OSError:
            time.sleep(1)
    proc.terminate()
    raise RuntimeError("ollama serve did not start within 60 s")


@app.function(image=image, volumes={MODELS_DIR: models}, timeout=1800)
def pull() -> None:
    """Download MODEL into the Volume once (CPU only; no GPU cost)."""
    proc = _start_ollama()
    try:
        subprocess.run(["ollama", "pull", MODEL], check=True)
        models.commit()
    finally:
        proc.terminate()


@app.function(
    image=image,
    gpu="T4",
    volumes={MODELS_DIR: models},
    max_containers=1,
    scaledown_window=300,
    timeout=3600,
)
@modal.concurrent(max_inputs=8)
@modal.web_server(PORT, startup_timeout=180, requires_proxy_auth=True)
def ollama() -> None:
    """Serve the Ollama HTTP API; the model is pre-loaded before traffic is routed."""
    _start_ollama()
    # モデルを GPU に読み込んでおき、最初の採点リクエストを速くする
    # (prompt なしの /api/generate はモデルの読み込みだけを行う)
    request = urllib.request.Request(
        f"http://127.0.0.1:{PORT}/api/generate",
        data=json.dumps({"model": MODEL, "keep_alive": -1}).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(request, timeout=150).read()
    except OSError as exc:  # 読み込みに失敗しても、最初のリクエストで改めて読み込まれる
        print(f"preload failed: {exc}")
