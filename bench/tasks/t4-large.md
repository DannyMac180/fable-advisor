This is a larger change with four independent parts. Implement all four in the `inventory` library, each with unit tests under `tests/`.

## Part A — file import/export
1. `inventory/csv_io.py`:
   - `export_csv(store, path)` writes a CSV with header `sku,name,quantity,price_cents,tags`, one row per item in SKU order, tags joined with `;`.
   - `import_csv(path) -> InventoryStore` reads that format back. An invalid data row (missing column, non-integer number, negative value, empty sku or name, duplicate sku) raises `ValueError` whose message contains `line N`, N being the 1-based line number in the file (the header is line 1).
2. `inventory/json_io.py`:
   - `export_json(store, path)` writes a JSON array of `Item.to_dict()` objects in SKU order.
   - `import_json(path) -> InventoryStore`. An invalid entry raises `ValueError` whose message contains `index N` (0-based position in the array).
3. Export both modules' functions from `inventory/__init__.py`.


## Part B — querying and reporting
1. `query(tag=None, min_quantity=None, max_quantity=None, name_contains=None, sort_by="sku", descending=False, limit=None, offset=0) -> list[Item]`:
   - `tag` matches case-insensitively; `name_contains` is a case-insensitive substring match; quantity bounds are inclusive.
   - `sort_by` is one of `sku`, `name`, `quantity`, `price_cents`, with ties broken by sku ascending (also when `descending=True`); any other value raises `ValueError`.
   - `offset` then `limit` are applied after sorting; a negative `limit` or `offset` raises `ValueError`.
2. `total_value(tag=None) -> int`: the sum of `quantity * price_cents` over items, optionally only those with the tag (case-insensitive).
3. `low_stock(threshold) -> list[Item]`: items with `quantity <= threshold`, sorted by quantity, then sku. A negative threshold raises `ValueError`.

Keep `list()` unchanged.

## Part C — command-line interface
1. `inventory/cli.py` exposes `main(argv: list[str]) -> int`. Usage: `python -m inventory --db PATH <command> ...`. The database is a JSON file holding an array of `Item.to_dict()` objects; a missing file means an empty store, and every command that changes the store saves it back.
2. Commands:
   - `add SKU NAME [--quantity N] [--price-cents N] [--tag T]...`
   - `remove SKU`
   - `adjust SKU DELTA` (DELTA may be negative)
   - `list [--tag T]` prints one line per item in SKU order: `SKU<TAB>NAME<TAB>QUANTITY`
   - `value` prints the total of `quantity * price_cents` as an integer
3. On success, return 0. On an error (unknown SKU, duplicate SKU, invalid value, quantity going negative), print a one-line message starting with `error:` to stderr, leave the database file unchanged, and return 1.
4. Add `inventory/__main__.py` so that `python -m inventory` calls `main(sys.argv[1:])` and exits with its return code.


## Part D — reservations
1. `inventory/reservations.py` defines `ReservationBook(store)`, which holds reservations against an `InventoryStore` without changing item quantities.
   - `reserve(sku, quantity, holder, now, ttl_seconds=3600) -> str` returns a new unique reservation id. It raises `NotFoundError` for an unknown SKU, and `ValueError` if `quantity <= 0`, `ttl_seconds <= 0`, or `quantity` exceeds `available(sku, now)`.
   - `release(reservation_id) -> None` raises `KeyError` for an unknown id.
   - `available(sku, now) -> int` is the item quantity minus all unexpired reservations for that SKU. A reservation is expired when `now >= created + ttl_seconds`.
   - `reservations_for(holder, now) -> list[dict]` returns that holder's unexpired reservations as dicts with keys `id`, `sku`, `quantity`, `expires_at`, sorted by `expires_at` then `id`.
   - `expire(now) -> int` removes expired reservations and returns how many it removed.
   - `now` is a number of seconds (an int or a float), passed in by the caller. Don't read the clock.
2. Export `ReservationBook` from `inventory/__init__.py`.

Use only the standard library. Verification: `python3 -m unittest -v` passes.
