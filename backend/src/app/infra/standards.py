"""Load the company standard pack from a YAML file (e.g. a Render Secret File).

顧客のパックは公開リポジトリに置かない。パスは REVIEW_STANDARD_PATH で渡す。
"""

from app.domain.standard import StandardPack


def load_pack(path: str) -> StandardPack:
    """Read and validate the pack at `path`. Raise `PackError` if missing or invalid."""
    raise NotImplementedError
