"""
Source access at exact deployed commits.

Every component lives in its own git repository under .meridian/repos/.
Contract discovery reads files with `git show <commit>:<path>` and probes
materialize a clean copy with `git archive <commit>`. Nothing is ever read
from a working tree, so what is inspected is exactly what was deployed.
"""

from __future__ import annotations

import io
import json
import subprocess
import zipfile
from pathlib import Path

from engine.paths import REPOS


class SourceUnavailable(RuntimeError):
    pass


def repo_path(component: str) -> Path:
    path = REPOS / component
    if not (path / ".git").exists():
        raise SourceUnavailable(f"No repository for {component}. Run ./demo/seed.sh.")
    return path


def git(component: str, *args: str, binary: bool = False):
    result = subprocess.run(
        ["git", "-c", "core.autocrlf=false", *args],
        cwd=repo_path(component), capture_output=True, text=not binary,
    )
    if result.returncode != 0:
        err = result.stderr if not binary else result.stderr.decode(errors="replace")
        raise SourceUnavailable(f"git {' '.join(args)} failed for {component}: {err.strip()}")
    return result.stdout


def known_commits() -> dict[str, dict[str, str]]:
    path = REPOS / "commits.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def commit_for(component: str, version: str) -> str | None:
    """Resolve a released version to its commit via the version tag."""
    commits = known_commits().get(component, {})
    if version in commits:
        return commits[version]
    tag = version if version[:1] in ("v", "V") else f"v{version}"
    try:
        return git(component, "rev-parse", "--short=7", f"{tag}^{{commit}}").strip()
    except SourceUnavailable:
        return None


def show(component: str, commit: str, path: str) -> str:
    return git(component, "show", f"{commit}:{path}")


def exists(component: str, commit: str, path: str) -> bool:
    try:
        git(component, "cat-file", "-e", f"{commit}:{path}")
        return True
    except SourceUnavailable:
        return False


def list_files(component: str, commit: str, prefix: str = "") -> list[str]:
    out = git(component, "ls-tree", "-r", "--name-only", commit)
    return [p for p in out.splitlines() if p.startswith(prefix)]


def log(component: str, limit: int = 20) -> list[dict]:
    fmt = "%h%x1f%an%x1f%aI%x1f%s%x1f%D"
    out = git(component, "log", "--all", f"-n{limit}", f"--format={fmt}")
    rows = []
    for line in out.splitlines():
        h, author, date, subject, refs = (line.split("\x1f") + [""] * 5)[:5]
        rows.append({"commit": h, "author": author, "date": date, "subject": subject,
                     "refs": [r.strip() for r in refs.split(",") if r.strip()]})
    return rows


def materialize(component: str, commit: str, destination: Path) -> Path:
    """Extract a clean tree of `component` at `commit` into `destination`."""
    data = git(component, "archive", "--format=zip", commit, binary=True)
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        archive.extractall(destination)
    return destination


def diff(component: str, base: str, head: str, path: str | None = None) -> str:
    args = ["diff", "--no-color", base, head]
    if path:
        args += ["--", path]
    return git(component, *args)
