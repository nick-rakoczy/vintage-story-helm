"""Download chart-managed mods before handing off to the image startup."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from urllib.parse import unquote, urlsplit


def download(mods, data):
    directory = Path(data) / "Mods"
    directory.mkdir(parents=True, exist_ok=True)
    for entry in mods:
        url = entry if "://" in entry else "https://mods.vintagestory.at/download/" + entry
        parsed = urlsplit(url)
        if parsed.scheme.lower() not in ("http", "https") or not parsed.netloc:
            raise ValueError("Mods require an HTTP or HTTPS download URL")
        name = unquote(parsed.path.rsplit("/", 1)[-1])
        if not name or name in (".", "..") or any(c in name for c in ("/", "\\", "\0")):
            raise ValueError("Mod download URL must end with a filename")
        destination = directory / name
        if destination.is_file():
            continue
        # Keep interrupted or failed downloads out of the installed mod list.
        with tempfile.NamedTemporaryFile(dir=directory, suffix=".tmp", delete=False) as output:
            temporary = Path(output.name)
        try:
            subprocess.run([
                "curl", "--fail", "--location", "--silent", "--show-error",
                "--proto", "=http,https", "--proto-redir", "=http,https",
                "--connect-timeout", "30", "--max-time", "600",
                "--output", str(temporary), "--url", url,
            ], check=True)
            temporary.chmod(0o644)
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)


def main():
    settings = json.loads(Path(__file__).with_name("mods.json").read_text())
    download(settings["mods"], os.environ.get("DATAPATH", settings["dataPath"]))
    # The image only supports short paths; these mods have already been handled.
    os.environ["VS_MODS"] = ""
    if settings["configureWorld"]:
        script = "/etc/vintage-story/configure-world.py"
        os.execv(sys.executable, [sys.executable, script])
    else:
        entrypoint = str(Path(os.environ.get("HOMEPATH", "/vintagestory")) / "entrypoint.sh")
        os.execv(entrypoint, [entrypoint])


if __name__ == "__main__":
    main()
