import unittest

from inventory import InventoryStore, Item, NotFoundError


class TestStore(unittest.TestCase):
    def setUp(self):
        self.store = InventoryStore([
            Item("B-2", "Bolt", 10, 25, ["Hardware"]),
            Item("A-1", "Anvil", 1, 9900, ["heavy", "hardware"]),
        ])

    def test_list_sorted_by_sku(self):
        self.assertEqual([i.sku for i in self.store.list()], ["A-1", "B-2"])

    def test_tags_normalized(self):
        self.assertEqual(self.store.get("B-2").tags, ["hardware"])

    def test_adjust_and_remove(self):
        self.store.adjust("B-2", -4)
        self.assertEqual(self.store.get("B-2").quantity, 6)
        with self.assertRaises(ValueError):
            self.store.adjust("B-2", -7)
        self.store.remove("A-1")
        with self.assertRaises(NotFoundError):
            self.store.get("A-1")

    def test_duplicate_sku(self):
        with self.assertRaises(ValueError):
            self.store.add(Item("A-1", "Again"))


if __name__ == "__main__":
    unittest.main()
