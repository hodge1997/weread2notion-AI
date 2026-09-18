from argparse import Namespace

from weread2notion.cli import build_parser


def test_dry_run_flag_is_available_without_notion_command_changes():
    args = build_parser().parse_args(["sync", "--dry-run"])
    assert isinstance(args, Namespace)
    assert args.command == "sync"
    assert args.dry_run is True


def test_summary_file_flag_is_available():
    args = build_parser().parse_args(["sync", "--summary-file", "summary.json"])
    assert args.summary_file == "summary.json"


def test_export_command_parser():
    args = build_parser().parse_args(["export", "--format", "markdown", "--output", "out"])
    assert args.command == "export"
    assert args.format == "markdown"
    assert args.output == "out"
