---
name: hermes-domain-manager
description: "Multi-registrar domain management: Namecheap, GoDaddy, Cloudflare. List domains, DNS CRUD, expiry monitoring, renewal pricing. (多注册商域名管理：Namecheap, GoDaddy, Cloudflare。域名列表、DNS管理、过期监控、续费价格。)"
version: 1.0.0
author: Tim Wynter
license: MIT
category: productivity
metadata:
  hermes:
    tags: [domain, dns, namecheap, godaddy, cloudflare, registrar, monitor]
    homepage: https://github.com/timwynter/hermes-domain-manager
  languages: [en, zh-CN]
---

# Hermes Domain Manager — Hermes 域名管家

Multi-registrar domain management for Hermes Agent. Supports Namecheap, GoDaddy, and Cloudflare with a unified interface. Extensible architecture — add new registrars by implementing `BaseProvider`.

为 Hermes Agent 设计的多注册商域名管理工具。支持 Namecheap、GoDaddy 和 Cloudflare，统一接口。可扩展架构 — 实现 `BaseProvider` 即可添加新注册商。

## Quick Start / 快速开始

```bash
# Install
cd ~/Projects/hermes-domain-manager && pip install -e .

# Or one-shot
PYTHONPATH=~/Projects/hermes-domain-manager python3 -m hermes_domain_manager.cli <command>
```

## Environment / 环境变量

Set in `~/.hermes/.env`:

```bash
# Namecheap
NAMECHEAP_API_KEY=your_api_key
NAMECHEAP_API_USER=your_api_user
NAMECHEAP_USERNAME=your_username

# GoDaddy
GODADDY_API_KEY=your_sso_key
GODADDY_API_SECRET=your_sso_secret

# Cloudflare
CLOUDFLARE_API_TOKEN=your_api_token
```

## Commands / 命令

### List all domains / 列出所有域名

```bash
PYTHONPATH=~/Projects/hermes-domain-manager python3 -m hermes_domain_manager.cli list
PYTHONPATH=~/Projects/hermes-domain-manager python3 -m hermes_domain_manager.cli list --provider namecheap
```

### DNS Records / DNS 记录

```bash
# List / 列出
PYTHONPATH=~/Projects/hermes-domain-manager python3 -m hermes_domain_manager.cli dns monah.ai

# Add/Update / 添加/更新
PYTHONPATH=~/Projects/hermes-domain-manager python3 -m hermes_domain_manager.cli dns-set monah.ai A @ 1.2.3.4 --ttl 600

# Delete / 删除
PYTHONPATH=~/Projects/hermes-domain-manager python3 -m hermes_domain_manager.cli dns-delete monah.ai A test
```

### Expiry Monitor / 过期监控

```bash
# Check all domains, warn within 30 days / 检查所有域名，30天内到期提醒
PYTHONPATH=~/Projects/hermes-domain-manager python3 -m hermes_domain_manager.cli monitor --days 30
```

### Other / 其他

```bash
PYTHONPATH=~/Projects/hermes-domain-manager python3 -m hermes_domain_manager.cli balance
PYTHONPATH=~/Projects/hermes-domain-manager python3 -m hermes_domain_manager.cli renew-price monah.ai
PYTHONPATH=~/Projects/hermes-domain-manager python3 -m hermes_domain_manager.cli providers
```

## Cron Monitoring / 定时监控

To set up daily domain expiry monitoring:

```bash
hermes cron create "0 9 * * *" \
  --prompt "Run domain expiry monitor: PYTHONPATH=~/Projects/hermes-domain-manager python3 -m hermes_domain_manager.cli monitor --days 30" \
  --name "domain-expiry-check"
```

Or as a `no_agent` script for silent daily reports (only alerts when domains are expiring):

```python
# ~/.hermes/scripts/hermes-domain-manager-cron.py
import sys, os
sys.path.insert(0, os.path.expanduser("~/Projects/hermes-domain-manager"))
from hermes_domain_manager.monitor import scan_all
from hermes_domain_manager.providers import list_providers

report = scan_all(list_providers(), warn_days=30)
# Only print if there are expiring domains (silent otherwise)
if "EXPIRING" in report or "expired" in report.lower():
    print(report)
```

## Adding a New Provider / 添加新注册商

1. Create `hermes_domain_manager/providers/yourprovider.py`
2. Implement `BaseProvider` abstract methods
3. Register in `hermes_domain_manager/providers/__init__.py`

Example template in `hermes_domain_manager/providers/base.py`.

1. 创建 `hermes_domain_manager/providers/yourprovider.py`
2. 实现 `BaseProvider` 抽象方法
3. 在 `hermes_domain_manager/providers/__init__.py` 注册

## Pitfalls / 注意事项

- ⚠️ **Namecheap IP whitelist**: Your public IP must be whitelisted in Namecheap API settings. The provider auto-detects the current IP. If your ISP uses dynamic IPs (like this user), you may need to whitelist multiple IPs.
- ⚠️ **Namecheap DNS**: The `dns-set` operation replaces ALL records — it fetches existing records first, then adds the new one. Be careful with bulk changes.
- ⚠️ **GoDaddy**: Uses `sso-key` auth header, not Bearer token. API key is called "API Key" in the dashboard.
- ⚠️ **Cloudflare**: Uses API Tokens (not Global API Key). Create at: My Profile → API Tokens → Create Token → Edit zone DNS.
- ⚠️ **Cloudflare**: Domain expiry is managed by the original registrar, not Cloudflare. The `expires` field will be None for Cloudflare-only domains.

## User's Current Setup / 当前配置

- Namecheap: 11 domains, whitelisted IPs: 87.232.98.28, 109.110.162.206
- GoDaddy: 2 active domains (timtsang.co, winterjv.com)
- Cloudflare: API token not yet configured

## Repository / 仓库

https://github.com/timwynter/hermes-domain-manager
