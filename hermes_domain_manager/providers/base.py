"""Abstract base class for domain registrar providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class DomainInfo:
    """Normalized domain record across all providers."""
    name: str
    registrar: str
    expires: Optional[date] = None
    created: Optional[date] = None
    auto_renew: bool = False
    locked: bool = False
    privacy: bool = False
    nameservers: list = field(default_factory=list)
    status: str = ""
    raw: dict = field(default_factory=dict)

    @property
    def days_left(self) -> Optional[int]:
        if self.expires:
            return (self.expires - date.today()).days
        return None

    @property
    def is_expiring_soon(self, threshold: int = 30) -> bool:
        d = self.days_left
        return d is not None and d <= threshold

    @property
    def is_expired(self) -> bool:
        d = self.days_left
        return d is not None and d < 0


@dataclass
class DnsRecord:
    """Normalized DNS record."""
    type: str       # A, AAAA, CNAME, MX, TXT, NS, etc.
    host: str       # @ for root, or subdomain
    value: str      # IP, hostname, or text
    ttl: int = 600
    priority: Optional[int] = None  # For MX/SRV


class BaseProvider(ABC):
    """All domain registrars must implement this interface."""

    name: str = "base"
    display_name: str = "Base Provider"
    api_docs_url: str = ""

    def __init__(self, **credentials):
        self.creds = credentials

    # ── Domain CRUD ─────────────────────────────────────────

    @abstractmethod
    def list_domains(self) -> list[DomainInfo]:
        """Return all domains in the account."""
        ...

    @abstractmethod
    def get_domain(self, domain: str) -> DomainInfo:
        """Get details for a single domain."""
        ...

    # ── DNS ─────────────────────────────────────────────────

    @abstractmethod
    def list_dns(self, domain: str) -> list[DnsRecord]:
        """List DNS records for a domain."""
        ...

    @abstractmethod
    def set_dns(self, domain: str, record: DnsRecord) -> bool:
        """Add or update a DNS record."""
        ...

    @abstractmethod
    def delete_dns(self, domain: str, record_type: str, host: str) -> bool:
        """Delete a DNS record."""
        ...

    # ── Optional ────────────────────────────────────────────

    def get_renewal_price(self, domain: str) -> Optional[dict]:
        """Get renewal pricing. Optional — returns None if unsupported."""
        return None

    def get_account_balance(self) -> Optional[dict]:
        """Get account balance. Optional — returns None if unsupported."""
        return None

    def health_check(self) -> bool:
        """Quick connectivity check. Must not raise."""
        try:
            self.list_domains()
            return True
        except Exception:
            return False
