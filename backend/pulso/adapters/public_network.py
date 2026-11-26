import ipaddress
import socket
from urllib.parse import urlsplit


def public_addresses(host):
    addresses = [result[4][0] for result in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)]
    if not addresses or any(not ipaddress.ip_address(address).is_global for address in addresses):
        raise ValueError("Endereço interno não permitido.")
    return addresses


def safe_public_url(value: str, *, media=False):
    url = urlsplit(value)
    suffixes = (
        "tiktok.com",
        "tiktokcdn.com",
        "tiktokcdn-us.com",
        "ttwstatic.com",  # Bootstrap assets requested by the public TikTok page.
        "byteoversea.com",
        "ibytedtos.com",
        "byteimg.com",
    )
    host = url.hostname or ""
    if (
        url.scheme != "https"
        or url.username
        or url.password
        or url.port not in {None, 443}
        or not any(host == suffix or host.endswith("." + suffix) for suffix in suffixes)
    ):
        raise ValueError("Destino externo não permitido.")
    public_addresses(host)
    return value
