#!/usr/bin/env python3
"""Domain Watch — unified CLI for multi-registrar domain management.

Usage:
  domain-watch list [--provider namecheap|godaddy|cloudflare|all]
  domain-watch dns <domain> [--provider auto]
  domain-watch dns-set <domain> <type> <host> <value> [--ttl 600] [--provider auto]
  domain-watch dns-delete <domain> <type> <host> [--provider auto]
  domain-watch monitor [--days 30]
  domain-watch balance [--provider all]
  domain-watch renew-price <domain> [--provider auto]
  domain-watch providers

Environment:
  NAMECHEAP_API_KEY, NAMECHEAP_API_USER, NAMECHEAP_USERNAME
  GODADDY_API_KEY, GODADDY_API_SECRET
  CLOUDFLARE_API_TOKEN
"""

import argparse
import json
import os
import sys
from datetime import date

from domain_watch.providers import get_provider, list_providers, BUILTIN
from domain_watch.monitor import scan_all


def _load_creds():
    """Load credentials from environment."""
    return {}


def _detect_provider(domain: str) -> str:
    """Heuristic: try each provider, return first that finds the domain."""
    for name in ["namecheap", "godaddy", "cloudflare"]:
        try:
            p = get_provider(name)
            p.get_domain(domain)
            return name
        except Exception:
            continue
    raise ValueError(f"Cannot find domain '{domain}' in any configured provider")


def cmd_list(args):
    providers = args.provider.split(",") if args.provider != "all" else list_providers()
    all_domains = []
    for pname in providers:
        try:
            p = get_provider(pname)
            domains = p.list_domains()
            for d in domains:
                days = d.days_left
                all_domains.append({
                    "name": d.name,
                    "registrar": d.registrar,
                    "expires": d.expires.isoformat() if d.expires else None,
                    "days_left": days,
                    "auto_renew": d.auto_renew,
                    "status": d.status or ("active" if days and days >= 0 else "expired"),
                })
        except Exception as e:
            print(f"⚠️  {pname}: {e}", file=sys.stderr)
    
    print(json.dumps(all_domains, indent=2, ensure_ascii=False))
    return all_domains


def cmd_dns(args):
    provider = args.provider if args.provider != "auto" else _detect_provider(args.domain)
    p = get_provider(provider)
    records = p.list_dns(args.domain)
    result = []
    for r in records:
        result.append({"type": r.type, "host": r.host, "value": r.value, "ttl": r.ttl, "priority": r.priority})
    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_dns_set(args):
    from domain_watch.providers.base import DnsRecord
    provider = args.provider if args.provider != "auto" else _detect_provider(args.domain)
    p = get_provider(provider)
    record = DnsRecord(type=args.type, host=args.host, value=args.value, ttl=args.ttl)
    ok = p.set_dns(args.domain, record)
    print(json.dumps({"status": "ok" if ok else "failed", "domain": args.domain, "record": f"{args.host} {args.type} {args.value}"}))


def cmd_dns_delete(args):
    provider = args.provider if args.provider != "auto" else _detect_provider(args.domain)
    p = get_provider(provider)
    ok = p.delete_dns(args.domain, args.type, args.host)
    print(json.dumps({"status": "ok" if ok else "not_found", "domain": args.domain, "deleted": f"{args.host} {args.type}"}))


def cmd_monitor(args):
    report = scan_all(list_providers(), args.days)
    print(report)


def cmd_balance(args):
    providers = args.provider.split(",") if args.provider != "all" else list_providers()
    for pname in providers:
        try:
            p = get_provider(pname)
            bal = p.get_account_balance()
            if bal:
                print(f"\n{pname}:")
                for k, v in bal.items():
                    print(f"  {k}: {v}")
            else:
                print(f"\n{pname}: balance not supported")
        except Exception as e:
            print(f"\n{pname}: {e}")


def cmd_renew_price(args):
    from domain_watch.providers.base import DnsRecord
    provider = args.provider if args.provider != "auto" else _detect_provider(args.domain)
    p = get_provider(provider)
    price = p.get_renewal_price(args.domain)
    print(json.dumps(price, indent=2, ensure_ascii=False))


def cmd_providers(args):
    for name, cls in BUILTIN.items():
        print(f"  {name:15s} — {cls.display_name}")
        print(f"  {'':15s}   API: {cls.api_docs_url}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Domain Watch — multi-registrar domain management")
    sub = parser.add_subparsers(dest="command")

    # list
    p_list = sub.add_parser("list", help="List all domains")
    p_list.add_argument("--provider", default="all", help="Provider name or 'all'")

    # dns
    p_dns = sub.add_parser("dns", help="List DNS records")
    p_dns.add_argument("domain")
    p_dns.add_argument("--provider", default="auto")

    # dns-set
    p_set = sub.add_parser("dns-set", help="Add/update DNS record")
    p_set.add_argument("domain")
    p_set.add_argument("type")
    p_set.add_argument("host")
    p_set.add_argument("value")
    p_set.add_argument("--ttl", type=int, default=600)
    p_set.add_argument("--provider", default="auto")

    # dns-delete
    p_del = sub.add_parser("dns-delete", help="Delete DNS record")
    p_del.add_argument("domain")
    p_del.add_argument("type")
    p_del.add_argument("host")
    p_del.add_argument("--provider", default="auto")

    # monitor
    p_mon = sub.add_parser("monitor", help="Monitor domains for expiry")
    p_mon.add_argument("--days", type=int, default=30, help="Warning threshold in days")

    # balance
    p_bal = sub.add_parser("balance", help="Account balance")
    p_bal.add_argument("--provider", default="all")

    # renew-price
    p_rp = sub.add_parser("renew-price", help="Check renewal price")
    p_rp.add_argument("domain")
    p_rp.add_argument("--provider", default="auto")

    # providers
    sub.add_parser("providers", help="List available providers")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    cmds = {
        "list": cmd_list,
        "dns": cmd_dns,
        "dns-set": cmd_dns_set,
        "dns-delete": cmd_dns_delete,
        "monitor": cmd_monitor,
        "balance": cmd_balance,
        "renew-price": cmd_renew_price,
        "providers": cmd_providers,
    }
    cmds[args.command](args)


if __name__ == "__main__":
    main()
