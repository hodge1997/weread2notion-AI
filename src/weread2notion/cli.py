from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import ConfigError, Settings
from .export import export_weread
from .notion import NotionWorkspace
from .sync import Synchronizer
from .weread import WeReadClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="weread2notion")
    sub = parser.add_subparsers(dest="command")
    sync = sub.add_parser("sync", help="同步微信读书数据，保留 Notion 页面结构")
    sync.add_argument("--full", action="store_true", help="备份并重建全部数据库行")
    sync.add_argument(
        "--dry-run", action="store_true", help="只读取微信数据并显示同步计划"
    )
    sync.add_argument(
        "--summary-file",
        help="将最终同步结果写入 JSON 文件，供 CI 摘要使用",
    )
    sub.add_parser("check", help="检查模板数据库与属性")
    export = sub.add_parser("export", help="导出微信读书书架数据")
    export.add_argument("--format", choices=("json", "markdown"), default="json")
    export.add_argument("--output", default="weread-export")
    return parser


def main(argv=None) -> None:
    args = build_parser().parse_args(argv)
    command = args.command or "sync"
    try:
        settings = Settings.from_env()
        weread = WeReadClient(settings.weread_api_key, settings.skill_version)
        if command == "export":
            print(json.dumps(export_weread(weread, args.output, args.format), ensure_ascii=False, indent=2))
            return
        if command == "sync" and getattr(args, "dry_run", False):
            result = Synchronizer(weread, None, settings.start_year, dry_run=True).run()
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return
        notion = NotionWorkspace(
            settings.notion_token,
            settings.notion_page_id,
            settings.notion_version,
            settings.request_interval,
        ).discover()
        preferences = notion.ensure_sync_settings(settings.start_year)
        notion.ensure_reading_snapshots()
        if command == "check":
            print(
                json.dumps(
                    {
                        "databases": notion.databases,
                        "schemas": notion.schemas,
                        "settings": {
                            key: value
                            for key, value in preferences.items()
                            if not key.startswith("_")
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return
        result = Synchronizer(
            weread,
            notion,
            settings.start_year,
            dry_run=False,
            preferences=preferences,
        ).run(
            full=getattr(args, "full", False),
            backup_dir=settings.backup_dir,
        )
        notion.mark_sync_settings_applied(
            preferences.get("_page_id"),
            preferences.get("_config_code", 0),
            preferences.get("_config_property", "同步配置版本（不可删除）"),
        )
        summary_file = getattr(args, "summary_file", None)
        if summary_file:
            summary_path = Path(summary_file)
            if summary_path.suffix.lower() != ".json" or ".." in summary_path.parts:
                raise SystemExit("summary-file 必须是不含父目录穿越的 .json 路径")
            summary_path.parent.mkdir(parents=True, exist_ok=True)
            with summary_path.open("w", encoding="utf-8") as handle:
                json.dump(result, handle, ensure_ascii=False, indent=2)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except ConfigError as exc:
        raise SystemExit(f"配置错误：{exc}") from exc


if __name__ == "__main__":
    main()
