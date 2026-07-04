#!/usr/bin/env python3
"""
view_circuit.py — turn a Verilog file into a schematic and open it.

Usage:
    python view_circuit.py path/to/file.v
    python view_circuit.py path/to/file.v --top my_module
    python view_circuit.py path/to/file.v --synth        # full gate-level view
    python view_circuit.py a.v b.v --top top_module       # multiple files

Requires (already in pyproject.toml): yowasp-yosys
Requires on the system: graphviz's `dot` command
    sudo apt install graphviz   # if you don't have it yet

By default this shows the RTL-level view (multiplier/adder/register blocks,
readable). Pass --synth for the fully technology-mapped gate-level netlist
(accurate, but usually a lot less readable — useful once you actually care
about gate count / area).
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path


def guess_top_module(verilog_files: list[Path]) -> str:
    """Find the first `module <name>` declaration across the given files."""
    pattern = re.compile(r"\bmodule\s+(\w+)")
    for f in verilog_files:
        text = f.read_text()
        match = pattern.search(text)
        if match:
            return match.group(1)
    raise RuntimeError(
        "Could not find any 'module <name>' declaration. "
        "Pass --top <name> explicitly."
    )


def run_yosys(verilog_files: list[Path], top: str, out_prefix: Path, synth: bool) -> Path:
    files_str = " ".join(str(f) for f in verilog_files)

    if synth:
        script = f"""
        read_verilog {files_str};
        synth -top {top};
        show -format dot -prefix {out_prefix}
        """
    else:
        script = f"""
        read_verilog {files_str};
        hierarchy -top {top};
        proc;
        opt_clean;
        show -format dot -prefix {out_prefix}
        """

    result = subprocess.run(
        ["yowasp-yosys", "-p", script],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise RuntimeError("yosys failed, see output above")

    dot_file = out_prefix.with_suffix(".dot")
    if not dot_file.exists():
        raise RuntimeError(f"Expected {dot_file} but it wasn't created")
    return dot_file


def dot_to_svg(dot_file: Path) -> Path:
    svg_file = dot_file.with_suffix(".svg")
    result = subprocess.run(
        ["dot", "-Tsvg", str(dot_file), "-o", str(svg_file)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        raise RuntimeError(
            "`dot` failed. Is graphviz installed? Try: sudo apt install graphviz"
        )
    return svg_file


def open_file(path: Path) -> None:
    if sys.platform.startswith("linux"):
        subprocess.run(["xdg-open", str(path)])
    elif sys.platform == "darwin":
        subprocess.run(["open", str(path)])
    elif sys.platform == "win32":
        import os
        os.startfile(str(path))  # type: ignore[attr-defined]
    else:
        import webbrowser
        webbrowser.open(path.resolve().as_uri())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("verilog_files", nargs="+", type=Path, help="One or more .v files")
    parser.add_argument("--top", default=None, help="Top module name (auto-detected if omitted)")
    parser.add_argument("--synth", action="store_true", help="Show full gate-level netlist instead of RTL blocks")
    parser.add_argument("--out-dir", type=Path, default=None, help="Where to write .dot/.svg (default: next to first input file)")
    args = parser.parse_args()

    for f in args.verilog_files:
        if not f.exists():
            sys.exit(f"error: file not found: {f}")

    top = args.top or guess_top_module(args.verilog_files)
    out_dir = args.out_dir or args.verilog_files[0].parent
    out_dir.mkdir(parents=True, exist_ok=True)
    out_prefix = out_dir / f"{top}_schematic"

    print(f"Top module : {top}")
    print(f"Mode       : {'gate-level (synth)' if args.synth else 'RTL blocks'}")

    dot_file = run_yosys(args.verilog_files, top, out_prefix, args.synth)
    svg_file = dot_to_svg(dot_file)

    print(f"Schematic  : {svg_file}")
    open_file(svg_file)


if __name__ == "__main__":
    main()