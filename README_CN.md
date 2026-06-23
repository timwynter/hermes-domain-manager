# 🌐 Domain Watch · 域名监控

> 为 Hermes Agent 设计的多注册商域名管理工具 — 跨 Namecheap、GoDaddy、Cloudflare 等平台监控、管理 DNS、追踪到期时间。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Hermes Agent](https://img.shields.io/badge/Hermes-Agent-purple.svg)](https://github.com/NousResearch/hermes-agent)

[English](README.md)

---

## ✨ 功能特性

- **统一接口** — Namecheap、GoDaddy、Cloudflare 使用相同命令
- **域名监控** — 可配置阈值的到期提醒
- **DNS 管理** — 增删改查 DNS 记录
- **续费价格** — 提前查看续费成本
- **账户余额** — 追踪注册商余额
- **可扩展** — 实现 `BaseProvider` 即可添加新注册商
- **Hermes 原生** — 为 Hermes Agent 设计，带 Skill 集成
- **静默定时模式** — 仅在域名即将到期时提醒

## 📦 安装

```bash
# 克隆
git clone https://github.com/timwynter/domain-watch.git
cd domain-watch

# 安装（可编辑模式）
pip install -e .

# 或直接使用
PYTHONPATH=. python3 -m domain_watch.cli providers
```

## 🔑 配置

在 `~/.hermes/.env` 中设置 API 凭证：

```bash
# Namecheap — 需要 IP 白名单
NAMECHEAP_API_KEY=你的密钥
NAMECHEAP_API_USER=你的API用户名
NAMECHEAP_USERNAME=你的用户名

# GoDaddy — API Key + Secret
GODADDY_API_KEY=你的密钥
GODADDY_API_SECRET=你的密钥

# Cloudflare — API Token（非 Global Key）
CLOUDFLARE_API_TOKEN=你的令牌
```

**Namecheap IP 白名单**：前往 Profile → Tools → API Access，添加你的公网 IP。运行 `curl ifconfig.me` 查看当前 IP。

## 🚀 使用方法

### 列出所有域名

```bash
domain-watch list
domain-watch list --provider namecheap
```

### DNS 记录

```bash
# 列出 DNS
domain-watch dns monah.ai

# 添加/更新记录
domain-watch dns-set monah.ai A @ 1.2.3.4 --ttl 600

# 删除记录
domain-watch dns-delete monah.ai A test
```

### 域名到期监控

```bash
# 检查所有注册商，30天内到期提醒
domain-watch monitor --days 30

# JSON 输出（用于脚本）
PYTHONPATH=. python3 -c "
from domain_watch.monitor import scan_json
from domain_watch.providers import list_providers
import json
print(json.dumps(scan_json(list_providers()), indent=2))
"
```

### 账户与价格

```bash
domain-watch balance
domain-watch renew-price monah.ai
```

## 🤖 Hermes Agent 集成

Domain Watch 包含 [SKILL.md](SKILL.md) 供 Hermes Agent 使用。安装方式：

```bash
hermes skills install https://raw.githubusercontent.com/timwynter/domain-watch/main/SKILL.md
```

然后对 Hermes 说："检查我的域名"、"给 monah.ai 添加 DNS 记录"、"openfrunk.com 什么时候到期？"

### 每日定时监控

```bash
# 创建静默每日检查（仅在域名到期时提醒）
hermes cron create "0 9 * * *" \
  --script ~/Projects/domain-watch/scripts/cron-check.py \
  --no-agent \
  --name "domain-expiry-check"
```

## 🏗️ 架构

```
domain_watch/
├── providers/           # 注册商适配器
│   ├── base.py          # 抽象基类 BaseProvider + DomainInfo/DnsRecord 数据类
│   ├── namecheap.py     # Namecheap API (XML)
│   ├── godaddy.py       # GoDaddy API (JSON REST)
│   └── cloudflare.py    # Cloudflare API (JSON REST)
├── cli.py               # 统一命令行
├── monitor.py           # 到期扫描引擎
└── __init__.py
```

### 添加新注册商

1. 创建 `domain_watch/providers/yourprovider.py`
2. 继承 `BaseProvider` 并实现所有 `@abstractmethod`
3. 在 `domain_watch/providers/__init__.py` 的 `BUILTIN` 字典中注册

```python
from .base import BaseProvider, DomainInfo, DnsRecord

class MyProvider(BaseProvider):
    name = "myregistrar"
    display_name = "我的注册商"

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

## 🚨 已知问题

| 问题 | 解决方案 |
|------|---------|
| Namecheap IP 变化（动态IP运营商） | 自动检测；在 Namecheap 后台添加多个 IP 白名单 |
| Namecheap DNS 会替换全部记录 | 代码会先获取现有记录再合并 |
| Cloudflare 域名不显示到期时间 | Cloudflare 是 DNS 托管商，非注册商 — 到期时间由原注册商管理 |
| `winterjv.com` 显示 active 但已过期 | GoDaddy 宽限期 — 域名可能仍可恢复 |

## 📄 许可证

MIT © 2026 Tim Wynter

## 🔗 相关链接

- [Hermes Agent](https://github.com/NousResearch/hermes-agent)
- [Namecheap API 文档](https://www.namecheap.com/support/api/intro/)
- [GoDaddy API 文档](https://developer.godaddy.com/)
- [Cloudflare API 文档](https://developers.cloudflare.com/api/)
