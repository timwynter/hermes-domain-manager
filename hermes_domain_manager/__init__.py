"""
Domain Watch — Multi-registrar domain management for Hermes Agent.

Supports: Namecheap, GoDaddy, Cloudflare (extensible).
Unified CLI for listing, DNS, monitoring, and renewal alerts.
"""

import os

# Auto-load ~/.hermes/.env into os.environ so providers can read creds
def _load_dotenv():
    env_path = os.path.expanduser("~/.hermes/.env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip()

_load_dotenv()

__version__ = "1.0.0"
__author__ = "Tim Wynter"
__license__ = "MIT"
