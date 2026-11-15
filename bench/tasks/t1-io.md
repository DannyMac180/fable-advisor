Add file import/export to the `inventory` library, with unit tests for each part under `tests/`.

1. `inventory/csv_io.py`:
   - `export_csv(store, path)` writes a CSV with header `sku,name,quantity,price_cents,tags`, one row per item in SKU order, tags joined with `;`.
   - `import_csv(path) -> InventoryStore` reads that format back. An invalid data row (missing column, non-integer number, negative value, empty sku or name, duplicate sku) raises `ValueError` whose message contains `line N`, N being the 1-based line number in the file (the header is line 1).
2. `inventory/json_io.py`:
   - `export_json(store, path)` writes a JSON array of `Item.to_dict()` objects in SKU order.
   - `import_json(path) -> InventoryStore`. An invalid entry raises `ValueError` whose message contains `index N` (0-based position in the array).
3. Export both modules' functions from `inventory/__init__.py`.

Use only the standard library. Verification: `python3 -m unittest -v` passes.
