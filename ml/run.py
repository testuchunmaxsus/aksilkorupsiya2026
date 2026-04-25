"""
AuksionWatch CLI.

Ishlatish:
    python run.py data/Fergana.xlsx
    python run.py data/input.csv
    python run.py data/input.csv --out results/
    python run.py data/input.csv --out results/ --open
"""

import argparse
import os
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from scripts.core_pipeline import run_pipeline


def main():
    parser = argparse.ArgumentParser(
        description="AuksionWatch — CSV/Excel faylni tahlil qilish",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Misollar:
  python run.py data/Fergana.xlsx
  python run.py data/toshkent.csv --out results/toshkent/
  python run.py data/samarkand.xlsx --open
        """,
    )
    parser.add_argument("input", help="CSV yoki Excel fayl yo'li")
    parser.add_argument("--out", default="data", help="Natija papkasi (default: data/)")
    parser.add_argument("--open", action="store_true", help="Natijani avtomatik ochish")
    args = parser.parse_args()

    if not Path(args.input).exists():
        sys.stderr.write(f"Xato: fayl topilmadi: {args.input}\n")
        sys.exit(1)

    result = run_pipeline(
        input_path=args.input,
        output_dir=args.out,
        verbose=True,
    )

    stats = result["stats"]
    print("\n" + "=" * 50)
    print("NATIJA:")
    print(f"  Jami lot    : {stats['total']:,}")
    print(f"  KRITIK      : {stats['kritik']:,}")
    print(f"  YUQORI      : {stats['yuqori']:,}")
    print(f"  Score max   : {stats['score_max']}")
    print(f"  Predictions : {result['output_csv']}")
    print(f"  Hisobot     : {result['output_report']}")
    print("=" * 50)

    if args.open:
        csv_path = result["output_csv"]
        if sys.platform == "win32":
            os.startfile(csv_path)
        elif sys.platform == "darwin":
            subprocess.run(["open", csv_path])
        else:
            subprocess.run(["xdg-open", csv_path])


if __name__ == "__main__":
    main()
