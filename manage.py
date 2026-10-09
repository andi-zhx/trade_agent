"""Offline maintenance. Restore never imports or initializes the current app."""
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="企业资料库维护工具")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init-db", help="初始化或兼容迁移数据库，不清空资料")
    backup = commands.add_parser("backup", help="生成含数据库与附件的完整资料包")
    backup.add_argument("--output", required=True, type=Path)
    restore = commands.add_parser("restore", help="校验并恢复到一个尚不存在的新目录")
    restore.add_argument("archive", type=Path)
    restore.add_argument("--to", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "restore":
        from backup_service import restore_bundle
        result = restore_bundle(args.archive, args.to)
        print(f"校验与恢复完成：{result}。停服后切换 TRADE_DATA_DIR，验证资料后再恢复使用。")
        return
    from app import app, init_db
    init_db(app)
    if args.command == "backup":
        from backup_service import create_bundle
        with app.app_context():
            if args.output.exists():
                raise SystemExit("目标文件已存在，请使用新文件名。")
            create_bundle(app, args.output)
        print(f"完整资料包已生成：{args.output}")
    else:
        print("数据库初始化完成。")


if __name__ == "__main__":
    main()
