"""这个文件放公共 HTTP 小工具，主要解决本地 Python 证书链不完整的问题。"""

from __future__ import annotations

import ssl
from urllib.request import Request, urlopen


def open_url(request: Request, timeout: int = 30):
    """使用 certifi 证书包打开 HTTPS 地址，减少本地证书配置问题。"""

    return urlopen(request, timeout=timeout, context=build_ssl_context())


def build_ssl_context() -> ssl.SSLContext:
    """优先使用 certifi；如果没安装，就退回 Python 默认配置。"""

    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:  # noqa: BLE001 - 证书辅助失败时仍然使用默认 SSL 上下文。
        return ssl.create_default_context()
