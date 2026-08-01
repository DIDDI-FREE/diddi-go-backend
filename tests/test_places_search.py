from types import SimpleNamespace

import pytest

from app_base.modules.ride.presentation.router import search_places
from app_base.shared_kernel.types import GeoPoint

pytestmark = pytest.mark.unit


class FakeDiddiMap:
    def __init__(self) -> None:
        self.query = None
        self.bias = None

    async def geocode(self, query, bias=None):
        self.query = query
        self.bias = bias
        return [
            SimpleNamespace(label="Plateau, Abidjan", point=GeoPoint(lat=5.3204, lng=-4.0161)),
            SimpleNamespace(label="Plateau Dokui", point=GeoPoint(lat=5.391, lng=-4.009)),
        ]


@pytest.mark.asyncio
async def test_search_places_returns_diddimap_results_with_bias_and_limit():
    diddimap = FakeDiddiMap()

    results = await search_places(
        q="Plateau",
        bias_lat=5.3599,
        bias_lng=-4.0083,
        limit=1,
        diddimap=diddimap,
    )

    assert diddimap.query == "Plateau"
    assert diddimap.bias == GeoPoint(lat=5.3599, lng=-4.0083)
    assert len(results) == 1
    assert results[0].model_dump() == {"label": "Plateau, Abidjan", "lat": 5.3204, "lng": -4.0161}


@pytest.mark.asyncio
async def test_search_places_ignores_partial_bias():
    diddimap = FakeDiddiMap()

    await search_places(q="Yopougon", bias_lat=5.3599, bias_lng=None, limit=10, diddimap=diddimap)

    assert diddimap.bias is None
