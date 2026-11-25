"""Package dist/version.dll into a zip laid out for the Expedition 33 game folder.

Usage: python package.py 1.0.0   ->  Expedition33FXCore-1.0.0.zip

The zip holds only the DLL and plain text files: no scripts and no archives inside the archive,
so mod sites' scanners have nothing extra to flag.
"""
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GAME_DIR = "Sandfall/Binaries/Win64/"


def crlf(text: str) -> bytes:
    return text.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8")


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: python package.py <version>")
    version = sys.argv[1]
    src = (ROOT / "src" / "fxcore.c").read_text(encoding="utf-8")
    if f'#define FXCORE_VERSION "{version}"' not in src:
        sys.exit(f"src/fxcore.c does not say version {version}")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    readme = readme.split("## Building from source")[0]
    readme = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", readme)
    readme += "\nSource code: https://github.com/mcirish3/Expedition33FXCore\n"

    out = ROOT / f"Expedition33FXCore-{version}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(ROOT / "dist" / "version.dll", GAME_DIR + "version.dll")
        z.writestr(GAME_DIR + "Expedition33FXCore.ini",
                   crlf((ROOT / "config" / "Expedition33FXCore.ini").read_text(encoding="utf-8")))
        z.writestr("Expedition33FXCore-README.txt", crlf(readme))
        z.writestr("Expedition33FXCore-LICENSE.txt", crlf((ROOT / "LICENSE").read_text(encoding="utf-8")))
    print(f"Packaged {out.name}")


if __name__ == "__main__":
    main()
