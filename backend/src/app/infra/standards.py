"""Load the company standard pack from a YAML file (e.g. a Render Secret File).

顧客のパックは公開リポジトリに置かない。パスは REVIEW_STANDARD_PATH で渡す。
"""

from pathlib import Path

import yaml

from app.domain.standard import PackError, StandardPack, parse_pack


def load_pack(path: str) -> StandardPack:
    """Read and validate the pack at `path`. Raise `PackError` if missing or invalid."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise PackError(f"基準パックを読み込めません: {path}") from exc
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise PackError(f"基準パックの YAML が不正です: {exc}") from exc
    return parse_pack(data)
