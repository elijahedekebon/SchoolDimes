"""School branding -> CSS custom properties (same formula as the dashboard's
Providers.brandShades: 10 shades light -> dark with the brand colour at 6)."""
import re

HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
# Mantine's default teal, used when the school has no valid primary_color.
TEAL = ["#e6fcf5", "#c3fae8", "#96f2d7", "#63e6be", "#38d9a9", "#20c997", "#12b886", "#0ca678", "#099268", "#087f5b"]


def brand_shades(hex_color: str) -> list[str]:
    n = int(hex_color[1:], 16)
    rgb = [(n >> 16) & 255, (n >> 8) & 255, n & 255]

    def mix(target, w):
        # JS Math.round rounds .5 up
        return "#" + "".join(f"{int(c + (target - c) * w + 0.5):02x}" for c in rgb)

    return [mix(255, 0.92), mix(255, 0.8), mix(255, 0.62), mix(255, 0.45), mix(255, 0.28), mix(255, 0.12),
            hex_color.lower(), mix(0, 0.12), mix(0, 0.24), mix(0, 0.36)]


def palette_for(branding) -> list[str]:
    color = (branding or {}).get("primary_color")
    return brand_shades(color) if isinstance(color, str) and HEX.match(color) else TEAL
