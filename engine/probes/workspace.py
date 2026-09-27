"""
Source access at exact deployed commits.

Every component lives in its own git repository under .meridian/repos/.
Contract discovery reads files with `git show <commit>:<path>` and probes
materialize a clean copy with `git archive <commit>`. Nothing is ever read
from a working tree, so what is inspected is exactly what was deployed.

Vercel's Python runtime does not provide the git executable. In that runtime,
this module falls back to the checked-in version trees under
sample-system/<component>/versions/<version>, resolved through the generated
commit map. The fallback still reads an exact released version tree and keeps
Git-backed behavior unchanged for local development and remediation tooling.
"""

from __future__ import annotations

import difflib
import io
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

from engine.paths import REPOS, ROOT


class SourceUnavailable(RuntimeError):
    pass


def _git_available() -> bool:
    return shutil.which("git") is not None


def repo_path(component: str) -> Path:
    path = REPOS / component
    if not (path / ".git").exists():
        raise SourceUnavailable(f"No repository for {component}. Run ./demo/seed.sh.")
    return path


def git(component: str, *args: str, binary: bool = False):
    if not _git_available():
        raise SourceUnavailable(
            "The git executable is unavailable in this runtime; use the version-tree fallback for source reads."
        )
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


def _version_for_commit(component: str, commit: str) -> str | None:
    for version, known_commit in known_commits().get(component, {}).items():
        if known_commit == commit or known_commit.startswith(commit) or commit.startswith(known_commit):
            return version
    return None


def _version_tree(component: str, commit: str) -> Path:
    version = _version_for_commit(component, commit)
    if version is None:
        raise SourceUnavailable(f"No version tree for {component} at commit {commit}.")
    root = ROOT / "sample-system" / component / "versions" / version
    if not root.is_dir():
        raise SourceUnavailable(f"No version tree for {component} {version}.")
    return root


def commit_for(component: str, version: str) -> str | None:
    """Resolve a released version to its commit via the version tag."""
    commits = known_commits().get(component, {})
    if version in commits:
        return commits[version]
    if not _git_available():
        return None
    tag = version if version[:1] in ("v", "V") else f"v{version}"
    try:
        return git(component, "rev-parse", "--short=7", f"{tag}^{{commit}}").strip()
    except SourceUnavailable:
        return None


def show(component: str, commit: str, path: str) -> str:
    if _git_available():
        return git(component, "show", f"{commit}:{path}")
    root = _version_tree(component, commit)
    target = root / path
    if not target.is_file():
        raise SourceUnavailable(f"Path {path} is not present for {component} at commit {commit}.")
    return target.read_text(encoding="utf-8")


def exists(component: str, commit: str, path: str) -> bool:
    if _git_available():
        try:
            git(component, "cat-file", "-e", f"{commit}:{path}")
            return True
        except SourceUnavailable:
            return False
    try:
        return (_version_tree(component, commit) / path).is_file()
    except SourceUnavailable:
        return False


def list_files(component: str, commit: str, prefix: str = "") -> list[str]:
    if _git_available():
        out = git(component, "ls-tree", "-r", "--name-only", commit)
        return [p for p in out.splitlines() if p.startswith(prefix)]
    root = _version_tree(component, commit)
    return sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.relative_to(root).as_posix().startswith(prefix)
    )


def log(component: str, limit: int = 20) -> list[dict]:
    if _git_available():
        fmt = "%h%x1f%an%x1f%aI%x1f%s%x1f%D"
        out = git(component, "log", "--all", f"-n{limit}", f"--format={fmt}")
        rows = []
        for line in out.splitlines():
            h, author, date, subject, refs = (line.split("\x1f") + [""] * 5)[:5]
            rows.append({"commit": h, "author": author, "date": date, "subject": subject,
                         "refs": [r.strip() for r in refs.split(",") if r.strip()]})
        return rows

    commits = known_commits().get(component, {})
    return [
        {"commit": commit, "author": "Meridian synthetic", "date": "",
         "subject": f"Release {version}", "refs": [version if version[:1] in ("v", "V") else f"v{version}"]}
        for version, commit in list(commits.items())[::-1][:limit]
    ]


def materialize(component: str, commit: str, destination: Path) -> Path:
    """Extract a clean tree of `component` at `commit` into `destination`."""
    if _git_available():
        data = git(component, "archive", "--format=zip", commit, binary=True)
        destination.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            archive.extractall(destination)
        return destination
    shutil.copytree(_version_tree(component, commit), destination, dirs_exist_ok=True)
    return destination


def diff(component: str, base: str, head: str, path: str | None = None) -> str:
    if _git_available():
        args = ["diff", "--no-color", base, head]
        if path:
            args += ["--", path]
        return git(component, *args)
    if not path:
        return ""
    before = show(component, base, path).splitlines(keepends=True)
    after = show(component, head, path).splitlines(keepends=True)
    return "".join(difflib.unified_diff(before, after, fromfile=f"{base}:{path}", tofile=f"{head}:{path}"))
