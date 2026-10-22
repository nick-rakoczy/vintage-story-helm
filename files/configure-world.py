"""Merge chart world settings after the image generates its server config."""

import json
import os
from pathlib import Path
import subprocess
import sys


def configure(settings_path):
    home = Path(os.environ.get("HOMEPATH", "/vintagestory"))
    data = Path(os.environ.get("DATAPATH", "/vintagestory/data"))
    config_path = data / "serverconfig.json"
    settings = json.loads(Path(settings_path).read_text())

    if not config_path.exists() or os.environ.get("FORCE_REGENERATE_CONFIG") == "true":
        subprocess.run(
            [sys.executable, str(home / "generate-config.py"), str(config_path)],
            check=True,
        )

    config = json.loads(config_path.read_text())
    world = config.get("WorldConfig") or {}
    configuration = world.get("WorldConfiguration") or {}
    configuration.update({
        key: str(value).lower() if isinstance(value, bool) else str(value)
        for key, value in settings.items()
    })
    world["WorldConfiguration"] = configuration
    config["WorldConfig"] = world

    # Replace atomically so an interrupted write cannot truncate the config.
    temporary = config_path.with_suffix(".json.tmp")
    try:
        temporary.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n")
        temporary.chmod(config_path.stat().st_mode & 0o777)
        temporary.replace(config_path)
    finally:
        temporary.unlink(missing_ok=True)

    # The entrypoint still handles ownership, mods, RCON, and server startup.
    # Generation already happened above; a second pass would erase the merge.
    os.environ["FORCE_REGENERATE_CONFIG"] = "false"
    entrypoint = str(home / "entrypoint.sh")
    os.execv(entrypoint, [entrypoint])


if __name__ == "__main__":
    configure(Path(__file__).with_name("world-configuration.json"))
