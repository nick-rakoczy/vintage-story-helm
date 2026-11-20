import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "download_mods", Path(__file__).resolve().parents[1] / "files/download-mods.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ModsTest(unittest.TestCase):
    def test_mixed_urls_and_short_paths(self):
        with tempfile.TemporaryDirectory() as root:
            def fetch(command, **kwargs):
                Path(command[command.index("--output") + 1]).write_bytes(b"mod")
            with patch.object(module.subprocess, "run", side_effect=fetch) as run:
                module.download([
                    "123/legacy.zip", "https://example.com/custom%20mod.zip?token=a,b",
                    "http://example.com/another.dll",
                ], root)
            self.assertEqual(run.call_count, 3)
            self.assertEqual(run.call_args_list[0].args[0][-1],
                             "https://mods.vintagestory.at/download/123/legacy.zip")
            self.assertEqual((Path(root) / "Mods/custom mod.zip").read_bytes(), b"mod")
            with patch.object(module.subprocess, "run") as run:
                module.download(["123/legacy.zip"], root)
                run.assert_not_called()

    def test_failed_download_is_not_installed(self):
        with tempfile.TemporaryDirectory() as root:
            with patch.object(module.subprocess, "run", side_effect=subprocess.CalledProcessError(22, "curl")):
                with self.assertRaises(subprocess.CalledProcessError):
                    module.download(["https://example.com/fail.zip"], root)
            self.assertEqual(list((Path(root) / "Mods").iterdir()), [])

    def test_invalid_urls_cannot_escape_mod_directory(self):
        with tempfile.TemporaryDirectory() as root:
            for url in ["file:///tmp/mod.zip", "https://example.com/", "https://example.com/%2e%2e", "https://example.com/a%2fb.zip"]:
                with self.subTest(url=url), self.assertRaises(ValueError):
                    module.download([url], root)
