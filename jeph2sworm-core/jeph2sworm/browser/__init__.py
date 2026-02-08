"""Browser automation package - browser-use bridge and controller."""

import sys
from pathlib import Path

# Add vendor/browser-use to sys.path if present (allows `from browser_use import ...`)
_vendor_browser_use = Path(__file__).resolve().parents[3] / "vendor" / "browser-use"
if _vendor_browser_use.is_dir() and str(_vendor_browser_use) not in sys.path:
    sys.path.insert(0, str(_vendor_browser_use))
