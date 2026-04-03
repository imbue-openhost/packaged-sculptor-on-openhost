"""Seed an initial project and workspace so the user has something to work with.

Runs once after the Sculptor backend starts. Creates a git repo in the
devuser's home directory, then uses the sculpt CLI to register it as a
project and create a cloned workspace with an agent.

Skips silently if the repo or workspace already exist (i.e. on container
restart with persistent storage).

This version uses only the Python standard library (no httpx) so it can
run without the sculptor venv — only system Python 3 is needed.
"""

import json
import logging
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="seed_workspace: %(message)s")

SCULPTOR_PORT = int(os.environ.get("SCULPTOR_PORT", "8080"))
SCULPTOR_URL = f"http://127.0.0.1:{SCULPTOR_PORT}"

DEVUSER_HOME = os.environ.get("OPENHOST_APP_DATA_DIR", "") + "/home"
REPO_PATH = os.path.join(DEVUSER_HOME, "project")

MAX_WAIT_SECONDS = 60
POLL_INTERVAL = 2

# The sculpt CLI binary extracted from the packaged release
SCULPT_BIN = "/opt/sculptor/sculpt/sculpt"


def _wait_for_backend() -> bool:
    """Poll the backend health endpoint until it responds."""
    deadline = time.monotonic() + MAX_WAIT_SECONDS
    while time.monotonic() < deadline:
        try:
            req = urllib.request.Request(f"{SCULPTOR_URL}/health", method="GET")
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, urllib.error.HTTPError, OSError):
            pass
        time.sleep(POLL_INTERVAL)
    return False


def _create_repo() -> None:
    """Create a git repo with an initial commit at REPO_PATH.

    Raises on failure (e.g. subprocess errors). No-ops if the repo already exists.
    """
    if os.path.isdir(os.path.join(REPO_PATH, ".git")):
        logger.info("repo already exists at %s", REPO_PATH)
        return

    os.makedirs(REPO_PATH, exist_ok=True)

    subprocess.check_call(["git", "-C", REPO_PATH, "init", "-b", "main"])

    # Set repo-local git identity as a fallback. We use repo-local config
    # because supervisord's user= doesn't update HOME, so --global would
    # try to write to /root/.gitconfig which devuser can't access.
    def _git_config_default(key: str, value: str) -> None:
        """Set a repo-local git config value only if it isn't already set globally."""
        result = subprocess.run(
            ["git", "-C", REPO_PATH, "config", key],
            capture_output=True,
        )
        if result.returncode != 0:
            subprocess.check_call(["git", "-C", REPO_PATH, "config", key, value])

    _git_config_default("user.name", "OpenHost User")
    _git_config_default("user.email", "user@openhost.local")

    subprocess.check_call(
        ["git", "-C", REPO_PATH, "commit", "--allow-empty", "-m", "Initial commit"],
    )
    logger.info("created repo at %s", REPO_PATH)


def _sculpt(*args: str) -> subprocess.CompletedProcess:
    """Run a sculpt CLI command, pointing at the local backend."""
    env = {**os.environ, "SCULPT_API_PORT": str(SCULPTOR_PORT)}
    cmd = [SCULPT_BIN, *args]
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


def _has_workspaces() -> bool:
    """Check if any workspaces already exist."""
    result = _sculpt("workspace", "list", "--all", "--json")
    if result.returncode != 0:
        logger.error("failed to list workspaces: %s", result.stderr)
        return False
    workspaces = json.loads(result.stdout)
    return len(workspaces) > 0


def _seed_project_and_workspace() -> None:
    """Use the sculpt CLI to create a project, workspace, and agent."""
    if _has_workspaces():
        logger.info("workspace already exists, skipping seed")
        return

    # Create workspace (also initializes the project via --repo)
    result = _sculpt(
        "workspace", "create",
        "--repo", REPO_PATH,
        "--strategy", "clone",
        "--json",
    )
    if result.returncode != 0:
        logger.error("failed to create workspace: %s", result.stderr)
        return

    ws = json.loads(result.stdout)
    workspace_id = ws["id"]
    logger.info("created workspace %s", workspace_id)

    # Create an agent in the workspace
    result = _sculpt("agent", "create", "--workspace", workspace_id, "--json")
    if result.returncode != 0:
        logger.error("failed to create agent: %s", result.stderr)
        return

    agent = json.loads(result.stdout)
    logger.info("created agent %s", agent.get("id", ""))


def main() -> None:
    logger.info("waiting for sculptor backend...")
    if not _wait_for_backend():
        logger.error("backend did not start within %ds, giving up", MAX_WAIT_SECONDS)
        sys.exit(1)

    logger.info("backend is ready")

    try:
        _create_repo()
    except Exception:
        logger.exception("failed to create repo")
        sys.exit(1)

    _seed_project_and_workspace()
    logger.info("done")


if __name__ == "__main__":
    main()
