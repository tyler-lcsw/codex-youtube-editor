import plistlib

import pytest


def _app(
    path,
    payload,
    *,
    bundle_id="local.tyler.codex-studio",
    bundle_executable="CodexStudio",
):
    executable = path / "Contents/MacOS/CodexStudio"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(payload)
    executable.chmod(0o755)
    (path / "Contents/Info.plist").write_bytes(
        plistlib.dumps(
            {
                "CFBundleExecutable": bundle_executable,
                "CFBundleIdentifier": bundle_id,
                "CFBundleName": "Codex Media Studio",
            }
        )
    )
    return path


def test_install_updates_canonical_bundle_without_replacing_its_outer_directory(tmp_path):
    from tools.install_studio_app import install_studio_app

    source = _app(tmp_path / "build/Codex Media Studio.app", b"new")
    destination = _app(tmp_path / "Applications/Codex Media Studio.app", b"old")
    backups = tmp_path / "Application Support/Codex Media Studio/Backups"
    original_inode = destination.stat().st_ino

    result = install_studio_app(
        source,
        destination,
        backup_root=backups,
        running_check=lambda _: False,
        timestamp="20260908-120000",
    )

    assert result == destination
    assert destination.stat().st_ino == original_inode
    assert (destination / "Contents/MacOS/CodexStudio").read_bytes() == b"new"
    backup = backups / "Codex Media Studio-20260908-120000.app-backup"
    assert (backup / "Contents/MacOS/CodexStudio").read_bytes() == b"old"
    assert not list((tmp_path / "Applications").glob("*.previous*"))


def test_install_refuses_to_modify_a_running_canonical_bundle(tmp_path):
    from tools.install_studio_app import install_studio_app

    source = _app(tmp_path / "build/Codex Media Studio.app", b"new")
    destination = _app(tmp_path / "Applications/Codex Media Studio.app", b"old")
    backups = tmp_path / "backups"

    with pytest.raises(RuntimeError, match="Quit Codex Media Studio"):
        install_studio_app(
            source,
            destination,
            backup_root=backups,
            running_check=lambda _: True,
        )

    assert (destination / "Contents/MacOS/CodexStudio").read_bytes() == b"old"
    assert not backups.exists()


def test_install_rejects_a_different_application_identity(tmp_path):
    from tools.install_studio_app import install_studio_app

    source = _app(
        tmp_path / "build/Codex Media Studio.app",
        b"other",
        bundle_id="example.unrelated-app",
    )
    destination = tmp_path / "Applications/Codex Media Studio.app"

    with pytest.raises(ValueError, match="bundle identifier"):
        install_studio_app(
            source,
            destination,
            backup_root=tmp_path / "backups",
            running_check=lambda _: False,
        )

    assert not destination.exists()


def test_install_rejects_mismatched_bundle_executable_metadata(tmp_path):
    from tools.install_studio_app import install_studio_app

    source = _app(
        tmp_path / "build/Codex Media Studio.app",
        b"other",
        bundle_executable="NotCodexStudio",
    )
    destination = tmp_path / "Applications/Codex Media Studio.app"

    with pytest.raises(ValueError, match="bundle executable"):
        install_studio_app(
            source,
            destination,
            backup_root=tmp_path / "backups",
            running_check=lambda _: False,
        )

    assert not destination.exists()


def test_first_install_creates_canonical_bundle_without_a_backup(tmp_path):
    from tools.install_studio_app import install_studio_app

    source = _app(tmp_path / "build/Codex Media Studio.app", b"first")
    destination = tmp_path / "Applications/Codex Media Studio.app"
    backups = tmp_path / "backups"

    install_studio_app(
        source,
        destination,
        backup_root=backups,
        running_check=lambda _: False,
    )

    assert (destination / "Contents/MacOS/CodexStudio").read_bytes() == b"first"
    assert not backups.exists()


def test_first_install_also_refuses_while_a_development_bundle_is_running(tmp_path):
    from tools.install_studio_app import install_studio_app

    source = _app(tmp_path / "build/Codex Media Studio.app", b"first")
    destination = tmp_path / "Applications/Codex Media Studio.app"

    with pytest.raises(RuntimeError, match="Quit Codex Media Studio"):
        install_studio_app(
            source,
            destination,
            backup_root=tmp_path / "backups",
            running_check=lambda _: True,
        )

    assert not destination.exists()


