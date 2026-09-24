"""Errors raised while loading an uploaded document (mapped to HTTP 400 by the API)."""


class DocumentError(Exception):
    """The upload is not a supported, readable .pptx or .pdf file."""
