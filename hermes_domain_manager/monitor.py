"""Domain expiry monitor — scan all providers and generate reports."""

import sys
from datetime import date
from typing import Optional

from hermes_domain_manager.providers import get_provider, list_providers


def _emoji(days: Optional[int]) -> str:
    if days is None:
        return "❓"
    if days < 0:
        return "🔴"
    if days <= 7:
        return "🟠"
    if days <= 14:
        return "🟡"
    if days <= 30:
        return "🔵"
    return "🟢"


def scan_all(provider_names: list[str], warn_days: int = 30) -> str:
    """Scan all providers and return a formatted report."""
    today = date.today()
    lines = []
    lines.append("=" * 65)
    lines.append("  🌐 DOMAIN WATCH — Expiry Monitor")
    lines.append("=" * 65)
    
    all_domains = []
    errors = []
    
    for pname in provider_names:
        try:
            p = get_provider(pname)
            domains = p.list_domains()
            all_domains.extend(domains)
        except Exception as e:
            errors.append(f"  ❌ {pname}: {e}")
    
    if errors:
        lines.extend(errors)
        lines.append("")
    
    if not all_domains:
        lines.append("  No domains found in any configured provider.")
        return "\n".join(lines)
    
    # Sort by days_left (expiring first)
    all_domains.sort(key=lambda d: d.days_left if d.days_left is not None else 99999)
    
    # Summary
    expiring = [d for d in all_domains if d.days_left is not None and d.days_left <= warn_days]
    expired = [d for d in all_domains if d.is_expired]
    active = [d for d in all_domains if not d.is_expired]
    
    lines.append(f"  📊 {len(all_domains)} domains total | {len(active)} active | {len(expired)} expired | {len(expiring)} expiring within {warn_days}d")
    lines.append("")
    
    # Per-provider sections
    seen_registrars = {}
    for d in all_domains:
        seen_registrars.setdefault(d.registrar, []).append(d)
    
    for reg, domains in seen_registrars.items():
        lines.append(f"  ── {reg.upper()} ({len(domains)} domains) ──")
        for d in domains:
            days = d.days_left
            auto = "🔁" if d.auto_renew else "  "
            e = _emoji(days)
            d_str = f"{days}d" if days is not None else "?"
            exp_str = d.expires.isoformat() if d.expires else "?"
            lines.append(f"  {e} {auto} {d.name:30s} {exp_str:12s} ({d_str:>5s})")
        lines.append("")
    
    # Alerts section
    if expiring:
        lines.append("  " + "=" * 61)
        lines.append(f"  ⚠️  EXPIRING WITHIN {warn_days} DAYS")
        lines.append("  " + "=" * 61)
        for d in expiring:
            auto = "🔁 AUTO" if d.auto_renew else "⚠️  MANUAL"
            lines.append(f"  {auto}  {d.name:30s} — {d.expires} ({d.days_left}d)")
    else:
        lines.append(f"  ✅ No domains expiring within {warn_days} days.")
    
    lines.append("")
    lines.append(f"  📅 Report: {today.isoformat()}")
    lines.append("=" * 65)
    
    return "\n".join(lines)


def scan_json(provider_names: list[str]) -> list[dict]:
    """Scan all providers and return JSON-serializable list."""
    all_domains = []
    for pname in provider_names:
        try:
            p = get_provider(pname)
            for d in p.list_domains():
                all_domains.append({
                    "name": d.name,
                    "registrar": d.registrar,
                    "expires": d.expires.isoformat() if d.expires else None,
                    "days_left": d.days_left,
                    "auto_renew": d.auto_renew,
                    "locked": d.locked,
                    "privacy": d.privacy,
                    "status": d.status,
            })
        except Exception:
            pass
    all_domains.sort(key=lambda d: d["days_left"] if d["days_left"] is not None else 99999)
    return all_domains
