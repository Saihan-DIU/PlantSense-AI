"""Render static/images/og-image.png, the 1200x630 picture shown when the site
is shared on Facebook, WhatsApp, LinkedIn or X.

  python tools/make_og_image.py

The design lives in tools/og-image.html and is rendered with a headless
Edge/Chrome, which shapes Bangla text correctly (Pillow can't without raqm).
"""
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "tools", "og-image.html")
OUT = os.path.join(ROOT, "static", "images", "og-image.png")

BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "google-chrome", "chromium", "msedge",
]


def find_browser():
    for b in BROWSERS:
        if os.path.exists(b) or shutil.which(b):
            return b
    sys.exit("No Edge/Chrome found to render the image.")


def main():
    with tempfile.TemporaryDirectory() as profile:
        subprocess.run([
            find_browser(), "--headless=new", "--disable-gpu", "--hide-scrollbars",
            f"--user-data-dir={profile}", "--force-device-scale-factor=1",
            "--window-size=1200,630", "--virtual-time-budget=8000",
            f"--screenshot={OUT}", "file:///" + SRC.replace("\\", "/"),
        ], check=True, capture_output=True, timeout=120)
    print(f"wrote {os.path.relpath(OUT, ROOT)} ({os.path.getsize(OUT) // 1024} KB)")


if __name__ == "__main__":
    main()
