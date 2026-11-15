from .models import Item


class NotFoundError(KeyError):
    pass


class InventoryStore:
    def __init__(self, items=None):
        self._items: dict[str, Item] = {}
        for item in items or []:
            self.add(item)

    def add(self, item: Item) -> None:
        if item.sku in self._items:
            raise ValueError(f"duplicate sku {item.sku}")
        self._items[item.sku] = item

    def get(self, sku: str) -> Item:
        try:
            return self._items[sku]
        except KeyError:
            raise NotFoundError(sku) from None

    def remove(self, sku: str) -> Item:
        item = self.get(sku)
        del self._items[sku]
        return item

    def adjust(self, sku: str, delta: int) -> Item:
        item = self.get(sku)
        if item.quantity + delta < 0:
            raise ValueError("quantity would go negative")
        item.quantity += delta
        return item

    def list(self) -> list[Item]:
        return sorted(self._items.values(), key=lambda i: i.sku)

    def __len__(self) -> int:
        return len(self._items)
