"""Copy real screenshots captured from the live SunStay site into docs/screenshots."""
from pathlib import Path
from PIL import Image
import shutil

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots"
TMP = Path(r"C:\Users\Redmibook\AppData\Local\Temp")

# name -> capture folder (browser temp dir); each contains 0/screenshot.jpeg
CAPTURES = {
    "real-home": "opencode-browser-Wjhvvh",
    "real-search": "opencode-browser-btkQAu",
    "real-admin-dashboard": "opencode-browser-ALafwa",
    "real-admin-bookings": "opencode-browser-XKYdkq",
    "real-admin-grid": "opencode-browser-BqH1Du",
    "real-admin-folios": "opencode-browser-PStZx7",
    "real-admin-waitlist": "opencode-browser-6w9umC",
    "real-admin-audit": "opencode-browser-GXEose",
    "real-admin-backups": "opencode-browser-K5Z8Bt",
    "real-admin-reviews": "opencode-browser-2aohrZ",
    "real-admin-settings": "opencode-browser-VGGPAb",
    "real-admin-housekeeping": "opencode-browser-D5FAj5",
    "real-admin-reports": "opencode-browser-cl4dWS",
    "real-admin-users": "opencode-browser-kPXY77",
    "real-admin-floor-plan": "opencode-browser-brAxrT",
    "real-admin-directories": "opencode-browser-B7spOg",
    "real-admin-maintenance": "opencode-browser-noSn7D",
    "real-manager-dashboard": "opencode-browser-qLQb76",
    "real-manager-bookings": "opencode-browser-F2Twjd",
    "real-manager-grid": "opencode-browser-vxo1LA",
    "real-manager-folios": "opencode-browser-kjTel6",
    "real-manager-waitlist": "opencode-browser-DxxxYU",
    "real-manager-reports": "opencode-browser-izRXrK",
    "real-guest-home": "opencode-browser-4e4nIb",
    "real-guest-bookings": "opencode-browser-A7mA3B",
    "real-guest-services": "opencode-browser-OZt6YF",
    "real-guest-invoices": "opencode-browser-ayB3dW",
    "real-guest-loyalty": "opencode-browser-2cAasj",
    "real-guest-profile": "opencode-browser-1srUar",
    "real-hk-board": "opencode-browser-aVNHbE",
    "real-hk-maintenance": "opencode-browser-MkNl3O",
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    saved = []
    for name, folder in CAPTURES.items():
        src = TMP / folder / "0" / "screenshot.jpeg"
        if not src.exists():
            print("MISSING", name, src)
            continue
        img = Image.open(src).convert("RGB")
        dst = OUT / f"{name}.jpg"
        img.save(dst, "JPEG", quality=88)
        saved.append((name, dst.stat().st_size))
    print("SAVED", len(saved))
    for n, s in saved:
        print(" ", n, s)


if __name__ == "__main__":
    main()
