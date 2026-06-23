"""Cloudflare API provider (domains only — DNS managed via zones)."""

import os
import json
import urllib.request
from datetime import datetime
from typing import Optional

from .base import BaseProvider, DomainInfo, DnsRecord


class CloudflareProvider(BaseProvider):
    name = "cloudflare"
    display_name = "Cloudflare"
    api_docs_url = "https://developers.cloudflare.com/api/"

    API_URL = "https://api.cloudflare.com/client/v4"

    def __init__(self, api_token: str = "", **kw):
        super().__init__(api_token=api_token)
        self.api_token = api_token or os.getenv("CLOUDFLARE_API_TOKEN", "")

    def _req(self, method: str, path: str, data: dict = None) -> dict:
        url = f"{self.API_URL}{path}"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read())
        if not result.get("success"):
            errors = result.get("errors", [])
            raise RuntimeError(f"Cloudflare API error: {errors}")
        return result.get("result", {})

    def _get_zone_id(self, domain: str) -> str:
        """Resolve domain to zone ID."""
        zones = self._req("GET", f"/zones?name={domain}&status=active")
        for z in (zones if isinstance(zones, list) else [zones]):
            if z.get("name") == domain:
                return z["id"]
        raise ValueError(f"Zone not found for domain: {domain}")

    def list_domains(self) -> list[DomainInfo]:
        """List all zones (domains) in Cloudflare account."""
        zones = self._req("GET", "/zones?per_page=200&status=active")
        out = []
        for z in (zones if isinstance(zones, list) else []):
            expires = None
            exp_str = z.get("created_on", "")[:10]  # Cloudflare doesn't expose expiry
            created = None
            try:
                created = datetime.strptime(
                    (z.get("created_on") or "")[:10], "%Y-%m-%d"
                ).date()
            except ValueError:
                pass
            
            out.append(DomainInfo(
                name=z.get("name", ""),
                registrar="cloudflare",
                expires=expires,
                created=created,
                auto_renew=True,  # Cloudflare auto-renews by default
                locked=z.get("paused", False) is False,
                nameservers=z.get("name_servers", []),
                status="active" if z.get("status") == "active" else z.get("status", ""),
                raw=z,
            ))
        return out

    def get_domain(self, domain: str) -> DomainInfo:
        zones = self._req("GET", f"/zones?name={domain}&status=active")
        for z in (zones if isinstance(zones, list) else [zones]):
            if z.get("name") == domain:
                created = None
                try:
                    created = datetime.strptime(
                        (z.get("created_on") or "")[:10], "%Y-%m-%d"
                    ).date()
                except ValueError:
                    pass
                return DomainInfo(
                    name=z.get("name", domain),
                    registrar="cloudflare",
                    created=created,
                    auto_renew=True,
                    locked=not z.get("paused", False),
                    nameservers=z.get("name_servers", []),
                    status=z.get("status", ""),
                    raw=z,
                )
        raise ValueError(f"Zone not found: {domain}")

    def list_dns(self, domain: str) -> list[DnsRecord]:
        zone_id = self._get_zone_id(domain)
        records = self._req("GET", f"/zones/{zone_id}/dns_records?per_page=500")
        out = []
        for r in (records if isinstance(records, list) else []):
            out.append(DnsRecord(
                type=r.get("type", ""),
                host=r.get("name", "").replace(f".{domain}", ""),
                value=r.get("content", ""),
                ttl=int(r.get("ttl", 1)),
                priority=r.get("priority"),
            ))
        return out

    def set_dns(self, domain: str, record: DnsRecord) -> bool:
        zone_id = self._get_zone_id(domain)
        body = {
            "type": record.type,
            "name": record.host if record.host != "@" else domain,
            "content": record.value,
            "ttl": record.ttl if record.ttl > 0 else 1,
        }
        if record.priority is not None:
            body["priority"] = record.priority
        
        self._req("POST", f"/zones/{zone_id}/dns_records", body)
        return True

    def delete_dns(self, domain: str, record_type: str, host: str) -> bool:
        zone_id = self._get_zone_id(domain)
        # Find the record ID first
        records = self._req("GET", f"/zones/{zone_id}/dns_records?type={record_type}&per_page=500")
        target_host = host if host != "@" else domain
        for r in (records if isinstance(records, list) else []):
            if r.get("name") == target_host or r.get("name") == f"{host}.{domain}":
                self._req("DELETE", f"/zones/{zone_id}/dns_records/{r['id']}")
                return True
        return False
