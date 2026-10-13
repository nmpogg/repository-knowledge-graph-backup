"""Generate scanner-only input; generated files are never imported or executed."""

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / ".benchmark" / "corpus"


def generate(count, seed=2026):
    if count not in {100, 1000, 9000}:
        raise ValueError("unsupported_count")
    if OUTPUT.exists() or OUTPUT.parent.is_symlink():
        raise ValueError("output_exists_or_unsafe_parent")
    OUTPUT.mkdir(parents=True)
    for i in range(count):
        name = f"fixture_{i:05d}"
        # Constant templates contain no config, credentials, imports or effects.
        source = (
            f"// Scanner corpus seed {seed}\n"
            f"export function {name}(): number {{ return {i}; }}\n"
        )
        (OUTPUT / f"{name}.ts").write_text(source)
    (OUTPUT / "manifest.json").write_text(json.dumps({"count": count, "seed": seed}))


def cleanup():
    if OUTPUT.is_symlink() or OUTPUT.parent.is_symlink():
        raise ValueError("unsafe_output")
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, choices=[100, 1000, 9000], default=100)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--cleanup", action="store_true")
    args = parser.parse_args()
    if args.cleanup:
        cleanup()
    else:
        generate(args.count, args.seed)


if __name__ == "__main__":
    main()
