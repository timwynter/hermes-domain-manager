"""GoDaddy API provider."""

import os
import json
import urllib.request
from datetime import datetime
from typing import Optional

from .base import BaseProvider, DomainInfo, DnsRecord


class GoDaddyProvider(BaseProvider):
    name = "godaddy"
    display_name = "GoDaddy"
    api_docs_url = "https://developer.godaddy.com/"

    API_URL = "https://api.godaddy.com/v1"

    def __init__(self, api_key: str = "", api_secret: str = "", **kw):
        super().__init__(api_key=api_key, api_secret=api_secret)
        self.api_key = api_key or os.getenv("GODADDY_API_KEY", "")
        self.api_secret = api_secret or os.getenv("GODADDY_API_SECRET", "")

    def _req(self, method: str, path: str, data: dict = None) -> dict:
        url = f"{self.API_URL}{path}"
        headers = {
            "Authorization": f"sso-key {self.api_key}:{self.api_secret}",
            "Content-Type": "application/json",
        }
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        resp = urllib.request.urlopen(req, timeout=30)
        if resp.status == 204:
            return {}
        return json.loads(resp.read())

    def list_domains(self) -> list[DomainInfo]:
        data = self._req("GET", "/domains?limit=200&statuses=ACTIVE")
        out = []
        for d in data:
            expires = None
            exp_str = (d.get("expires") or "")[:10]
            if exp_str:
                try:
                    expires = datetime.strptime(exp_str, "%Y-%m-%d").date()
                except ValueError:
                    pass
            created = None
            cr_str = (d.get("createdAt") or "")[:10]
            if cr_str:
                try:
                    created = datetime.strptime(cr_str, "%Y-%m-%d").date()
                except ValueError:
                    pass
            
            out.append(DomainInfo(
                name=d.get("domain", ""),
                registrar="godaddy",
                expires=expires,
                created=created,
                auto_renew=d.get("renewAuto", False),
                locked=d.get("locked", False),
                privacy=d.get("privacy", False),
                nameservers=d.get("nameServers") or [],
                status=d.get("status", ""),
                raw=d,
            ))
        return out

    def get_domain(self, domain: str) -> DomainInfo:
        d = self._req("GET", f"/domains/{domain}")
        expires = None
        exp_str = (d.get("expires") or "")[:10]
        if exp_str:
            try:
                expires = datetime.strptime(exp_str, "%Y-%m-%d").date()
            except ValueError:
                pass
        return DomainInfo(
            name=d.get("domain", domain),
            registrar="godaddy",
            expires=expires,
            auto_renew=d.get("renewAuto", False),
            locked=d.get("locked", False),
            privacy=d.get("privacy", False),
            nameservers=d.get("nameServers") or [],
            status=d.get("status", ""),
            raw=d,
        )

    def list_dns(self, domain: str) -> list[DnsRecord]:
        data = self._req("GET", f"/domains/{domain}/records")
        records = []
        for r in data:
            records.append(DnsRecord(
                type=r.get("type", ""),
                host=r.get("name", ""),
                value=r.get("data", ""),
                ttl=int(r.get("ttl", 600)),
                priority=r.get("priority"),
            ))
        return records

    def set_dns(self, domain: str, record: DnsRecord) -> bool:
        body = [{
            "type": record.type,
            "name": record.host,
            "data": record.value,
            "ttl": record.ttl,
        }]
        if record.priority is not None:
            body[0]["priority"] = record.priority
        
        self._req("PUT", f"/domains/{domain}/records/{record.type}/{record.host}", body)
        return True

    def delete_dns(self, domain: str, record_type: str, host: str) -> bool:
        self._req("DELETE", f"/domains/{domain}/records/{record_type}/{host}")
        return True
