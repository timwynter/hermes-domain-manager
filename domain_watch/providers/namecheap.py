"""Namecheap API provider."""

import os
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional

from .base import BaseProvider, DomainInfo, DnsRecord


def _get_public_ip() -> str:
    for svc in ["https://api.ipify.org", "https://ifconfig.me/ip", "https://icanhazip.com"]:
        try:
            return urllib.request.urlopen(svc, timeout=5).read().decode().strip()
        except Exception:
            continue
    return "127.0.0.1"


class NamecheapProvider(BaseProvider):
    name = "namecheap"
    display_name = "Namecheap"
    api_docs_url = "https://www.namecheap.com/support/api/intro/"

    API_URL = "https://api.namecheap.com/xml.response"
    NS = "http://api.namecheap.com/xml.response"

    def __init__(self, api_key: str = "", api_user: str = "", username: str = "", **kw):
        super().__init__(api_key=api_key, api_user=api_user, username=username)
        self.api_key = api_key or os.getenv("NAMECHEAP_API_KEY", "")
        self.api_user = api_user or os.getenv("NAMECHEAP_API_USER", "")
        self.username = username or os.getenv("NAMECHEAP_USERNAME", "")

    def _call(self, command: str, extra: dict = None) -> ET.Element:
        params = {
            "ApiUser": self.api_user,
            "ApiKey": self.api_key,
            "UserName": self.username,
            "Command": f"namecheap.{command}",
            "ClientIp": _get_public_ip(),
        }
        if extra:
            params.update(extra)
        url = f"{self.API_URL}?{urllib.parse.urlencode(params)}"
        resp = urllib.request.urlopen(url, timeout=30)
        root = ET.fromstring(resp.read())
        
        status = root.attrib.get("Status")
        if status == "ERROR":
            errors = root.findall(f"{{{self.NS}}}Errors/{{{self.NS}}}Error")
            msgs = [e.text or e.attrib.get("Number", "?") for e in errors]
            raise RuntimeError(f"Namecheap API error: {'; '.join(msgs)}")
        return root

    def _find(self, root, tag):
        return root.find(f"{{{self.NS}}}{tag}")

    def _findall(self, root, tag):
        return root.findall(f"{{{self.NS}}}{tag}")

    def list_domains(self) -> list[DomainInfo]:
        root = self._call("domains.getList", {"PageSize": "100"})
        cr = self._find(root, "CommandResponse")
        result = self._find(cr, "DomainGetListResult") if cr is not None else None
        if result is None:
            return []
        
        domains = self._findall(result, "Domain")
        out = []
        for d in domains:
            a = d.attrib
            expires = None
            try:
                expires = datetime.strptime(a.get("Expires", ""), "%m/%d/%Y").date()
            except ValueError:
                pass
            created = None
            try:
                created = datetime.strptime(a.get("Created", ""), "%m/%d/%Y").date()
            except ValueError:
                pass
            
            out.append(DomainInfo(
                name=a.get("Name", ""),
                registrar="namecheap",
                expires=expires,
                created=created,
                auto_renew=a.get("AutoRenew") == "true",
                locked=a.get("IsLocked") == "true",
                privacy=a.get("WhoisGuard") == "ENABLED",
                raw=dict(a),
            ))
        return out

    def get_domain(self, domain: str) -> DomainInfo:
        root = self._call("domains.getInfo", {"DomainName": domain})
        info = self._find(self._find(root, "CommandResponse"), "DomainGetInfoResult")
        if info is None:
            raise ValueError(f"Domain not found: {domain}")
        a = info.attrib
        expires = None
        try:
            expires = datetime.strptime(a.get("DomainExpires", ""), "%m/%d/%Y").date()
        except ValueError:
            pass
        
        ns_el = self._find(info, "DnsDetails")
        ns = ns_el.attrib.get("Nameserver", "") if ns_el is not None else ""
        
        return DomainInfo(
            name=a.get("DomainName", domain),
            registrar="namecheap",
            expires=expires,
            auto_renew=a.get("AutoRenew") == "true",
            locked=a.get("IsLocked") == "true",
            privacy=a.get("WhoisGuard") == "ENABLED",
            nameservers=[n.strip() for n in ns.split(",") if n.strip()],
            raw=dict(a),
        )

    def list_dns(self, domain: str) -> list[DnsRecord]:
        parts = domain.split(".")
        sld, tld = parts[0], ".".join(parts[1:])
        root = self._call("domains.dns.getHosts", {"SLD": sld, "TLD": tld})
        hosts = self._findall(
            self._find(self._find(root, "CommandResponse"), "DomainDNSGetHostsResult"),
            "host",
        )
        records = []
        for h in hosts:
            a = h.attrib
            records.append(DnsRecord(
                type=a.get("Type", ""),
                host=a.get("Name", ""),
                value=a.get("Address", ""),
                ttl=int(a.get("TTL", 1800)),
                priority=int(a["MXPref"]) if a.get("MXPref") else None,
            ))
        return records

    def set_dns(self, domain: str, record: DnsRecord) -> bool:
        parts = domain.split(".")
        sld, tld = parts[0], ".".join(parts[1:])
        params = {"SLD": sld, "TLD": tld}
        
        # Warning: Namecheap replaces ALL records — fetch existing first
        existing = self.list_dns(domain)
        # Add existing records
        for i, r in enumerate(existing, 1):
            params[f"HostName{i}"] = r.host
            params[f"RecordType{i}"] = r.type
            params[f"Address{i}"] = r.value
            params[f"TTL{i}"] = str(r.ttl)
            if r.priority:
                params[f"MXPref{i}"] = str(r.priority)
        
        # Add/replace the new record
        i = len(existing) + 1
        params[f"HostName{i}"] = record.host
        params[f"RecordType{i}"] = record.type
        params[f"Address{i}"] = record.value
        params[f"TTL{i}"] = str(record.ttl)
        if record.priority:
            params[f"MXPref{i}"] = str(record.priority)
        
        root = self._call("domains.dns.setHosts", params)
        return root.attrib.get("Status") == "OK"

    def delete_dns(self, domain: str, record_type: str, host: str) -> bool:
        existing = self.list_dns(domain)
        filtered = [r for r in existing if not (r.type == record_type and r.host == host)]
        if len(filtered) == len(existing):
            return False  # Not found
        
        parts = domain.split(".")
        sld, tld = parts[0], ".".join(parts[1:])
        params = {"SLD": sld, "TLD": tld}
        for i, r in enumerate(filtered, 1):
            params[f"HostName{i}"] = r.host
            params[f"RecordType{i}"] = r.type
            params[f"Address{i}"] = r.value
            params[f"TTL{i}"] = str(r.ttl)
            if r.priority:
                params[f"MXPref{i}"] = str(r.priority)
        
        # If no records left, send empty
        if not filtered:
            params["HostName1"] = ""
            params["RecordType1"] = "A"
            params["Address1"] = ""
            params["TTL1"] = "1800"
        
        root = self._call("domains.dns.setHosts", params)
        return root.attrib.get("Status") == "OK"

    def get_renewal_price(self, domain: str) -> Optional[dict]:
        tld = domain.split(".")[-1]
        root = self._call("users.getPricing", {
            "ProductType": "DOMAIN",
            "ProductCategory": "RENEW",
            "ActionName": "RENEW",
            "ProductName": tld,
        })
        prices = self._findall(
            self._find(self._find(root, "CommandResponse"), "UserGetPricingResult"),
            "Price",
        )
        result = []
        for p in prices:
            a = p.attrib
            if a.get("DurationType") == "YEAR":
                result.append({"years": int(a["Duration"]), "price": float(a["Price"])})
        return {"domain": domain, "tld": tld, "prices": result}

    def get_account_balance(self) -> Optional[dict]:
        root = self._call("users.getBalances")
        bal = self._find(
            self._find(root, "CommandResponse"), "UserGetBalancesResult"
        )
        if bal is not None:
            return dict(bal.attrib)
        return None
