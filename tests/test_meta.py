"""Meta-consistency guards: version drift and changelog hygiene."""

import pathlib
import tomllib

import rtai_core

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_version_single_source():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["version"] == rtai_core.__version__, (
        "version drift between pyproject.toml and rtai_core/version.py")


def test_changelog_documents_current_version():
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    heading = f"## {rtai_core.__version__}"
    assert heading in text, f"CHANGELOG missing entry '{heading}'"


def test_vendored_cores_match_shared_core():
    """Vendored copies must be byte-identical to the shared core."""
    shared = {p.relative_to(ROOT / "rtai_core"): p.read_bytes()
              for p in (ROOT / "rtai_core").rglob("*.py")}
    for project in sorted(ROOT.glob("0*")):
        vendored = project / "rtai_core"
        if not vendored.is_dir():  # pragma: no cover
            continue
        for rel_path, shared_bytes in shared.items():
            target = vendored / rel_path
            assert target.exists(), f"{project.name}: missing {rel_path}"
            assert target.read_bytes() == shared_bytes, (
                f"{project.name}: drifted {rel_path} - re-run vendor sync")