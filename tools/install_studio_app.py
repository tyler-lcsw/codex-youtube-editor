"""Install one canonical Studio app without invalidating its persistent Dock alias."""

import argparse
from contextlib import contextmanager
from datetime import datetime
import fcntl
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import uuid


BUNDLE_ID = "local.tyler.codex-studio"
APP_NAME = "Codex Media Studio.app"


def _bundle_info(app):
    app = Path(app)
    info_path = app / "Contents/Info.plist"
    executable = app / "Contents/MacOS/CodexStudio"
    if (
        app.suffix != ".app"
        or not info_path.is_file()
        or not executable.is_file()
        or not os.access(executable, os.X_OK)
    ):
        raise ValueError(f"Not a complete {APP_NAME} bundle: {app}")
    info = plistlib.loads(info_path.read_bytes())
    if info.get("CFBundleIdentifier") != BUNDLE_ID:
        raise ValueError(f"Unexpected bundle identifier in {app}")
    if info.get("CFBundleExecutable") != "CodexStudio":
        raise ValueError(f"Unexpected bundle executable in {app}")
    return info


def studio_is_running(_destination):
    """Return true when any installed or development Studio bundle is running."""
    result = subprocess.run(
        ["pgrep", "-x", "CodexStudio"], capture_output=True, text=True, check=False
    )
    if result.returncode not in (0, 1):
        raise RuntimeError("Could not determine whether Codex Media Studio is running")
    return result.returncode == 0


def _backup_name(destination, timestamp):
    stem = Path(destination).stem
    return f"{stem}-{timestamp}.app-backup"


def _verify_signature(app):
    result = subprocess.run(
        ["codesign", "--verify", "--deep", "--strict", str(app)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or "verification failed"
        raise ValueError(f"Invalid application signature: {detail}")


def _paths_overlap(first, second):
    return first == second or first.is_relative_to(second) or second.is_relative_to(first)


@contextmanager
def _install_lock(parent):
    lock_path = parent / ".codex-media-studio-install.lock"
    with lock_path.open("a+") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def install_studio_app(
    source,
    destination,
    *,
    backup_root,
    running_check=studio_is_running,
    timestamp=None,
    verify_signature=False,
):
    """Install source while preserving the destination app directory itself.

    macOS Dock items may retain file identity in addition to a path. Replacing only
    Contents keeps a pinned canonical bundle attached to the current installation.
    Historical copies use a non-.app suffix outside Applications so LaunchServices
    does not present them as alternate installed versions.
    """
    source = Path(source).resolve()
    destination = Path(destination).expanduser()
    if destination.is_symlink():
        raise ValueError("Destination must be the canonical app directory, not a symlink")
    destination = destination.resolve()
    backup_root = Path(backup_root).resolve()
    _bundle_info(source)
    if verify_signature:
        _verify_signature(source)
    paths = (("source", source), ("destination", destination), ("backup", backup_root))
    for index, (first_name, first) in enumerate(paths):
        for second_name, second in paths[index + 1 :]:
            if _paths_overlap(first, second):
                raise ValueError(f"{first_name} and {second_name} paths must not overlap")
    if running_check(destination):
        raise RuntimeError("Quit Codex Media Studio before installing the latest build")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with _install_lock(destination.parent):
        if running_check(destination):
            raise RuntimeError("Quit Codex Media Studio before installing the latest build")
        if destination.exists():
            _bundle_info(destination)

        timestamp = timestamp or datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = backup_root / _backup_name(destination, timestamp)
        created_destination = not destination.exists()
        if not created_destination and backup.exists():
            raise FileExistsError(f"Backup already exists: {backup}")
        if created_destination:
            destination.mkdir()

        nonce = uuid.uuid4().hex
        backup_incoming = backup_root / f".{backup.name}.next-{nonce}"
        swap_prefix = f".{destination.name}.Contents"
        incoming = destination.parent / f"{swap_prefix}.next-{nonce}"
        previous = destination.parent / f"{swap_prefix}.previous-{nonce}"
        failed = destination.parent / f"{swap_prefix}.failed-{nonce}"
        current = destination / "Contents"
        swapped = False
        try:
            if not created_destination:
                backup_root.mkdir(parents=True, exist_ok=True)
                shutil.copytree(
                    destination,
                    backup_incoming,
                    symlinks=True,
                    copy_function=shutil.copy2,
                )
                backup_incoming.rename(backup)
            shutil.copytree(
                source / "Contents",
                incoming,
                symlinks=True,
                copy_function=shutil.copy2,
            )
            if running_check(destination):
                raise RuntimeError("Quit Codex Media Studio before installing the latest build")
            if current.exists():
                current.rename(previous)
            incoming.rename(current)
            swapped = True
            if verify_signature:
                _verify_signature(destination)
            shutil.rmtree(previous, ignore_errors=True)
        except BaseException:
            if swapped and previous.exists():
                current.rename(failed)
                previous.rename(current)
                shutil.rmtree(failed, ignore_errors=True)
            elif not current.exists() and previous.exists():
                previous.rename(current)
            shutil.rmtree(incoming, ignore_errors=True)
            shutil.rmtree(backup_incoming, ignore_errors=True)
            if created_destination:
                shutil.rmtree(destination, ignore_errors=True)
            raise
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument(
        "--destination",
        type=Path,
        default=Path.home() / "Applications" / APP_NAME,
    )
    parser.add_argument(
        "--backup-root",
        type=Path,
        default=Path.home()
        / "Library/Application Support/Codex Media Studio/Backups",
    )
    args = parser.parse_args()
    installed = install_studio_app(
        args.source,
        args.destination,
        backup_root=args.backup_root,
        verify_signature=True,
    )
    print(installed)


if __name__ == "__main__":
    main()
