# SPDX-License-Identifier: 0BSD
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

from build_addon import build, PAYLOAD
from reader import read_config, read_results

ROOT = Path(__file__).resolve().parents[1]


class TemplateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.config = self.root / "config.yaml"
        self.config.write_text("VIDEO_PATH: recording.mp4\nNUM_OBJECTS: 2\n")
        self.results = self.root / "result.csv"
        self.results.write_text("frame,heading,cx\n1,359.5,40\n2,0.5,42\n")

    def tearDown(self):
        self.temporary.cleanup()

    def test_config_read_only(self):
        before = self.config.read_bytes()
        self.assertEqual(read_config(self.config)["NUM_OBJECTS"], 2)
        self.assertEqual(self.config.read_bytes(), before)

    def test_csv_values_are_not_converted(self):
        before = self.results.read_bytes()
        parsed = read_results(self.results)
        self.assertEqual(parsed["records_after_first_row"], 2)
        self.assertEqual(parsed["preview"][0], ["1", "359.5", "40"])
        self.assertEqual(self.results.read_bytes(), before)

    def test_bom_and_preview_limit(self):
        self.results.write_text("\ufeffframe,id\n1,1\n2,2\n")
        parsed = read_results(self.results, 1)
        self.assertEqual(parsed["first_row"], ["frame", "id"])
        self.assertEqual(len(parsed["preview"]), 1)
        self.assertEqual(parsed["records_after_first_row"], 2)

    def test_empty_csv_rejected(self):
        self.results.write_text("")
        with self.assertRaises(ValueError):
            read_results(self.results)

    def test_nonmapping_yaml_rejected(self):
        self.config.write_text("- one\n- two\n")
        with self.assertRaises(ValueError):
            read_config(self.config)

    def test_yaml_python_tag_rejected(self):
        import yaml
        self.config.write_text("!!python/object/apply:os.system ['echo unsafe']")
        with self.assertRaises(yaml.YAMLError):
            read_config(self.config)

    def test_standalone_headless_command(self):
        result = subprocess.run([sys.executable, str(ROOT / "app.py"), "--check", "--config", str(self.config),
                                 "--results", str(self.results)], capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(result.stdout)["csv"]["records_after_first_row"], 2)

    def test_build_contains_only_payload(self):
        archive = build(ROOT, self.root / "dist")
        with zipfile.ZipFile(archive) as content:
            self.assertEqual(set(content.namelist()), set(PAYLOAD))
            self.assertEqual(json.loads(content.read("addon.json"))["license"], "0BSD")

    def test_deterministic_build_and_update_digest(self):
        first = build(ROOT, self.root / "one", "https://example.org/addon.zip")
        second = build(ROOT, self.root / "two")
        self.assertEqual(first.read_bytes(), second.read_bytes())
        update = json.loads((first.parent / "update.json").read_text())
        self.assertEqual(update["sha256"], hashlib.sha256(first.read_bytes()).hexdigest())
        self.assertEqual(update["url"], "https://example.org/addon.zip")

    def test_bad_download_url_rejected(self):
        with self.assertRaises(ValueError):
            build(ROOT, self.root / "dist", "http://example.org/addon.zip")


if __name__ == "__main__":
    unittest.main()
