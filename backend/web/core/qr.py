"""Device-provisioning QR (was components/DeviceToken.tsx, qrcode.react).

Payload, JSON (UTF-8, no spaces), documented in docs/API_CONTRACTS.md:
  {"type":"schooldimes_device","v":1,"api_base_url":"http://192.168.1.20:8000","device_token":"<raw token>"}
api_base_url is the backend origin the DEVICE must use (a LAN address for a
phone on the school Wi-Fi). Drawn server-side as SVG; nothing is stored."""
import io
import json

import segno


def provisioning_payload(api_base_url: str, token: str) -> str:
    return json.dumps({"type": "schooldimes_device", "v": 1, "api_base_url": (api_base_url or "").rstrip("/"),
                       "device_token": token}, separators=(",", ":"))


def qr_svg(payload: str) -> str:
    """Error correction M with the standard 4-module quiet zone, ~240 px."""
    qr = segno.make(payload, error="m", micro=False)
    out = io.BytesIO()
    width = qr.symbol_size(scale=1, border=4)[0]
    qr.save(out, kind="svg", scale=max(1, 240 // width), border=4, xmldecl=False, svgns=True, nl=False)
    return out.getvalue().decode()


def default_device_api_base(request) -> str:
    from django.conf import settings

    return (settings.DEVICE_API_BASE_URL or request.build_absolute_uri("/")).rstrip("/")
