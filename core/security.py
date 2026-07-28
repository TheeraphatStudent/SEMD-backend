"""URL-safety validation (SSRF defense-in-depth).

Wired into `control/prediction_control.py::PredictionControl.predict()` as of
Domain 5 -- see `docs/backend/features/url-evaluation/README.md` for the
before/after accepted-input list and rationale. See
SEMD_BACKEND_CURRENT_STATE.md section 7.2 for the original finding (this
backend forwards user-submitted URLs to a Redis queue consumed by `semd-ml`
and to admin-configured third-party detectors, with zero validation).

This module classifies a URL as safe/unsafe; it does not fetch page content.
`check_url_safety()` is the pure lexical check (scheme, credentials, literal
IP host). `check_url_safety_async()` additionally resolves DNS for non-literal
hosts and checks every resolved address -- this is what actually closes the
DNS-rebinding gap (a hostname that only resolves to a private IP at lookup
time), and is what `PredictionControl` calls.
"""

from __future__ import annotations

import asyncio
import ipaddress
import re
import socket
from dataclasses import dataclass, field
from urllib.parse import urlsplit

from core.exceptions import ValidationError

ALLOWED_SCHEMES = frozenset({'http', 'https'})

# RFC 6598 (100.64.0.0/10, carrier-grade NAT) is included alongside the
# standard private/link-local/loopback ranges since it's routable inside many
# cloud VPCs and has been used in real SSRF-to-metadata-endpoint exploits.
_BLOCKED_HOSTNAME_LITERALS = frozenset({
    'localhost', 'localhost.localdomain', 'metadata.google.internal',
})

# Cloud metadata endpoints that aren't already covered by the private/
# link-local IP-range checks below (metadata.google.internal resolves to a
# link-local address, but is blocked by hostname too as defense-in-depth).
_BLOCKED_IP_LITERALS = frozenset({
    '169.254.169.254',  # AWS/GCP/Azure/OCI instance metadata
    'fd00:ec2::254',    # AWS IMDS, IPv6
})


@dataclass(frozen=True)
class UrlSafetyResult:
    is_safe: bool
    reason: str | None = None
    normalized_url: str | None = None
    errors: list[str] = field(default_factory=list)


def _is_blocked_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> tuple[bool, str | None]:
    if ip.is_loopback:
        return True, 'loopback address'
    if ip.is_link_local:
        return True, 'link-local address'
    if ip.is_private:
        return True, 'private network address'
    if ip.is_reserved:
        return True, 'reserved address'
    if ip.is_multicast:
        return True, 'multicast address'
    if isinstance(ip, ipaddress.IPv4Address) and ip in ipaddress.ip_network('100.64.0.0/10'):
        return True, 'carrier-grade NAT (RFC 6598) address'
    if str(ip) in _BLOCKED_IP_LITERALS:
        return True, 'cloud metadata endpoint'
    return False, None


