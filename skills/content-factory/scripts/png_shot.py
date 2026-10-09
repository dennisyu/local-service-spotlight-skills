"""Headless-Chrome PNG capture shared by the Content Factory renderers.

Prefers the real Chrome/Chromium binary over wrapper scripts (a wrapper that
pins ``--remote-debugging-port`` or a shared ``--user-data-dir`` keeps Chrome
alive after the screenshot and the render never returns). Always uses its own
throwaway profile, never the operator's daily browser profile, and gives up
after ``timeout`` seconds instead of hanging a test run.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

CANDIDATES = (
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
    "google-chrome",
    "chrome",
)


class PngError(RuntimeError):
    pass


def find_chrome() -> str | None:
    for name in CANDIDATES:
        found = shutil.which(name)
        if found:
            return found
    return None


def write_png(html_path: Path, png_path: Path, width: int, height: int, timeout: int = 120) -> None:
    chrome = find_chrome()
    if not chrome:
        raise PngError("no Chrome/Chromium on PATH; skip --png or install google-chrome")
    with tempfile.TemporaryDirectory(prefix="cf-png-profile-") as profile:
        try:
            subprocess.run(
                [
                    chrome,
                    "--headless=new",
                    "--disable-gpu",
                    "--no-sandbox",
                    "--no-first-run",
                    "--disable-extensions",
                    "--hide-scrollbars",
                    "--mute-audio",
                    f"--user-data-dir={profile}",
                    f"--window-size={width},{height}",
                    f"--screenshot={png_path}",
                    html_path.resolve().as_uri(),
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise PngError(f"Chrome did not finish the screenshot in {timeout}s") from exc
        except subprocess.CalledProcessError as exc:
            raise PngError(f"Chrome exited {exc.returncode}: {exc.stderr.strip()[-400:]}") from exc
    if not png_path.is_file():
        raise PngError(f"Chrome returned but {png_path} was not written")
