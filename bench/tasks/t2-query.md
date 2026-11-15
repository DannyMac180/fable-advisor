Add querying and reporting to `InventoryStore` in `inventory/store.py`, with unit tests for each part under `tests/`.

1. `query(tag=None, min_quantity=None, max_quantity=None, name_contains=None, sort_by="sku", descending=False, limit=None, offset=0) -> list[Item]`:
   - `tag` matches case-insensitively; `name_contains` is a case-insensitive substring match; quantity bounds are inclusive.
   - `sort_by` is one of `sku`, `name`, `quantity`, `price_cents`, with ties broken by sku ascending (also when `descending=True`); any other value raises `ValueError`.
   - `offset` then `limit` are applied after sorting; a negative `limit` or `offset` raises `ValueError`.
2. `total_value(tag=None) -> int`: the sum of `quantity * price_cents` over items, optionally only those with the tag (case-insensitive).
3. `low_stock(threshold) -> list[Item]`: items with `quantity <= threshold`, sorted by quantity, then sku. A negative threshold raises `ValueError`.

Keep `list()` unchanged. Verification: `python3 -m unittest -v` passes.
