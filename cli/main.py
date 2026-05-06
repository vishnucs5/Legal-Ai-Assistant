from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

try:
    import typer
    from rich.console import Console
except ModuleNotFoundError:
    typer = None
    Console = None

from core.comparator import ContractComparator
from pipeline.pipeline import LegalAnalysisPipeline
from pipeline.stages import AnalysisConfig
from utils.output_formatter import OutputFormatter

console = Console() if Console else None
app = typer.Typer(help="Legal AI Assistant contract analysis CLI") if typer else None


def _print(value: str) -> None:
    if console:
        console.print(value)
    else:
        print(value)


def _print_json(data: dict) -> None:
    if console:
        console.print_json(data=data)
    else:
        print(json.dumps(data, indent=2, default=str))


def _run_analyze(input_file: Path, contract_type: str, jurisdiction: str, depth: str, output: str, stream: bool) -> None:
    config = AnalysisConfig(contract_type=contract_type, jurisdiction=jurisdiction, depth=depth, output=output)
    pipeline = LegalAnalysisPipeline()
    if stream:
        asyncio.run(_stream(pipeline, input_file, config))
    else:
        report = asyncio.run(pipeline.run(input_file, config))
        _print(OutputFormatter().format(report, output))


def _run_compare(old_file: Path, new_file: Path, contract_type: str, jurisdiction: str, show_diff: bool) -> None:
    config = AnalysisConfig(contract_type=contract_type, jurisdiction=jurisdiction)
    pipeline = LegalAnalysisPipeline()
    old_report = asyncio.run(pipeline.run(old_file, config))
    new_report = asyncio.run(pipeline.run(new_file, config))
    result = ContractComparator().compare(old_report.clauses, new_report.clauses)
    if not show_diff:
        for item in result["changed_clauses"]:
            item.pop("diff", None)
    _print_json(result)


async def _stream(pipeline: LegalAnalysisPipeline, input_file: Path, config: AnalysisConfig) -> None:
    async for event in pipeline.stream(input_file, config):
        _print(event.rstrip())


if typer:

    @app.command()
    def analyze(
        input_file: Path,
        contract_type: str = typer.Option("unknown", "--type"),
        jurisdiction: str = typer.Option(""),
        depth: str = typer.Option("standard"),
        output: str = typer.Option("json"),
        stream: bool = typer.Option(False),
    ) -> None:
        _run_analyze(input_file, contract_type, jurisdiction, depth, output, stream)

    @app.command()
    def compare(
        old_file: Path,
        new_file: Path,
        contract_type: str = typer.Option("unknown", "--type"),
        jurisdiction: str = typer.Option(""),
        show_diff: bool = typer.Option(False),
    ) -> None:
        _run_compare(old_file, new_file, contract_type, jurisdiction, show_diff)


def _argparse_main() -> None:
    parser = argparse.ArgumentParser(description="Legal AI Assistant contract analysis CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("input_file", type=Path)
    analyze_parser.add_argument("--type", dest="contract_type", default="unknown")
    analyze_parser.add_argument("--jurisdiction", default="")
    analyze_parser.add_argument("--depth", default="standard")
    analyze_parser.add_argument("--output", default="json")
    analyze_parser.add_argument("--stream", action="store_true")

    compare_parser = subparsers.add_parser("compare")
    compare_parser.add_argument("old_file", type=Path)
    compare_parser.add_argument("new_file", type=Path)
    compare_parser.add_argument("--type", dest="contract_type", default="unknown")
    compare_parser.add_argument("--jurisdiction", default="")
    compare_parser.add_argument("--show-diff", action="store_true")

    args = parser.parse_args()
    if args.command == "analyze":
        _run_analyze(args.input_file, args.contract_type, args.jurisdiction, args.depth, args.output, args.stream)
    else:
        _run_compare(args.old_file, args.new_file, args.contract_type, args.jurisdiction, args.show_diff)


if __name__ == "__main__":
    if app:
        app()
    else:
        _argparse_main()

