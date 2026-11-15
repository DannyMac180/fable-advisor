import unittest
from accept_t1 import AcceptT1  # noqa: F401
from accept_t2 import AcceptT2  # noqa: F401
from accept_t3 import AcceptT3  # noqa: F401
from inventory import InventoryStore, Item, NotFoundError


class AcceptT4Reservations(unittest.TestCase):
    def book(self):
        from inventory import ReservationBook
        store = InventoryStore([Item("A-1", "Anvil", 5, 100), Item("B-2", "Bolt", 2, 5)])
        return store, ReservationBook(store)

    def test_reserve_and_available(self):
        store, b = self.book()
        r1 = b.reserve("A-1", 3, "ann", now=0, ttl_seconds=10)
        self.assertEqual(b.available("A-1", now=1), 2)
        self.assertEqual(store.get("A-1").quantity, 5)
        with self.assertRaises(ValueError):
            b.reserve("A-1", 3, "bob", now=1)
        r2 = b.reserve("A-1", 2, "bob", now=1)
        self.assertNotEqual(r1, r2)
        self.assertEqual(b.available("A-1", now=10), 3)  # r1 expired at now >= 10
        b.release(r2)
        self.assertEqual(b.available("A-1", now=10), 5)
        with self.assertRaises(KeyError):
            b.release(r2)

    def test_errors(self):
        _, b = self.book()
        with self.assertRaises(NotFoundError):
            b.reserve("Z-9", 1, "ann", now=0)
        for kw in [dict(quantity=0), dict(quantity=1, ttl_seconds=0)]:
            args = dict(sku="B-2", holder="ann", now=0, quantity=kw.pop("quantity"))
            with self.assertRaises(ValueError):
                b.reserve(**args, **kw)

    def test_listing_and_expire(self):
        _, b = self.book()
        late = b.reserve("A-1", 1, "ann", now=0, ttl_seconds=50)
        early = b.reserve("B-2", 1, "ann", now=0, ttl_seconds=20)
        b.reserve("A-1", 1, "bob", now=0, ttl_seconds=5)
        rows = b.reservations_for("ann", now=1)
        self.assertEqual([r["id"] for r in rows], [early, late])
        self.assertEqual(set(rows[0]), {"id", "sku", "quantity", "expires_at"})
        self.assertEqual(rows[0]["expires_at"], 20)
        self.assertEqual(b.expire(now=20), 2)
        self.assertEqual([r["id"] for r in b.reservations_for("ann", now=20)], [late])


if __name__ == "__main__":
    unittest.main()
