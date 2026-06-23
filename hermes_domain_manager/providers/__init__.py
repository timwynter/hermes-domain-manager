"""Provider registry — discover and instantiate providers."""

from .base import BaseProvider
from .namecheap import NamecheapProvider
from .godaddy import GoDaddyProvider
from .cloudflare import CloudflareProvider

# All built-in providers
BUILTIN: dict[str, type[BaseProvider]] = {
    "namecheap": NamecheapProvider,
    "godaddy": GoDaddyProvider,
    "cloudflare": CloudflareProvider,
}


def get_provider(name: str, **credentials) -> BaseProvider:
    """Instantiate a provider by name."""
    cls = BUILTIN.get(name.lower())
    if cls is None:
        raise ValueError(
            f"Unknown provider: {name}. Available: {list(BUILTIN.keys())}"
        )
    return cls(**credentials)


def list_providers() -> list[str]:
    """Return available provider names."""
    return list(BUILTIN.keys())
