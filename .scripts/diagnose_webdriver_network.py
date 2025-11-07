"""Diagnostic helper to reproduce webdriver_manager network/DNS failures.

Run this with the same Python interpreter you used for the failure and also with the system
Python to compare results. It prints environment variables, socket.getaddrinfo results,
and a simple HTTPS request to the msedgedriver host.

Usage:
  # inside poetry venv
  poetry run python scripts/diagnose_webdriver_network.py

  # system python
  python scripts/diagnose_webdriver_network.py

"""

from __future__ import annotations

import os
import socket
import sys
import traceback
import requests


HOSTS = [
    "msedgedriver.azureedge.net",
    "chromedriver.storage.googleapis.com",
    "github.com",
    "www.google.com",
]


def print_env():
    keys = ["HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "http_proxy", "https_proxy", "no_proxy"]
    print("Environment vars:")
    for k in keys:
        v = os.environ.get(k)
        if v:
            print(f"  {k}={v}")
    print()


def dns_check(host: str):
    try:
        print(f"DNS lookup for {host}:")
        infos = socket.getaddrinfo(host, 443)
        for info in infos[:5]:
            print(" ", info)
    except Exception:
        print("  DNS lookup failed:")
        traceback.print_exc()
    print()


def http_check(url: str):
    try:
        print(f"HTTP HEAD {url} ->")
        r = requests.head(url, timeout=10)
        print(f"  status: {r.status_code}")
        print(f"  headers: {list(r.headers.items())[:3]}")
    except Exception:
        print("  HTTP check failed:")
        traceback.print_exc()
    print()


def main():
    print("Python:", sys.executable, sys.version.replace("\n", " "))
    print_env()

    for h in HOSTS:
        dns_check(h)

    # Try a real request against msedgedriver
    target = "https://msedgedriver.azureedge.net/"
    http_check(target)

    print("Done.")


if __name__ == "__main__":
    main()
