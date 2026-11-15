from dataclasses import dataclass, field


@dataclass
class Item:
    sku: str
    name: str
    quantity: int = 0
    price_cents: int = 0
    tags: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.sku or not self.sku.strip():
            raise ValueError("sku must be non-empty")
        if not self.name or not self.name.strip():
            raise ValueError("name must be non-empty")
        if self.quantity < 0:
            raise ValueError("quantity must be >= 0")
        if self.price_cents < 0:
            raise ValueError("price_cents must be >= 0")
        self.tags = sorted({t.strip().lower() for t in self.tags if t.strip()})

    def to_dict(self) -> dict:
        return {
            "sku": self.sku,
            "name": self.name,
            "quantity": self.quantity,
            "price_cents": self.price_cents,
            "tags": list(self.tags),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Item":
        return cls(
            sku=data["sku"],
            name=data["name"],
            quantity=int(data.get("quantity", 0)),
            price_cents=int(data.get("price_cents", 0)),
            tags=list(data.get("tags", [])),
        )
