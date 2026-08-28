"""Minimal DiddiMap stub for local Bruno E2E runs.

DiddiGo refuses to fabricate a silent geographic fallback (by design — see
PRODUCTION_READINESS.md) so `POST /rides` and `/places/search` genuinely need a
reachable DiddiMap at DIDDIMAP_BASE_URL (default http://localhost:4000). This stub
implements just enough of the two endpoints DiddiMap's client actually calls
(app_base/modules/ride/infra/routing_client.py) to unblock local testing without
running the real DiddiMap service.

Usage:
    python bruno/diddigo-api/mock-diddimap.py
    # leave running in its own terminal, then run the Bruno collection against
    # the "local" environment as normal.

Not used for staging — staging's DIDDIMAP_BASE_URL points at the real
abidjanmaps-backend-staging service.
"""

from __future__ import annotations

import json
import math
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

PORT = 4000


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802 (stdlib naming)
        if self.path != "/api/v1/route":
            self._send_json(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length) or b"{}")
        start, end = payload.get("start", {}), payload.get("end", {})
        distance_km = _haversine_km(
            float(start.get("lat", 0)), float(start.get("lng", 0)),
            float(end.get("lat", 0)), float(end.get("lng", 0)),
        )
        # ~25 km/h average urban speed, floor 60s so tiny hops still return something.
        duration_seconds = max(60, int(distance_km / 25 * 3600))
        self._send_json(200, {"distance_km": round(distance_km, 3), "duration_seconds": duration_seconds})

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path != "/api/v1/geocoding/search":
            self._send_json(404, {"error": "not found"})
            return
        qs = parse_qs(parsed.query)
        q = qs.get("q", ["Unknown place"])[0]
        bias_lat = float(qs.get("bias_lat", ["5.3600"])[0])
        bias_lng = float(qs.get("bias_lng", ["-4.0083"])[0])
        self._send_json(
            200,
            {
                "results": [
                    {"label": f"{q} (mock result)", "location": {"lat": bias_lat, "lng": bias_lng}},
                ],
            },
        )

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        print(f"[mock-diddimap] {self.address_string()} - {format % args}")


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"mock-diddimap listening on http://localhost:{PORT}")
    server.serve_forever()
