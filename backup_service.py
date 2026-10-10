"""Consistent SQLite snapshots and validated, non-destructive offline restore."""
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sqlite3
import tempfile
from zipfile import ZIP_DEFLATED, ZipFile

from models import db


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sqlite_snapshot(source, destination):
    source, destination = Path(source), Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".partial")
    try:
        with closing(sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True, timeout=30)) as src:
            with closing(sqlite3.connect(temporary)) as dst:
                src.backup(dst)
                if dst.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise ValueError("数据库备份完整性检查失败")
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def create_bundle(app, destination):
    """Snapshot DB first; uploads are append-only, including soft-deleted files."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    data_root = Path(app.config["DATA_ROOT"])
    with tempfile.TemporaryDirectory(dir=destination.parent) as temp:
        staging = Path(temp)
        database = staging / "trade_agent.db"
        sqlite_snapshot(db.engine.url.database, database)
        with closing(sqlite3.connect(database)) as connection:
            references = [row[0] for row in connection.execute("SELECT file_path FROM documents") if row[0]]
        for reference in references:
            path = data_root / reference
            if not path.resolve().is_relative_to((data_root / "uploads").resolve()) or not path.is_file():
                raise ValueError("有附件缺失或路径不合法，完整备份未生成，请检查附件目录。")
        manifest = {"format": 1, "created_at": datetime.now(timezone.utc).isoformat(), "sha256": {}}
        archive = staging / "bundle.zip"
        files = [(database, "trade_agent.db")]
        files += [(p, p.relative_to(data_root).as_posix()) for p in sorted((data_root / "uploads").rglob("*")) if p.is_file()]
        with ZipFile(archive, "w", compression=ZIP_DEFLATED) as bundle:
            for path, name in files:
                if path.is_symlink() or (name != "trade_agent.db" and not path.resolve().is_relative_to(data_root.resolve())):
                    raise ValueError("附件目录不得包含外部链接")
                digest = hashlib.sha256()
                with path.open("rb") as source, bundle.open(name, "w") as output:
                    for chunk in iter(lambda: source.read(1024 * 1024), b""):
                        output.write(chunk)
                        digest.update(chunk)
                manifest["sha256"][name] = digest.hexdigest()
            bundle.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        os.replace(archive, destination)
    return destination


def restore_bundle(archive, destination):
    """Restore only to a new directory; never replace a running or existing DB."""
    destination = Path(destination).resolve()
    if destination.exists():
        raise ValueError("恢复目标必须是尚不存在的新目录；不会覆盖已有资料。")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as temp:
        staging = Path(temp) / "restored"
        staging.mkdir()
        with ZipFile(archive) as bundle:
            names = bundle.namelist()
            if len(names) != len(set(names)):
                raise ValueError("备份包含重复路径")
            manifest = json.loads(bundle.read("manifest.json"))
            if manifest.get("format") != 1 or "trade_agent.db" not in manifest.get("sha256", {}):
                raise ValueError("不支持的备份格式")
            hashes = manifest["sha256"]
            if set(names) != set(hashes) | {"manifest.json"}:
                raise ValueError("备份文件清单不一致")
            for name, expected_hash in hashes.items():
                relative = PurePosixPath(name)
                if relative.is_absolute() or ".." in relative.parts or "\\" in name or not (name == "trade_agent.db" or name.startswith("uploads/")):
                    raise ValueError("备份包含非法路径")
                target = staging / name
                target.parent.mkdir(parents=True, exist_ok=True)
                with bundle.open(name) as source, target.open("xb") as output:
                    shutil.copyfileobj(source, output)
                if file_hash(target) != expected_hash:
                    raise ValueError("备份文件校验失败")
        with closing(sqlite3.connect(staging / "trade_agent.db")) as connection:
            if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("恢复数据库完整性检查失败")
            for (reference,) in connection.execute("SELECT file_path FROM documents"):
                if reference:
                    target = staging / reference
                    if not target.resolve().is_relative_to((staging / "uploads").resolve()) or not target.is_file():
                        raise ValueError("恢复资料缺少数据库引用的附件")
        staging.rename(destination)
    return destination
