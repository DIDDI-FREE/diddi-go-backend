"""HTTP / WebSocket helpers for the dispatch E2E suite (SCRUM-63).

Thin, explicit wrappers over the staging API. Auth is real: passenger, drivers
and the admin log in via OTP (the operator pastes the code, or supplies it via
`DIDDIGO_OTP_<digits>`); the /internal dispatch admin routes use an S2S
client-credentials token plus the admin's DiddiFreeID id as X-Backoffice-Actor.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import uuid
from dataclasses import dataclass, field
from typing import Any

import httpx

from tests.e2e.config import CONFIG, E2EConfig


def _otp_code(phone: str) -> str:
    """OTP for `phone`: env override for non-interactive reruns, else prompt.

    Env key is DIDDIGO_OTP_<digits-of-phone> (e.g. +2250700000101 ->
    DIDDIGO_OTP_2250700000101)."""
    key = "DIDDIGO_OTP_" + re.sub(r"\D", "", phone)
    env = os.getenv(key)
    if env:
        return env.strip()
    return input(f"\n[e2e] Enter OTP received for {phone} (env {key} to skip prompt): ").strip()


@dataclass
class DriverActor:
    name: str
    phone: str
    token: str
    driver_id: str
    vehicle_id: str
    lat: float
    lng: float


@dataclass
class E2EClient:
    config: E2EConfig = CONFIG
    _s2s: str | None = field(default=None, init=False)
    _admin_token: str | None = field(default=None, init=False)
    _admin_id: str | None = field(default=None, init=False)

    def _http(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(base_url=self.config.base_url, timeout=self.config.http_timeout)

    @staticmethod
    def _auth(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    # --- authentication ----------------------------------------------------

    async def login_via_otp(self, phone: str, *, role: str = "passenger") -> str:
        async with self._http() as http:
            # Register is idempotent for our purposes: a 409/400 means the
            # account already exists, which is fine — we still OTP into it.
            await http.post("/v1/auth/register", json={"phone": phone, "role": role})
            resp = await http.post("/v1/auth/otp/request", json={"phone": phone})
            resp.raise_for_status()
            code = _otp_code(phone)
            verify = await http.post("/v1/auth/otp/verify", json={"phone": phone, "code": code})
            verify.raise_for_status()
            token = verify.json()["access_token"]
        return token

    async def s2s_token(self) -> str:
        if self._s2s:
            return self._s2s
        data = {
            "grant_type": "client_credentials",
            "client_id": self.config.s2s_client_id,
            "client_secret": self.config.s2s_client_secret,
        }
        if self.config.s2s_audience:
            data["audience"] = self.config.s2s_audience
        async with httpx.AsyncClient(timeout=self.config.http_timeout) as http:
            resp = await http.post(
                self.config.s2s_token_url, data=data, headers={"X-Client-ID": self.config.s2s_client_id},
            )
            resp.raise_for_status()
            self._s2s = resp.json()["access_token"]
        return self._s2s

    async def admin_token(self) -> str:
        if self._admin_token is None:
            self._admin_token = await self.login_via_otp(self.config.admin_phone, role="admin")
        return self._admin_token

    async def admin_id(self) -> str:
        if self._admin_id is None:
            token = await self.admin_token()
            async with self._http() as http:
                resp = await http.get("/v1/auth/me", headers=self._auth(token))
                resp.raise_for_status()
                self._admin_id = str(resp.json()["id"])
        return self._admin_id

    def _s2s_headers(self, token: str, actor_id: str, *, write: bool) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {token}", "X-Client-ID": self.config.s2s_client_id}
        if write:
            headers["X-Request-ID"] = str(uuid.uuid4())
            headers["Idempotency-Key"] = str(uuid.uuid4())
            headers["X-Backoffice-Actor"] = actor_id
        return headers

    # --- driver onboarding -------------------------------------------------

    async def onboard_driver(self, index: int, lat: float, lng: float, *, name: str) -> DriverActor:
        """register -> OTP -> create profile -> admin KYC approve -> add vehicle
        -> admin KYV approve -> go online at (lat,lng). Driver is now matchable."""
        phone = self.config.driver_phone(index)
        token = await self.login_via_otp(phone, role="driver")
        admin_token = await self.admin_token()
        async with self._http() as http:
            profile = await http.post(
                "/v1/drivers/profile",
                headers=self._auth(token),
                json={"license_number": f"CI-E2E-{index:04d}", "legal_name": f"E2E Driver {index}"},
            )
            profile.raise_for_status()
            driver_id = str((await self._driver_me(http, token))["id"])

            approve = await http.post(
                f"/v1/drivers/{driver_id}/kyc/approve",
                headers=self._auth(admin_token),
                json={"notes": "e2e auto-approve"},
            )
            approve.raise_for_status()

            vehicle = await http.post(
                "/v1/drivers/vehicle",
                headers=self._auth(token),
                json={
                    "plate_number": f"E2E-{index:04d}-CI",
                    "category": self.config.vehicle_category,
                    "comfort_level": self.config.comfort_level,
                },
            )
            vehicle.raise_for_status()
            vehicle_id = str(vehicle.json()["id"])

            kyv = await http.post(
                f"/v1/drivers/vehicles/{vehicle_id}/kyv/approve",
                headers=self._auth(admin_token),
                json={"notes": "e2e auto-approve"},
            )
            kyv.raise_for_status()

            online = await http.post("/v1/drivers/online", headers=self._auth(token), json={"lat": lat, "lng": lng})
            online.raise_for_status()
        return DriverActor(
            name=name, phone=phone, token=token, driver_id=driver_id,
            vehicle_id=vehicle_id, lat=lat, lng=lng,
        )

    @staticmethod
    async def _driver_me(http: httpx.AsyncClient, token: str) -> dict[str, Any]:
        resp = await http.get("/v1/drivers/me", headers={"Authorization": f"Bearer {token}"})
        resp.raise_for_status()
        return resp.json()

    async def go_offline(self, driver: DriverActor) -> None:
        async with self._http() as http:
            await http.post("/v1/drivers/offline", headers=self._auth(driver.token))

    # --- ride lifecycle ----------------------------------------------------

    async def request_ride(
        self, passenger_token: str, pickup: tuple[float, float], dropoff: tuple[float, float],
    ) -> str:
        async with self._http() as http:
            resp = await http.post(
                "/v1/rides",
                headers=self._auth(passenger_token),
                json={
                    "pickup": {"lat": pickup[0], "lng": pickup[1]},
                    "dropoff": {"lat": dropoff[0], "lng": dropoff[1]},
                    "vehicle_category": self.config.vehicle_category,
                    "comfort_level": self.config.comfort_level,
                    "payment_method": self.config.payment_method,
                },
            )
            resp.raise_for_status()
            return str(resp.json()["id"])

    async def ride_status(self, token: str, ride_id: str) -> str:
        async with self._http() as http:
            resp = await http.get(f"/v1/rides/{ride_id}", headers=self._auth(token))
            resp.raise_for_status()
            return str(resp.json()["status"])

    async def wait_for_status(self, token: str, ride_id: str, targets: set[str], *, timeout: float = 30) -> str:
        deadline = timeout
        async with self._http() as http:
            while deadline > 0:
                resp = await http.get(f"/v1/rides/{ride_id}", headers=self._auth(token))
                resp.raise_for_status()
                status = str(resp.json()["status"])
                if status in targets:
                    return status
                await asyncio.sleep(1.5)
                deadline -= 1.5
        raise AssertionError(f"ride {ride_id} did not reach {targets} within {timeout}s (last={status})")

    async def accept_ride(self, driver: DriverActor, ride_id: str) -> None:
        async with self._http() as http:
            resp = await http.post(f"/v1/rides/{ride_id}/accept", headers=self._auth(driver.token))
            resp.raise_for_status()

    async def set_ride_status(self, driver_token: str, ride_id: str, status: str) -> None:
        async with self._http() as http:
            resp = await http.patch(
                f"/v1/rides/{ride_id}/status", headers=self._auth(driver_token), json={"status": status},
            )
            resp.raise_for_status()

    async def rate_ride(self, token: str, ride_id: str, *, stars: int = 5, comment: str = "e2e") -> None:
        async with self._http() as http:
            await http.post(
                f"/v1/rides/{ride_id}/rating", headers=self._auth(token), json={"stars": stars, "comment": comment},
            )

    # --- dispatch admin (S2S) ----------------------------------------------

    async def get_config(self) -> dict[str, Any]:
        token = await self.s2s_token()
        actor = await self.admin_id()
        async with self._http() as http:
            resp = await http.get(
                "/internal/v1/admin/dispatch/config", headers=self._s2s_headers(token, actor, write=False),
            )
            resp.raise_for_status()
            return resp.json()

    async def put_config(self, config: dict[str, Any]) -> dict[str, Any]:
        token = await self.s2s_token()
        actor = await self.admin_id()
        async with self._http() as http:
            resp = await http.put(
                "/internal/v1/admin/dispatch/config",
                headers=self._s2s_headers(token, actor, write=True),
                json=config,
            )
            resp.raise_for_status()
            return resp.json()

    async def grant_boost(self, driver_id: str, *, points: int, duration_minutes: int, reason: str) -> dict[str, Any]:
        token = await self.s2s_token()
        actor = await self.admin_id()
        async with self._http() as http:
            resp = await http.post(
                "/internal/v1/admin/dispatch/priority-boosts",
                headers=self._s2s_headers(token, actor, write=True),
                json={"driver_id": driver_id, "points": points, "duration_minutes": duration_minutes, "reason": reason},
            )
            resp.raise_for_status()
            return resp.json()

    async def driver_priority(self, driver_id: str) -> dict[str, Any]:
        token = await self.s2s_token()
        actor = await self.admin_id()
        async with self._http() as http:
            resp = await http.get(
                f"/internal/v1/admin/dispatch/drivers/{driver_id}/priority",
                headers=self._s2s_headers(token, actor, write=False),
            )
            resp.raise_for_status()
            return resp.json()

    # --- WebSocket offer observation ---------------------------------------

    async def observe_wave(
        self, drivers: list[DriverActor], request_ride_coro, *, seconds: float | None = None,
    ) -> tuple[str, list[str]]:
        """Open every driver's WS FIRST (offers are never replayed), then run
        `request_ride_coro()` to create the ride, then return
        `(ride_id, [names that received ride.new_request])` in arrival order.

        With dispatch config `offer_wave_size=1`, the single returned name is the
        top-ranked driver — which is how ETA-ranking and the priority cap are
        asserted end-to-end."""
        import websockets  # local import: keeps test collection working if the lib is absent

        seconds = seconds or self.config.ws_collect_seconds
        received: list[str] = []
        lock = asyncio.Lock()
        ready = [asyncio.Event() for _ in drivers]
        ride_id_box: dict[str, str] = {}

        async def watch(driver: DriverActor, ready_evt: asyncio.Event) -> None:
            url = f"{self.config.ws_url}?token={driver.token}"
            try:
                async with websockets.connect(url) as ws:
                    ready_evt.set()
                    while True:
                        raw = await asyncio.wait_for(ws.recv(), timeout=seconds)
                        event = json.loads(raw)
                        rid = ride_id_box.get("id")
                        if event.get("event") == "ride.new_request" and rid and str(event.get("ride_id")) == rid:
                            async with lock:
                                if driver.name not in received:
                                    received.append(driver.name)
                            return
            except TimeoutError:
                return
            except Exception:  # noqa: BLE001 — a dropped socket just means "no offer observed"
                ready_evt.set()
                return

        watchers = [asyncio.create_task(watch(d, ready[i])) for i, d in enumerate(drivers)]
        await asyncio.gather(*(evt.wait() for evt in ready))  # all sockets open before we request
        ride_id_box["id"] = await request_ride_coro()
        await asyncio.gather(*watchers)
        return ride_id_box["id"], received
