#!/usr/bin/env python
"""SNS EMR Backend PR scope validator (CI-only, git-diff based).

This CI-only tool validates that the committed file set in
`git diff <base>...<head> --name-only` is fully covered by an explicit JSON
allowlist supplied by the caller. Normal pytest runs never invoke it.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


class ScopeGuardError(Exception):
    """Deterministic configuration/environment failure (exit code 2)."""


@dataclass(frozen=True)
class Manifest:
    allowed_paths: frozenset[str]
    allowed_prefixes: tuple[str, ...]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_manifest(allowlist_path: Path) -> Manifest:
    if not allowlist_path.is_file():
        raise ScopeGuardError(
            f"authorization allowlist not found: {allowlist_path}. "
            "An explicit allowlist must be supplied via --allowlist."
        )

    try:
        raw_text = allowlist_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ScopeGuardError(
            f"unable to read authorization allowlist: {allowlist_path} ({exc})"
        ) from exc

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ScopeGuardError(
            f"authorization allowlist is not valid JSON: {allowlist_path} ({exc})"
        ) from exc

    if not isinstance(data, dict):
        raise ScopeGuardError(
            f"authorization allowlist must be a JSON object: {allowlist_path}"
        )

    allowed_paths_raw = data.get("allowed_paths", [])
    allowed_prefixes_raw = data.get("allowed_prefixes", [])

    if not isinstance(allowed_paths_raw, list) or not all(
        isinstance(item, str) for item in allowed_paths_raw
    ):
        raise ScopeGuardError(
            f"'allowed_paths' must be a list of strings: {allowlist_path}"
        )

    if not isinstance(allowed_prefixes_raw, list) or not all(
        isinstance(item, str) for item in allowed_prefixes_raw
    ):
        raise ScopeGuardError(
            f"'allowed_prefixes' must be a list of strings: {allowlist_path}"
        )

    allowed_paths = frozenset(allowed_paths_raw)
    allowed_prefixes = tuple(allowed_prefixes_raw)

    if not allowed_paths and not allowed_prefixes:
        raise ScopeGuardError(
            "authorization allowlist defines no allowed_paths or allowed_prefixes: "
            f"{allowlist_path}. An empty allowlist is a configuration error, not an "
            "automatic pass."
        )

    return Manifest(allowed_paths=allowed_paths, allowed_prefixes=allowed_prefixes)


def get_changed_files(repo_root: Path, base_ref: str, head_ref: str) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{base_ref}...{head_ref}"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise ScopeGuardError(f"unable to invoke git: {exc}") from exc

    if result.returncode != 0:
        detail = result.stderr.strip() or "git diff returned a non-zero exit code"
        raise ScopeGuardError(
            f"'git diff --name-only {base_ref}...{head_ref}' failed "
            f"(exit {result.returncode}): {detail}"
        )

    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def classify(changed_files: list[str], manifest: Manifest) -> tuple[list[str], list[str]]:
    authorized: list[str] = []
    unauthorized: list[str] = []

    for path in changed_files:
        normalized = path.replace("\\", "/")
        if normalized in manifest.allowed_paths or normalized.startswith(
            manifest.allowed_prefixes
        ):
            authorized.append(path)
        else:
            unauthorized.append(path)

    return authorized, unauthorized


def run(
    base_ref: str,
    head_ref: str,
    allowlist_path: Path,
    repo_root: Path | None = None,
) -> int:
    root = repo_root if repo_root is not None else _repo_root()

    manifest = load_manifest(allowlist_path)
    changed_files = get_changed_files(root, base_ref, head_ref)

    if not changed_files:
        print(f"No changes detected between {base_ref} and {head_ref}. Nothing to validate.")
        return 0

    authorized, unauthorized = classify(changed_files, manifest)

    print(f"Changed files ({base_ref}...{head_ref}): {len(changed_files)}")
    for path in authorized:
        print(f"  [AUTHORIZED]   {path}")
    for path in unauthorized:
        print(f"  [UNAUTHORIZED] {path}")

    if unauthorized:
        print(
            f"\nFAIL: {len(unauthorized)} unauthorized file(s) changed: {unauthorized}",
            file=sys.stderr,
        )
        return 1

    print(f"\nPASS: all {len(authorized)} changed file(s) are authorized.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--allowlist",
        required=True,
        type=Path,
        help="Path to the JSON authorization allowlist.",
    )
    parser.add_argument(
        "--base-ref",
        default="origin/main",
        help="Base ref to diff against (default: origin/main).",
    )
    parser.add_argument(
        "--head-ref",
        default="HEAD",
        help="Head ref to diff (default: HEAD).",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root to run git diff in (default: this repo's root).",
    )
    args = parser.parse_args(argv)

    try:
        return run(args.base_ref, args.head_ref, args.allowlist, args.repo_root)
    except ScopeGuardError as exc:
        print(f"CONFIGURATION ERROR: {exc}", file=sys.stderr)
        return 2
    except Exception:
        print("CONFIGURATION ERROR: unexpected validator failure.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
