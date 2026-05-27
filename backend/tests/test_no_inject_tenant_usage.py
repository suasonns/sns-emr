from pathlib import Path

FORBIDDEN_IMPORT = "inject_tenant"

ALLOWED_FILES = {
    "app/dependencies/tenant.py",
}


def test_inject_tenant_not_used_outside_dependencies():
    app_dir = Path("app")

    offenders = []
    for path in app_dir.rglob("*.py"):
        rel = str(path).replace("\\", "/")
        if rel in ALLOWED_FILES:
            continue

        content = path.read_text(encoding="utf-8")
        if FORBIDDEN_IMPORT in content:
            offenders.append(rel)

    assert not offenders, f"inject_tenant used in forbidden files: {offenders}"