# 🌐 Hermes Domain Manager

> Multi-registrar domain management for Hermes Agent — monitor, manage DNS, and track expiries across Namecheap, GoDaddy, Cloudflare, and more.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Hermes Agent](https://img.shields.io/badge/Hermes-Agent-purple.svg)](https://github.com/NousResearch/hermes-agent)

[中文文档](README_CN.md)

---

## ✨ Features

- **Unified Interface** — Same commands for Namecheap, GoDaddy, Cloudflare
- **Domain Monitoring** — Expiry alerts with configurable thresholds
- **DNS Management** — List, add, update, delete DNS records
- **Renewal Pricing** — Check renewal costs before they hit
- **Account Balance** — Track registrar balances
- **Extensible** — Add new registrars by implementing `BaseProvider`
- **Hermes Native** — Designed for Hermes Agent with skill integration
- **Silent Cron Mode** — Only alerts when domains are expiring

## 📦 Installation

```bash
# Clone
git clone https://github.com/timwynter/hermes-domain-manager.git
cd hermes-domain-manager

# Install (editable)
pip install -e .

# Or use directly
PYTHONPATH=. python3 -m hermes_domain_manager.cli providers
```

## 🔑 Configuration

Set API credentials in `~/.hermes/.env`:

```bash
# Namecheap — requires IP whitelist
NAMECHEAP_API_KEY=your_api_key
NAMECHEAP_API_USER=your_api_user
NAMECHEAP_USERNAME=your_username

# GoDaddy — API Key + Secret
GODADDY_API_KEY=your_key
GODADDY_API_SECRET=your_secret

# Cloudflare — API Token (not Global Key)
CLOUDFLARE_API_TOKEN=your_token
```

**Namecheap IP Whitelist**: Go to Profile → Tools → API Access and add your public IP. Run `curl ifconfig.me` to find it.

## 🚀 Usage

### List All Domains

```bash
hermes-domain-manager list
hermes-domain-manager list --provider namecheap
```

### DNS Records

```bash
# List DNS
hermes-domain-manager dns monah.ai

# Add/Update record
hermes-domain-manager dns-set monah.ai A @ 1.2.3.4 --ttl 600

# Delete record
hermes-domain-manager dns-delete monah.ai A test
```

### Domain Expiry Monitor

```bash
# Check all registrars, warn within 30 days
hermes-domain-manager monitor --days 30

# JSON output (for scripts)
PYTHONPATH=. python3 -c "
from hermes_domain_manager.monitor import scan_json
from hermes_domain_manager.providers import list_providers
import json
print(json.dumps(scan_json(list_providers()), indent=2))
"
```

### Account & Pricing

```bash
hermes-domain-manager balance
hermes-domain-manager renew-price monah.ai
```

## 🤖 Hermes Agent Integration

Hermes Domain Manager includes a [SKILL.md](SKILL.md) for Hermes Agent. Install it:

```bash
hermes skills install https://raw.githubusercontent.com/timwynter/hermes-domain-manager/main/SKILL.md
```

Then ask Hermes: "check my domains", "add DNS record for monah.ai", "when does openfrunk.com expire?"

### Daily Cron Monitor

```bash
# Create silent daily check (alerts only when domains expiring)
hermes cron create "0 9 * * *" \
  --script ~/Projects/hermes-domain-manager/scripts/cron-check.py \
  --no-agent \
  --name "domain-expiry-check"
```

## 🏗️ Architecture

```
hermes_domain_manager/
├── providers/           # Registrar adapters
│   ├── base.py          # Abstract BaseProvider + DomainInfo/DnsRecord dataclasses
│   ├── namecheap.py     # Namecheap API (XML)
│   ├── godaddy.py       # GoDaddy API (JSON REST)
│   └── cloudflare.py    # Cloudflare API (JSON REST)
├── cli.py               # Unified CLI
├── monitor.py           # Expiry scan engine
└── __init__.py
```

### Adding a Provider

1. Create `hermes_domain_manager/providers/yourprovider.py`
2. Subclass `BaseProvider` and implement all `@abstractmethod`s
3. Register in `hermes_domain_manager/providers/__init__.py` → `BUILTIN` dict

```python
from .base import BaseProvider, DomainInfo, DnsRecord

class MyProvider(BaseProvider):
    name = "myregistrar"
    display_name = "My Registrar"

    def list_domains(self) -> list[DomainInfo]:
        ...
    def get_domain(self, domain: str) -> DomainInfo:
        ...
    def list_dns(self, domain: str) -> list[DnsRecord]:
        ...
    def set_dns(self, domain: str, record: DnsRecord) -> bool:
        ...
    def delete_dns(self, domain: str, record_type: str, host: str) -> bool:
        ...
```

## 🚨 Known Issues

| Issue | Workaround |
|-------|-----------|
| Namecheap IP changes (dynamic ISP) | Auto-detected; whitelist multiple IPs in Namecheap dashboard |
| Namecheap DNS replaces ALL records | Provider fetches existing records first, then merges |
| Cloudflare domains don't show expiry | Cloudflare is a DNS host, not a registrar — expiry is managed elsewhere |
| `winterjv.com` shows active but expired | GoDaddy grace period — domain may still be recoverable |

## 📄 License

MIT © 2026 Tim Wynter

## 🔗 Links

- [Hermes Agent](https://github.com/NousResearch/hermes-agent)
- [Namecheap API Docs](https://www.namecheap.com/support/api/intro/)
- [GoDaddy API Docs](https://developer.godaddy.com/)
- [Cloudflare API Docs](https://developers.cloudflare.com/api/)
