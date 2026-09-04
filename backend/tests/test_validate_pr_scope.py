"""Tests for the CI-only PR scope validator."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts import validate_pr_scope
from scripts.validate_pr_scope import (
    Manifest,
    ScopeGuardError,
    classify,
    get_changed_files,
    load_manifest,
    main,
    run,
)


def _git(cwd: Path, *args: str) -> None:
    result = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"git {' '.join(args)} failed: {result.stdout}\n{result.stderr}"
    )


def _init_repo_with_diff(tmp_path: Path, changed_files: list[str]) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")

    (repo / "README.md").write_text("base\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "base")
    _git(repo, "branch", "-f", "base_ref", "HEAD")

    for rel_path in changed_files:
        full_path = repo / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text("content\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "head changes")
    _git(repo, "branch", "-f", "head_ref", "HEAD")

    return repo


def _write_allowlist(
    tmp_path: Path, data: dict | str, name: str = "allowlist.json"
) -> Path:
    allowlist_path = tmp_path / name
    if isinstance(data, str):
        allowlist_path.write_text(data, encoding="utf-8")
    else:
        allowlist_path.write_text(json.dumps(data), encoding="utf-8")
    return allowlist_path


def test_all_authorized_files_pass(tmp_path):
    repo = _init_repo_with_diff(
        tmp_path,
        ["backend/manifests/foo.json", "backend/scripts/import_foo.py"],
    )
    allowlist_path = _write_allowlist(
        tmp_path,
        {
            "allowed_paths": [
                "backend/manifests/foo.json",
                "backend/scripts/import_foo.py",
            ]
        },
    )

    exit_code = run("base_ref", "head_ref", allowlist_path, repo_root=repo)
    assert exit_code == 0


def test_allowed_prefixes_also_pass(tmp_path):
    repo = _init_repo_with_diff(
        tmp_path,
        ["backend/alembic/versions/0001_add_thing.py"],
    )
    allowlist_path = _write_allowlist(
        tmp_path,
        {"allowed_prefixes": ["backend/alembic/versions/"]},
    )

    exit_code = run("base_ref", "head_ref", allowlist_path, repo_root=repo)
    assert exit_code == 0


def test_unauthorized_file_fails_with_clear_message(tmp_path, capsys):
    repo = _init_repo_with_diff(
        tmp_path,
        ["backend/manifests/foo.json", "backend/app/models/patients.py"],
    )
    allowlist_path = _write_allowlist(
        tmp_path,
        {"allowed_paths": ["backend/manifests/foo.json"]},
    )

    exit_code = run("base_ref", "head_ref", allowlist_path, repo_root=repo)
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "backend/app/models/patients.py" in captured.err
    assert "unauthorized" in captured.err.lower()


def test_exit_code_preserved_through_main_cli_for_unauthorized(tmp_path):
    repo = _init_repo_with_diff(
        tmp_path,
        ["backend/app/models/patients.py"],
    )
    allowlist_path = _write_allowlist(
        tmp_path,
        {"allowed_paths": ["backend/manifests/foo.json"]},
    )

    exit_code = main(
        [
            "--allowlist",
            str(allowlist_path),
            "--base-ref",
            "base_ref",
            "--head-ref",
            "head_ref",
            "--repo-root",
            str(repo),
        ]
    )
    assert exit_code == 1


def test_missing_allowlist_fails_deterministically(tmp_path, capsys):
    repo = _init_repo_with_diff(tmp_path, ["backend/manifests/foo.json"])
    missing_allowlist_path = tmp_path / "does_not_exist.json"

    exit_code = main(
        [
            "--allowlist",
            str(missing_allowlist_path),
            "--base-ref",
            "base_ref",
            "--head-ref",
            "head_ref",
            "--repo-root",
            str(repo),
        ]
    )
    assert exit_code == 2

    captured = capsys.readouterr()
    assert "CONFIGURATION ERROR" in captured.err
    assert "not found" in captured.err.lower()
    assert "Traceback" not in captured.err


def test_exit_code_preserved_through_main_cli_for_config_error(tmp_path):
    repo = _init_repo_with_diff(tmp_path, ["backend/manifests/foo.json"])
    missing_allowlist_path = tmp_path / "does_not_exist.json"

    exit_code = main(
        [
            "--allowlist",
            str(missing_allowlist_path),
            "--base-ref",
            "base_ref",
            "--head-ref",
            "head_ref",
            "--repo-root",
            str(repo),
        ]
    )
    assert exit_code == 2


def test_load_manifest_raises_scope_guard_error_for_missing_file(tmp_path):
    with pytest.raises(ScopeGuardError, match="not found"):
        load_manifest(tmp_path / "nope.json")


def test_malformed_allowlist_json_fails_deterministically(tmp_path, capsys):
    repo = _init_repo_with_diff(tmp_path, ["backend/manifests/foo.json"])
    allowlist_path = _write_allowlist(tmp_path, "{not valid json!!!")

    exit_code = main(
        [
            "--allowlist",
            str(allowlist_path),
            "--base-ref",
            "base_ref",
            "--head-ref",
            "head_ref",
            "--repo-root",
            str(repo),
        ]
    )
    assert exit_code == 2

    captured = capsys.readouterr()
    assert "CONFIGURATION ERROR" in captured.err
    assert "not valid JSON" in captured.err


def test_load_manifest_raises_for_malformed_json(tmp_path):
    allowlist_path = _write_allowlist(tmp_path, "{not valid json!!!")
    with pytest.raises(ScopeGuardError, match="not valid JSON"):
        load_manifest(allowlist_path)


def test_empty_allowlist_fails_deterministically(tmp_path, capsys):
    repo = _init_repo_with_diff(tmp_path, ["backend/manifests/foo.json"])
    allowlist_path = _write_allowlist(tmp_path, {})

    exit_code = main(
        [
            "--allowlist",
            str(allowlist_path),
            "--base-ref",
            "base_ref",
            "--head-ref",
            "head_ref",
            "--repo-root",
            str(repo),
        ]
    )
    assert exit_code == 2

    captured = capsys.readouterr()
    assert "CONFIGURATION ERROR" in captured.err
    assert "no allowed_paths or allowed_prefixes" in captured.err


def test_load_manifest_raises_for_empty_allowlist(tmp_path):
    allowlist_path = _write_allowlist(
        tmp_path, {"allowed_paths": [], "allowed_prefixes": []}
    )
    with pytest.raises(ScopeGuardError, match="no allowed_paths or allowed_prefixes"):
        load_manifest(allowlist_path)


def test_load_manifest_rejects_non_string_entries(tmp_path):
    allowlist_path = _write_allowlist(tmp_path, {"allowed_paths": [123]})
    with pytest.raises(ScopeGuardError, match="allowed_paths"):
        load_manifest(allowlist_path)


def test_load_manifest_rejects_non_object_json(tmp_path):
    allowlist_path = _write_allowlist(tmp_path, "[1, 2, 3]")
    with pytest.raises(ScopeGuardError, match="must be a JSON object"):
        load_manifest(allowlist_path)


def test_git_diff_failure_is_deterministic_not_silent_pass(tmp_path, capsys):
    not_a_repo = tmp_path / "not_a_repo"
    not_a_repo.mkdir()
    allowlist_path = _write_allowlist(tmp_path, {"allowed_paths": ["foo.txt"]})

    exit_code = main(
        [
            "--allowlist",
            str(allowlist_path),
            "--base-ref",
            "base_ref",
            "--head-ref",
            "head_ref",
            "--repo-root",
            str(not_a_repo),
        ]
    )
    assert exit_code == 2

    captured = capsys.readouterr()
    assert "CONFIGURATION ERROR" in captured.err
    assert "Traceback (most recent call last)" not in captured.err
    assert "Traceback (most recent call last)" not in captured.out


def test_invalid_head_ref_fails_deterministically(tmp_path, capsys):
    repo = _init_repo_with_diff(tmp_path, ["backend/manifests/foo.json"])
    allowlist_path = _write_allowlist(
        tmp_path, {"allowed_paths": ["backend/manifests/foo.json"]}
    )

    exit_code = main(
        [
            "--allowlist",
            str(allowlist_path),
            "--base-ref",
            "base_ref",
            "--head-ref",
            "definitely_missing_head_ref",
            "--repo-root",
            str(repo),
        ]
    )
    assert exit_code == 2

    captured = capsys.readouterr()
    assert "CONFIGURATION ERROR" in captured.err
    assert "definitely_missing_head_ref" in captured.err
    assert "Traceback" not in captured.err


def test_get_changed_files_raises_scope_guard_error_for_bad_refs(tmp_path):
    repo = _init_repo_with_diff(tmp_path, ["backend/manifests/foo.json"])
    with pytest.raises(ScopeGuardError):
        get_changed_files(repo, "nonexistent_ref_aaa", "nonexistent_ref_bbb")


def test_git_unavailable_fails_deterministically(monkeypatch, tmp_path, capsys):
    repo = _init_repo_with_diff(tmp_path, ["backend/manifests/foo.json"])
    allowlist_path = _write_allowlist(
        tmp_path, {"allowed_paths": ["backend/manifests/foo.json"]}
    )

    def _boom(*args, **kwargs):
        raise FileNotFoundError("git executable not found")

    monkeypatch.setattr(validate_pr_scope.subprocess, "run", _boom)

    exit_code = main(
        [
            "--allowlist",
            str(allowlist_path),
            "--base-ref",
            "base_ref",
            "--head-ref",
            "head_ref",
            "--repo-root",
            str(repo),
        ]
    )
    assert exit_code == 2

    captured = capsys.readouterr()
    assert "CONFIGURATION ERROR" in captured.err
    assert "unable to invoke git" in captured.err
    assert "Traceback" not in captured.err
    assert "Traceback" not in captured.out


def test_get_changed_files_raises_scope_guard_error_when_git_missing(monkeypatch, tmp_path):
    def _boom(*args, **kwargs):
        raise OSError("git executable not found")

    monkeypatch.setattr(validate_pr_scope.subprocess, "run", _boom)
    with pytest.raises(ScopeGuardError, match="unable to invoke git"):
        get_changed_files(tmp_path, "base_ref", "head_ref")


def test_no_changes_between_refs_passes_trivially(tmp_path):
    repo = tmp_path / "repo_no_diff"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "base")

    allowlist_path = _write_allowlist(tmp_path, {"allowed_paths": ["irrelevant.txt"]})
    exit_code = run("HEAD", "HEAD", allowlist_path, repo_root=repo)
    assert exit_code == 0


def test_unstaged_files_do_not_affect_committed_diff_validation(tmp_path):
    repo = _init_repo_with_diff(tmp_path, ["backend/manifests/foo.json"])
    allowlist_path = _write_allowlist(
        tmp_path, {"allowed_paths": ["backend/manifests/foo.json"]}
    )

    (repo / "README.md").write_text("base\nunstaged change\n", encoding="utf-8")

    exit_code = run("base_ref", "head_ref", allowlist_path, repo_root=repo)
    assert exit_code == 0


def test_untracked_files_do_not_affect_committed_diff_validation(tmp_path):
    repo = _init_repo_with_diff(tmp_path, ["backend/manifests/foo.json"])
    allowlist_path = _write_allowlist(
        tmp_path, {"allowed_paths": ["backend/manifests/foo.json"]}
    )

    (repo / "totally_untracked_secret.txt").write_text("surprise\n", encoding="utf-8")

    exit_code = run("base_ref", "head_ref", allowlist_path, repo_root=repo)
    assert exit_code == 0


def test_classify_exact_path_match_not_suffix_match():
    manifest = Manifest(
        allowed_paths=frozenset({"backend/manifests/foo.json"}),
        allowed_prefixes=(),
    )
    authorized, unauthorized = classify(
        ["backend/manifests/foo.json", "vendor/backend/manifests/foo.json"],
        manifest,
    )
    assert authorized == ["backend/manifests/foo.json"]
    assert unauthorized == ["vendor/backend/manifests/foo.json"]


def test_classify_prefix_match():
    manifest = Manifest(
        allowed_paths=frozenset(),
        allowed_prefixes=("backend/alembic/versions/",),
    )
    authorized, unauthorized = classify(
        ["backend/alembic/versions/0001_x.py", "backend/app/main.py"],
        manifest,
    )
    assert authorized == ["backend/alembic/versions/0001_x.py"]
    assert unauthorized == ["backend/app/main.py"]


@pytest.mark.parametrize(
    ("argv", "setup"),
    [
        (
            lambda repo, tmp: [
                "--allowlist",
                str(tmp / "missing.json"),
                "--base-ref",
                "base_ref",
                "--head-ref",
                "head_ref",
                "--repo-root",
                str(repo),
            ],
            None,
        ),
        (
            lambda repo, tmp: [
                "--allowlist",
                str(tmp / "malformed.json"),
                "--base-ref",
                "base_ref",
                "--head-ref",
                "head_ref",
                "--repo-root",
                str(repo),
            ],
            lambda tmp: (tmp / "malformed.json").write_text(
                "{bad json", encoding="utf-8"
            ),
        ),
        (
            lambda repo, tmp: [
                "--allowlist",
                str(tmp / "good.json"),
                "--base-ref",
                "base_ref",
                "--head-ref",
                "missing_head",
                "--repo-root",
                str(repo),
            ],
            lambda tmp: (tmp / "good.json").write_text(
                json.dumps({"allowed_paths": ["backend/manifests/foo.json"]}),
                encoding="utf-8",
            ),
        ),
    ],
)
def test_no_credentials_or_traceback_ever_printed(tmp_path, capsys, argv, setup):
    repo = _init_repo_with_diff(tmp_path, ["backend/manifests/foo.json"])
    if setup is not None:
        setup(tmp_path)

    exit_code = main(argv(repo, tmp_path))
    assert exit_code == 2

    captured = capsys.readouterr()
    combined = f"{captured.out}\n{captured.err}"
    assert "Traceback" not in combined
    assert "postgresql://" not in combined


_AFFECTED_ONTOLOGY_TEST_MODULES = [
    "tests/test_als_production_source_manifest.py",
    "tests/test_cardiovascular_production_source_manifest.py",
    "tests/test_dementia_production_hardening.py",
    "tests/test_hiv_production_source_manifest.py",
    "tests/test_liver_production_source_manifest.py",
    "tests/test_neurologic_production_source_manifest.py",
    "tests/test_ontology_neurologic_clinical_reasoning.py",
    "tests/test_pulmonary_production_source_manifest.py",
    "tests/test_renal_production_source_manifest.py",
]


def test_affected_ontology_modules_no_longer_reference_git_diff():
    backend_root = Path(__file__).resolve().parents[1]
    removed_test_name = "test_only_" "authorized_files_changed"
    for relative_path in _AFFECTED_ONTOLOGY_TEST_MODULES:
        module_path = backend_root / relative_path
        source = module_path.read_text(encoding="utf-8")
        assert "subprocess" not in source, (
            f"{relative_path} still imports/uses subprocess; scope-guard removal incomplete"
        )
        assert f"def {removed_test_name}" not in source, (
            f"{relative_path} still defines the removed scope-guard test"
        )
        assert "origin/main" not in source, (
            f"{relative_path} still references origin/main diffing"
        )
        assert '"git"' not in source and "'git'" not in source, (
            f"{relative_path} still invokes a git subprocess; scope-guard removal incomplete"
        )
