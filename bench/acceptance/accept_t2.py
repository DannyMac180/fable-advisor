import unittest
from inventory import InventoryStore, Item


def store():
    return InventoryStore([
        Item("D-4", "drill", 3, 5000, ["Power", "tools"]),
        Item("B-2", "Bolt", 10, 25, ["hardware"]),
        Item("A-1", "Anvil", 1, 9900, ["heavy", "hardware"]),
        Item("C-3", "bolt cutter", 3, 2500, ["tools"]),
    ])


class AcceptT2(unittest.TestCase):
    def skus(self, items):
        return [i.sku for i in items]

    def test_filters(self):
        s = store()
        self.assertEqual(self.skus(s.query(tag="HARDWARE")), ["A-1", "B-2"])
        self.assertEqual(self.skus(s.query(name_contains="BOLT")), ["B-2", "C-3"])
        self.assertEqual(self.skus(s.query(min_quantity=3, max_quantity=3)), ["C-3", "D-4"])

    def test_sort_ties_and_paging(self):
        s = store()
        self.assertEqual(self.skus(s.query(sort_by="quantity")), ["A-1", "C-3", "D-4", "B-2"])
        self.assertEqual(self.skus(s.query(sort_by="quantity", descending=True)), ["B-2", "C-3", "D-4", "A-1"])
        self.assertEqual(self.skus(s.query(sort_by="price_cents", limit=2, offset=1)), ["C-3", "D-4"])
        self.assertEqual(self.skus(s.query(sort_by="name")), ["A-1", "B-2", "C-3", "D-4"])
        for bad in [dict(sort_by="weight"), dict(limit=-1), dict(offset=-1)]:
            with self.assertRaises(ValueError):
                s.query(**bad)

    def test_value_and_low_stock(self):
        s = store()
        self.assertEqual(s.total_value(), 3 * 5000 + 10 * 25 + 9900 + 3 * 2500)
        self.assertEqual(s.total_value(tag="Tools"), 3 * 5000 + 3 * 2500)
        self.assertEqual(self.skus(s.low_stock(3)), ["A-1", "C-3", "D-4"])
        with self.assertRaises(ValueError):
            s.low_stock(-1)
        self.assertEqual(self.skus(s.list()), ["A-1", "B-2", "C-3", "D-4"])


if __name__ == "__main__":
    unittest.main()
