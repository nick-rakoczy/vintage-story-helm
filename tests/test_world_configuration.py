import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    "configure_world", Path(__file__).resolve().parents[1] / "files/configure-world.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class WorldConfigurationTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.config = self.root / "serverconfig.json"
        self.settings = self.root / "settings.json"
        self.settings.write_text(json.dumps({
            "deathPunishment": "keep", "graceTimer": 2,
            "saplingGrowthRate": 2, "allowMap": False,
        }))
        self.environment = patch.dict(os.environ, {
            "HOMEPATH": str(self.root), "DATAPATH": str(self.root),
            "FORCE_REGENERATE_CONFIG": "false",
        })
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.exec = patch.object(module.os, "execv").start()
        self.addCleanup(patch.stopall)

    def write_generator(self):
        (self.root / "generate-config.py").write_text(
            "import json, pathlib, sys\n"
            "path = pathlib.Path(sys.argv[1])\n"
            "if path.exists():\n"
            "    path.rename(path.with_suffix('.json.backup'))\n"
            "path.write_text(json.dumps({'ServerName': 'generated', "
            "'WorldConfig': {'WorldConfiguration': None}}))\n"
        )

    def assert_settings(self):
        config = json.loads(self.config.read_text())
        settings = config["WorldConfig"]["WorldConfiguration"]
        self.assertEqual(settings["deathPunishment"], "keep")
        self.assertEqual(settings["graceTimer"], "2")
        self.assertEqual(settings["saplingGrowthRate"], "2")
        self.assertEqual(settings["allowMap"], "false")
        self.assertEqual(os.environ["FORCE_REGENERATE_CONFIG"], "false")
        self.exec.assert_called_once_with(
            str(self.root / "entrypoint.sh"), [str(self.root / "entrypoint.sh")]
        )
        return config

    def test_first_start_generates_then_merges(self):
        self.write_generator()
        module.configure(self.settings)
        self.assertEqual(self.assert_settings()["ServerName"], "generated")

    def test_existing_config_preserves_unrelated_fields(self):
        self.config.write_text(json.dumps({
            "Password": "existing-password",
            "WorldConfig": {"Seed": "123", "WorldConfiguration": {"daysPerMonth": "12"}},
        }))
        self.config.chmod(0o640)
        module.configure(self.settings)
        config = self.assert_settings()
        self.assertEqual(config["Password"], "existing-password")
        self.assertEqual(config["WorldConfig"]["Seed"], "123")
        self.assertEqual(config["WorldConfig"]["WorldConfiguration"]["daysPerMonth"], "12")
        self.assertEqual(self.config.stat().st_mode & 0o777, 0o640)

    def test_force_regeneration_keeps_backup_and_applies_settings(self):
        self.write_generator()
        original = '{"ServerName": "old"}'
        self.config.write_text(original)
        os.environ["FORCE_REGENERATE_CONFIG"] = "true"
        module.configure(self.settings)
        self.assertEqual(self.assert_settings()["ServerName"], "generated")
        self.assertEqual(self.config.with_suffix(".json.backup").read_text(), original)

    def test_generator_failure_prevents_server_start(self):
        (self.root / "generate-config.py").write_text("raise SystemExit(1)\n")
        with self.assertRaises(subprocess.CalledProcessError):
            module.configure(self.settings)
        self.exec.assert_not_called()


if __name__ == "__main__":
    unittest.main()