def check_url_safety(raw_url: str) -> UrlSafetyResult:
    """Classify a user-submitted URL as safe or unsafe to hand to a downstream
    fetcher (semd-ml, a third-party detector). Does not resolve DNS -- hostname
    literals are checked for the common metadata/localhost aliases, and literal
    IP hosts are checked against private/reserved ranges. DNS-based rebinding
    (a hostname that resolves to a private IP only at fetch time) is NOT
    caught here and must be re-checked immediately before any actual fetch,
    by whichever service performs it.
    """
    if not raw_url or not isinstance(raw_url, str):
        return UrlSafetyResult(is_safe=False, reason='empty or non-string URL')

    try:
        parts = urlsplit(raw_url.strip())
    except ValueError as exc:
        return UrlSafetyResult(is_safe=False, reason=f'unparseable URL: {exc}')

    scheme = parts.scheme.lower()
    if scheme not in ALLOWED_SCHEMES:
        return UrlSafetyResult(is_safe=False, reason=f'unsupported scheme "{scheme or "(none)"}"')

    if parts.username or parts.password:
        return UrlSafetyResult(is_safe=False, reason='embedded credentials in URL are not allowed')

    hostname = parts.hostname
    if not hostname:
        return UrlSafetyResult(is_safe=False, reason='missing host')

    hostname = hostname.lower()

    if hostname in _BLOCKED_HOSTNAME_LITERALS:
        return UrlSafetyResult(is_safe=False, reason=f'blocked hostname "{hostname}"')

    # Reject percent-encoded or otherwise non-literal-looking hosts that
    # ipaddress can't parse but which some HTTP clients / DNS resolvers have
    # historically normalized into a routable address (e.g. decimal/octal/hex
    # IP encodings like "0x7f000001" or "017700000001" for 127.0.0.1).
    if re.fullmatch(r'0x[0-9a-f]+|0[0-7]+|\d+', hostname):
        return UrlSafetyResult(is_safe=False, reason='numeric-encoded host not allowed')

    try:
        ip = ipaddress.ip_address(hostname)
    except ValueError:
        ip = None

    if ip is not None:
        blocked, reason = _is_blocked_ip(ip)
        if blocked:
            return UrlSafetyResult(is_safe=False, reason=reason)

    return UrlSafetyResult(is_safe=True, normalized_url=raw_url.strip())


async def resolve_and_check_dns(hostname: str, timeout: float = 3.0) -> tuple[bool, str | None]:
    """Resolve `hostname` and check every returned address against the same
    blocklist as literal-IP hosts. Returns (blocked, reason). Treats a
    resolution failure (NXDOMAIN, timeout) as blocked -- a URL this backend
    can't resolve can't legitimately be evaluated downstream either, and
    silently letting it through just defers the failure to the ML queue or
    third-party detector with no safety benefit.
    """
    try:
        loop = asyncio.get_running_loop()
        infos = await asyncio.wait_for(
            loop.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        return True, f'DNS resolution of "{hostname}" timed out'
    except socket.gaierror as exc:
        return True, f'DNS resolution of "{hostname}" failed: {exc}'

    for family, _, _, _, sockaddr in infos:
        address = sockaddr[0]
        try:
            ip = ipaddress.ip_address(address)
        except ValueError:
            continue
        blocked, reason = _is_blocked_ip(ip)
        if blocked:
            return True, f'"{hostname}" resolves to {address} ({reason})'

    return False, None


async def check_url_safety_async(raw_url: str, *, dns_timeout: float = 3.0) -> UrlSafetyResult:
    """Full check used by control/prediction_control.py: lexical check first
    (cheap, catches scheme/credential/literal-IP issues without a network
    call), then DNS resolution + resolved-IP check for non-literal hosts.
    """
    lexical = check_url_safety(raw_url)
    if not lexical.is_safe:
        return lexical

    hostname = urlsplit(raw_url.strip()).hostname or ''
    try:
        ipaddress.ip_address(hostname)
        return lexical  # already a literal IP, already checked by check_url_safety
    except ValueError:
        pass

    blocked, reason = await resolve_and_check_dns(hostname, timeout=dns_timeout)
    if blocked:
        return UrlSafetyResult(is_safe=False, reason=reason)

    return lexical


async def reject_unsafe_urls(urls: list[str]) -> None:
    """Shared entry point for both URL-submission paths in this backend
    (`control/prediction_control.py`'s `/prediction/predict` and
    `services/ml_prediction_service.py`'s `/ml/predict*` -- two independent
    code paths that both accept user-supplied URLs and both need this check;
    see docs/backend/features/url-evaluation/README.md). Raises
    `core.exceptions.ValidationError` (422, code=UNSAFE_URL) listing every
    rejected URL and why, rather than silently dropping them.
    """
    results = await asyncio.gather(*(check_url_safety_async(url) for url in urls))
    errors = [
        {'url': url, 'reason': result.reason}
        for url, result in zip(urls, results)
        if not result.is_safe
    ]
    if errors:
        raise ValidationError(
            'One or more URLs failed safety validation',
            code='UNSAFE_URL',
            errors=errors,
        )