def test_install_rejects_a_symlink_destination(tmp_path):
    from tools.install_studio_app import install_studio_app

    source = _app(tmp_path / "build/Codex Media Studio.app", b"new")
    actual = _app(tmp_path / "elsewhere/Codex Media Studio.app", b"old")
    destination = tmp_path / "Applications/Codex Media Studio.app"
    destination.parent.mkdir()
    destination.symlink_to(actual, target_is_directory=True)

    with pytest.raises(ValueError, match="not a symlink"):
        install_studio_app(
            source,
            destination,
            backup_root=tmp_path / "backups",
            running_check=lambda _: False,
        )

    assert (actual / "Contents/MacOS/CodexStudio").read_bytes() == b"old"


def test_backup_collision_preserves_installed_app_and_existing_backup(tmp_path):
    from tools.install_studio_app import install_studio_app

    source = _app(tmp_path / "build/Codex Media Studio.app", b"new")
    destination = _app(tmp_path / "Applications/Codex Media Studio.app", b"old")
    backups = tmp_path / "backups"
    collision = backups / "Codex Media Studio-20260908-120000.app-backup"
    collision.mkdir(parents=True)
    marker = collision / "keep.txt"
    marker.write_text("existing backup")

    with pytest.raises(FileExistsError, match="Backup already exists"):
        install_studio_app(
            source,
            destination,
            backup_root=backups,
            running_check=lambda _: False,
            timestamp="20260908-120000",
        )

    assert marker.read_text() == "existing backup"
    assert (destination / "Contents/MacOS/CodexStudio").read_bytes() == b"old"


def test_install_rejects_backup_storage_nested_inside_the_app(tmp_path):
    from tools.install_studio_app import install_studio_app

    source = _app(tmp_path / "build/Codex Media Studio.app", b"new")
    destination = _app(tmp_path / "Applications/Codex Media Studio.app", b"old")

    with pytest.raises(ValueError, match="must not overlap"):
        install_studio_app(
            source,
            destination,
            backup_root=destination / "Backups",
            running_check=lambda _: False,
        )

    assert (destination / "Contents/MacOS/CodexStudio").read_bytes() == b"old"


def test_install_aborts_if_studio_launches_during_staging(tmp_path):
    from tools.install_studio_app import install_studio_app

    source = _app(tmp_path / "build/Codex Media Studio.app", b"new")
    destination = _app(tmp_path / "Applications/Codex Media Studio.app", b"old")
    checks = iter((False, False, True))

    with pytest.raises(RuntimeError, match="Quit Codex Media Studio"):
        install_studio_app(
            source,
            destination,
            backup_root=tmp_path / "backups",
            running_check=lambda _: next(checks),
        )

    assert (destination / "Contents/MacOS/CodexStudio").read_bytes() == b"old"
    assert sorted(item.name for item in destination.iterdir()) == ["Contents"]


def test_failed_post_install_signature_check_restores_previous_contents(tmp_path, monkeypatch):
    import tools.install_studio_app as installer

    source = _app(tmp_path / "build/Codex Media Studio.app", b"new")
    destination = _app(tmp_path / "Applications/Codex Media Studio.app", b"old")
    checks = iter((None, ValueError("copied bundle failed verification")))

    def verify(app):
        result = next(checks)
        if result:
            assert sorted(item.name for item in app.iterdir()) == ["Contents"]
            raise result

    monkeypatch.setattr(installer, "_verify_signature", verify)
    with pytest.raises(ValueError, match="copied bundle failed verification"):
        installer.install_studio_app(
            source,
            destination,
            backup_root=tmp_path / "backups",
            running_check=lambda _: False,
            verify_signature=True,
        )

    assert (destination / "Contents/MacOS/CodexStudio").read_bytes() == b"old"


def test_bundle_rebuild_preserves_outer_directory_for_persistent_dock_aliases(tmp_path):
    from tools.build_studio_app import assemble

    executable = tmp_path / "binary"
    executable.write_bytes(b"first")
    executable.chmod(0o755)
    engine = tmp_path / "engine"
    (engine / "tools").mkdir(parents=True)
    (engine / "tools/studio.py").write_text("fixture")
    output = tmp_path / "Codex Media Studio.app"

    assemble(executable, engine, output, sign=False)
    original_inode = output.stat().st_ino
    executable.write_bytes(b"second")
    assemble(executable, engine, output, sign=False)

    assert output.stat().st_ino == original_inode
    assert (output / "Contents/MacOS/CodexStudio").read_bytes() == b"second"
