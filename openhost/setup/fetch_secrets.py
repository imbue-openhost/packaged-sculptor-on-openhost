#!/usr/bin/env python3
"""Fetch secrets from the OpenHost secrets service and write them to a shell-sourceable file.

Intended to run at container startup before other services. Requires:
  OPENHOST_APP_TOKEN   - app token for service auth
  OPENHOST_ROUTER_URL  - router base URL (e.g. http://127.0.0.1:8080)

Writes /run/openhost-secrets.env with export lines for each fetched secret.
Exits 0 even if secrets service is unavailable (services may not be deployed yet).
"""

import json
import os
import urllib.error
import urllib.request

ROUTER_URL = os.environ.get("OPENHOST_ROUTER_URL", "")
APP_TOKEN = os.environ.get("OPENHOST_APP_TOKEN", "")
OUTPUT_FILE = "/run/openhost-secrets.env"

KEYS = [
    "ANTHROPIC_API_KEY",
    "GIT_USER_NAME",
    "GIT_USER_EMAIL",
    "GITHUB_ACCESS_TOKEN",
    "GITLAB_ACCESS_TOKEN",
]


def main():
    if not ROUTER_URL or not APP_TOKEN:
        print(
            "fetch_secrets: OPENHOST_ROUTER_URL or OPENHOST_APP_TOKEN not set, skipping"
        )
        _write_empty()
        return

    url = f"{ROUTER_URL}/api/services/v2/call/secrets/get"
    body = json.dumps({"keys": KEYS}).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {APP_TOKEN}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        print(f"fetch_secrets: HTTP {e.code} from secrets service: {body}")
        _write_empty()
        return
    except (urllib.error.URLError, OSError) as e:
        print(f"fetch_secrets: could not reach secrets service ({e}), skipping")
        _write_empty()
        return

    secrets = data.get("secrets", {})
    missing = data.get("missing", [])

    if missing:
        print(f"fetch_secrets: missing keys (granted but not set): {missing}")

    with open(OUTPUT_FILE, "w") as f:
        for key, value in secrets.items():
            # Shell-escape single quotes in values
            escaped = value.replace("'", "'\\''")
            f.write(f"export {key}='{escaped}'\n")

    os.chmod(OUTPUT_FILE, 0o600)
    print(f"fetch_secrets: wrote {len(secrets)} secrets to {OUTPUT_FILE}")


def _write_empty():
    with open(OUTPUT_FILE, "w") as f:
        f.write("# No secrets fetched\n")
    os.chmod(OUTPUT_FILE, 0o600)


if __name__ == "__main__":
    main()
