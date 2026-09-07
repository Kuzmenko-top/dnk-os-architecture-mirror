# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_lib_ssrf_guard"
# purpose: "High-security SSRF protection, URL allowlisting, private IP blocking, and upload limit validation"
# author: "DNK-e.com Maksym & Gerych"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# --- END DNK-MRH-HEADER ---

import socket
import ipaddress
from urllib.parse import urlparse
from typing import List, Set, Optional, Tuple

ALLOWED_DOMAINS: Set[str] = {
    "tiktok.com",
    "www.tiktok.com",
    "instagram.com",
    "www.instagram.com",
    "youtube.com",
    "www.youtube.com",
    "youtu.be",
    "telegram.org",
    "t.me",
    "cdn.shopify.com",
    "shopify.com",
}

PRIVATE_IP_RANGES: List[ipaddress.IPv4Network] = [
    ipaddress.IPv4Network("127.0.0.0/8"),      # localhost loopback
    ipaddress.IPv4Network("10.0.0.0/8"),       # RFC 1918 private
    ipaddress.IPv4Network("172.16.0.0/12"),    # RFC 1918 private
    ipaddress.IPv4Network("192.168.0.0/16"),   # RFC 1918 private
    ipaddress.IPv4Network("169.254.0.0/16"),   # link-local / cloud metadata (AWS/GCP/Azure)
    ipaddress.IPv4Network("0.0.0.0/8"),        # current network
    ipaddress.IPv4Network("100.64.0.0/10"),    # carrier-grade NAT
]


class SSRFGuard:
    """
    SSRF Protection Guard for URL Ingestion & External Resource Fetching.
    Protects against:
    - Direct IP navigation (127.0.0.1, 10.x, 192.168.x, 172.16-31.x, 169.254.x)
    - Decimal & Hex IP representations (e.g. 2130706433, 0x7f000001)
    - DNS Rebinding to private networks
    - Cloud metadata endpoint exfiltration (169.254.169.254)
    - Non-allowlisted external domain access
    """

    @staticmethod
    def _parse_ip_literal(host: str) -> Optional[ipaddress.IPv4Address | ipaddress.IPv6Address]:
        """Try parsing host as IPv4/IPv6 literal, integer decimal, or hexadecimal."""
        clean_host = host.strip("[]")
        # 1. Standard dotted-decimal IPv4 or colon IPv6
        try:
            return ipaddress.ip_address(clean_host)
        except ValueError:
            pass

        # 2. Integer or Hex encoded IP (e.g. 2130706433 or 0x7f000001)
        try:
            int_val = int(clean_host, 0)
            if 0 <= int_val <= 0xFFFFFFFF:
                return ipaddress.IPv4Address(int_val)
        except (ValueError, OverflowError):
            pass

        return None

    @staticmethod
    def _is_private_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
        """Check if IP falls within private, loopback, link-local, or reserved ranges."""
        if ip.is_loopback or ip.is_private or ip.is_reserved or ip.is_link_local:
            return True

        if isinstance(ip, ipaddress.IPv4Address):
            for private_range in PRIVATE_IP_RANGES:
                if ip in private_range:
                    return True

        if isinstance(ip, ipaddress.IPv6Address):
            if ip.is_site_local or ip.ipv4_mapped:
                return True

        return False

    @classmethod
    def is_allowed_url(cls, url: str) -> Tuple[bool, str]:
        """
        Validate URL against SSRF attacks.

        Returns:
            (is_allowed, error_message)
        """
        if not url or not isinstance(url, str):
            return False, "Empty or invalid URL"

        try:
            parsed = urlparse(url.strip())

            # Check scheme
            if parsed.scheme.lower() not in ["https", "http"]:
                return False, f"Invalid scheme: {parsed.scheme}"

            if not parsed.netloc:
                return False, "Missing netloc/host in URL"

            # Extract host without port or auth credentials
            netloc = parsed.netloc
            if "@" in netloc:
                netloc = netloc.split("@")[-1]

            domain = netloc.split(":")[0].strip().lower()
            if not domain:
                return False, "Missing domain in URL"

            # 1. Check if domain is an IP literal (dotted, decimal, or hex)
            ip_literal = cls._parse_ip_literal(domain)
            if ip_literal is not None:
                if cls._is_private_ip(ip_literal):
                    return False, f"Private IP detected: {ip_literal}"
                # Even if public IP, raw IP literals are not in allowed domains
                return False, f"Direct IP access not allowed: {ip_literal}"

            # 2. Check domain allowlist
            # Check exact match or valid root domain match (e.g. static.cdn.shopify.com)
            is_allowlisted = False
            for allowed in ALLOWED_DOMAINS:
                if domain == allowed or domain.endswith("." + allowed):
                    is_allowlisted = True
                    break

            if not is_allowlisted:
                return False, f"Domain {domain} not in allowlist"

            # 3. Resolve DNS to detect DNS rebinding or internal CNAME/A records
            try:
                ip_addresses = socket.getaddrinfo(domain, None)
            except socket.gaierror as e:
                return False, f"DNS resolution failed for {domain}: {str(e)}"

            if not ip_addresses:
                return False, f"No IP addresses resolved for domain {domain}"

            for family, _, _, _, sockaddr in ip_addresses:
                ip_str = sockaddr[0]

                try:
                    ip = ipaddress.ip_address(ip_str)
                    if cls._is_private_ip(ip):
                        return False, f"Private IP detected via DNS: {ip}"
                except ValueError:
                    return False, f"Invalid IP returned by DNS: {ip_str}"

            return True, "OK"

        except Exception as e:
            return False, f"Validation error: {str(e)}"

    @staticmethod
    def validate_upload_limits(
        content_length: Optional[int],
        duration: Optional[float],
    ) -> Tuple[bool, str]:
        """
        Validate upload limits.

        - Max payload: 150MB
        - Max duration: 600s (10 min)
        - Network timeout: 15s
        """
        MAX_PAYLOAD_SIZE = 150 * 1024 * 1024  # 150MB
        MAX_DURATION = 600.0  # 10 min
        NETWORK_TIMEOUT = 15.0  # 15s

        if content_length is not None and content_length > MAX_PAYLOAD_SIZE:
            return False, f"Payload too large: {content_length} > {MAX_PAYLOAD_SIZE}"

        if duration is not None and duration > MAX_DURATION:
            return False, f"Duration too long: {duration}s > {MAX_DURATION}s"

        return True, "OK"
