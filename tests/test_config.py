import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import flash_config as config


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def file(self, text, suffix=".json"):
        path = self.root / ("items" + suffix)
        path.write_text(text, encoding="utf-8")
        return path

    def test_json_and_csv_match(self):
        base = Path(__file__).resolve().parents[1] / "examples"
        self.assertEqual(config.load_catalog(base / "items.json"), config.load_catalog(base / "items.csv"))

    def test_deterministic_generation_and_escaping(self):
        rows = config.validate([{"id": "a", "name": 'é"\\\n123', "price": 0}])
        output = config.render(rows)
        self.assertEqual(output, config.render(rows))
        self.assertIn('name = "\\195\\169\\034\\092\\010123"', output)
        self.assertIn("table.freeze", output)

    def test_rejects_invalid_records(self):
        base = {"id": "a", "name": "Item", "price": 1}
        changes = [{"id": "a b"}, {"id": "1a"}, {"name": " "}, {"price": True}, {"price": -1}, {"price": 1.0}, {"price": config.MAX_PRICE + 1}, {"extra": 1}, {"requires": ""}, {"requires": "missing"}]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(config.CatalogError):
                config.validate([base | change])
        for value in [None, {}, [], [1], [base, base], [base | {"requires": "a"}]]:
            with self.subTest(value=value), self.assertRaises(config.CatalogError):
                config.validate(value)

    def test_cycle_and_long_chain(self):
        with self.assertRaises(config.CatalogError):
            config.validate([{"id": "a", "name": "A", "price": 0, "requires": "b"}, {"id": "b", "name": "B", "price": 0, "requires": "a"}])
        rows = [{"id": f"a{i}", "name": "A", "price": 0, **({"requires": f"a{i+1}"} if i < 2999 else {})} for i in range(3000)]
        self.assertEqual(len(config.validate(rows)), 3000)

    def test_duplicate_json_keys_and_nonfinite(self):
        for text in ['[{"id":"a","id":"b","name":"A","price":0}]', '[{"id":"a","name":"A","price":NaN}]', '[{"id":"a","name":"A","price":1e999}]']:
            with self.subTest(text=text), self.assertRaises(ValueError):
                config.load_catalog(self.file(text))

    def test_csv_shape_and_numeric_errors(self):
        for text in ['id,name,price,price\na,A,0,0', 'id,name,price\na,A', 'id,name,price\na,A,0,extra', 'id,name,price\na,A,01', 'id,name,price\na,A,1.5', 'id,name,price\na,"unclosed,1']:
            with self.subTest(text=text), self.assertRaises((ValueError, config.csv.Error)):
                config.load_catalog(self.file(text, ".csv"))

    def test_limit_and_utf8(self):
        with self.assertRaises(config.CatalogError):
            config.load_catalog(self.file(" " * (config.MAX_BYTES + 1)))
        with self.assertRaises(UnicodeError):
            config.load_catalog(self.file('[{"id":"a","name":"\\ud800","price":0}]'))

    def test_cli_invalid_input_preserves_output(self):
        source = self.file("[]")
        target = self.root / "Items.luau"
        target.write_text("original", encoding="utf-8")
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(config.main([str(source), "--output", str(target)]), 1)
        self.assertEqual(target.read_text(), "original")

    def test_cli_subprocess_success_and_error(self):
        source = self.file('[{"id":"a","name":"A","price":0}]')
        target = self.root / "build" / "Items.luau"
        program = str(Path(config.__file__))
        result = subprocess.run([sys.executable, program, str(source), "--output", str(target)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(target.read_text(), config.render(config.load_catalog(source)))
        bad = subprocess.run([sys.executable, program, str(source), "--output", str(source)], capture_output=True)
        self.assertEqual(bad.returncode, 1)
        check = subprocess.run([sys.executable, program, str(source), "--check"], capture_output=True)
        self.assertEqual(check.returncode, 0)


if __name__ == "__main__":
    unittest.main()
