#!/usr/bin/env python3
"""Silent cron check — outputs domain expiry report only when action is needed.
Use with: hermes cron create ... --script this_file --no-agent
"""

import sys, os
sys.path.insert(0, os.path.expanduser("~/Projects/domain-watch"))

from domain_watch.monitor import scan_all
from domain_watch.providers import list_providers

WARN_DAYS = 30

report = scan_all(list_providers(), warn_days=WARN_DAYS)

# Only print if there are expiring or expired domains
if "EXPIRING" in report or "🔴" in report:
    print(report)
# Otherwise silent (no output = no message sent)
