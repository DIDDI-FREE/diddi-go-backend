from dataclasses import dataclass


@dataclass(frozen=True)
class GeoPoint:
    lat: float
    lng: float


@dataclass(frozen=True)
class Pagination:
    page: int
    page_size: int
    total_items: int
    total_pages: int
