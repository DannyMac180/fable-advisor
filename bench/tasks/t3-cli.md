Add a command-line interface to the `inventory` library, with unit tests under `tests/`.

1. `inventory/cli.py` exposes `main(argv: list[str]) -> int`. Usage: `python -m inventory --db PATH <command> ...`. The database is a JSON file holding an array of `Item.to_dict()` objects; a missing file means an empty store, and every command that changes the store saves it back.
2. Commands:
   - `add SKU NAME [--quantity N] [--price-cents N] [--tag T]...`
   - `remove SKU`
   - `adjust SKU DELTA` (DELTA may be negative)
   - `list [--tag T]` prints one line per item in SKU order: `SKU<TAB>NAME<TAB>QUANTITY`
   - `value` prints the total of `quantity * price_cents` as an integer
3. On success, return 0. On an error (unknown SKU, duplicate SKU, invalid value, quantity going negative), print a one-line message starting with `error:` to stderr, leave the database file unchanged, and return 1.
4. Add `inventory/__main__.py` so that `python -m inventory` calls `main(sys.argv[1:])` and exits with its return code.

Use only the standard library (`argparse`, `json`). Verification: `python3 -m unittest -v` passes.
