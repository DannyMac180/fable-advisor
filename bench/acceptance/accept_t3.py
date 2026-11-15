import json, os, subprocess, sys, tempfile, unittest


class AcceptT3(unittest.TestCase):
    def setUp(self):
        self.db = os.path.join(tempfile.mkdtemp(), "db.json")

    def run_cli(self, *args):
        return subprocess.run([sys.executable, "-m", "inventory", "--db", self.db, *args], capture_output=True, text=True, cwd=os.getcwd())

    def test_flow(self):
        r = self.run_cli("add", "B-2", "Bolt", "--quantity", "10", "--price-cents", "25", "--tag", "hardware")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.run_cli("add", "A-1", "Anvil", "--quantity", "1", "--price-cents", "9900", "--tag", "heavy", "--tag", "hardware").returncode, 0)
        self.assertEqual(self.run_cli("adjust", "B-2", "-4").returncode, 0)
        r = self.run_cli("list")
        self.assertEqual(r.stdout.strip().splitlines(), ["A-1\tAnvil\t1", "B-2\tBolt\t6"])
        r = self.run_cli("list", "--tag", "heavy")
        self.assertEqual(r.stdout.strip().splitlines(), ["A-1\tAnvil\t1"])
        self.assertEqual(self.run_cli("value").stdout.strip(), str(6 * 25 + 9900))
        self.assertEqual(self.run_cli("remove", "A-1").returncode, 0)
        with open(self.db) as f:
            self.assertEqual([d["sku"] for d in json.load(f)], ["B-2"])

    def test_errors_leave_db_unchanged(self):
        self.run_cli("add", "B-2", "Bolt", "--quantity", "2")
        with open(self.db) as f:
            before = f.read()
        for args in [("add", "B-2", "Dup"), ("remove", "Z-9"), ("adjust", "B-2", "-5"), ("add", "C-3", "Cog", "--quantity", "-1")]:
            r = self.run_cli(*args)
            self.assertEqual(r.returncode, 1, args)
            self.assertTrue(r.stderr.strip().startswith("error:"), (args, r.stderr))
            with open(self.db) as f:
                self.assertEqual(f.read(), before, args)

    def test_main_returns_int(self):
        from inventory.cli import main
        self.assertEqual(main(["--db", self.db, "value"]), 0)


if __name__ == "__main__":
    unittest.main()
