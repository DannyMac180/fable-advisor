import json, os, tempfile, unittest
from inventory import InventoryStore, Item
from inventory.csv_io import export_csv, import_csv
from inventory.json_io import export_json, import_json


def sample():
    return InventoryStore([Item("B-2", "Bolt", 10, 25, ["hardware", "small"]), Item("A-1", "Anvil", 1, 9900, ["heavy"]), Item("C-3", "Cog", 0, 0, [])])


class AcceptT1(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def p(self, name):
        return os.path.join(self.d, name)

    def write(self, name, text):
        with open(self.p(name), "w", newline="") as f:
            f.write(text)
        return self.p(name)

    def test_csv_roundtrip(self):
        export_csv(sample(), self.p("a.csv"))
        with open(self.p("a.csv")) as f:
            lines = f.read().splitlines()
        self.assertEqual(lines[0], "sku,name,quantity,price_cents,tags")
        self.assertTrue(lines[1].startswith("A-1,"))
        self.assertIn("hardware;small", lines[2])
        s = import_csv(self.p("a.csv"))
        self.assertEqual([i.to_dict() for i in s.list()], [i.to_dict() for i in sample().list()])

    def test_csv_errors_name_line(self):
        hdr = "sku,name,quantity,price_cents,tags\n"
        for bad in ["A-1,Anvil,x,1,\n", "A-1,Anvil,-1,1,\n", ",Anvil,1,1,\n"]:
            path = self.write("b.csv", hdr + "Z-9,Zip,1,1,\n" + bad)
            with self.assertRaises(ValueError) as cm:
                import_csv(path)
            self.assertIn("line 3", str(cm.exception))
        path = self.write("c.csv", hdr + "A-1,Anvil,1,1,\nA-1,Again,1,1,\n")
        with self.assertRaises(ValueError) as cm:
            import_csv(path)
        self.assertIn("line 3", str(cm.exception))

    def test_json_roundtrip_and_errors(self):
        export_json(sample(), self.p("a.json"))
        with open(self.p("a.json")) as f:
            data = json.load(f)
        self.assertEqual([d["sku"] for d in data], ["A-1", "B-2", "C-3"])
        s = import_json(self.p("a.json"))
        self.assertEqual(len(s), 3)
        path = self.write("b.json", json.dumps([{"sku": "A", "name": "a"}, {"sku": "B", "name": "b", "quantity": -2}]))
        with self.assertRaises(ValueError) as cm:
            import_json(path)
        self.assertIn("index 1", str(cm.exception))

    def test_package_exports(self):
        import inventory
        for n in ["export_csv", "import_csv", "export_json", "import_json"]:
            self.assertTrue(hasattr(inventory, n), n)


if __name__ == "__main__":
    unittest.main()
