"""Geo helpers: distance, bounding boxes and hotspot grid bucketing.

Deliberately dependency-free (no PostGIS) so the same code runs against
Supabase Postgres and a local SQLite database.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

EARTH_RADIUS_M = 6_371_000.0


def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two WGS84 points, in metres."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = phi2 - phi1
    d_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


@dataclass(frozen=True)
class BoundingBox:
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float


def bounding_box(lat: float, lon: float, radius_meters: float) -> BoundingBox:
    """A lat/lon box that fully contains the circle of the given radius.

    Used as a cheap, index-friendly SQL prefilter before the exact haversine
    check is applied in Python.
    """
    lat_delta = math.degrees(radius_meters / EARTH_RADIUS_M)
    # Guard against the poles, where cos(lat) collapses to 0.
    cos_lat = max(math.cos(math.radians(lat)), 1e-6)
    lon_delta = math.degrees(radius_meters / (EARTH_RADIUS_M * cos_lat))
    return BoundingBox(
        min_lat=lat - lat_delta,
        max_lat=lat + lat_delta,
        min_lon=lon - lon_delta,
        max_lon=lon + lon_delta,
    )


def grid_cell(lat: float, lon: float, cell_meters: float) -> tuple[int, int]:
    """Snap a point to an integer grid cell of roughly `cell_meters` per side."""
    lat_step = math.degrees(cell_meters / EARTH_RADIUS_M)
    cos_lat = max(math.cos(math.radians(lat)), 1e-6)
    lon_step = math.degrees(cell_meters / (EARTH_RADIUS_M * cos_lat))
    return (math.floor(lat / lat_step), math.floor(lon / lon_step))


def grid_cell_center(
    cell: tuple[int, int], cell_meters: float, reference_lat: float
) -> tuple[float, float]:
    """Approximate centre point of a grid cell produced by `grid_cell`."""
    lat_step = math.degrees(cell_meters / EARTH_RADIUS_M)
    cos_lat = max(math.cos(math.radians(reference_lat)), 1e-6)
    lon_step = math.degrees(cell_meters / (EARTH_RADIUS_M * cos_lat))
    return (
        round((cell[0] + 0.5) * lat_step, 6),
        round((cell[1] + 0.5) * lon_step, 6),
    )


def is_within_city(
    lat: float, lon: float, center_lat: float, center_lon: float, radius_km: float
) -> bool:
    """True when the point falls inside the serviceable city radius."""
    return haversine_meters(lat, lon, center_lat, center_lon) <= radius_km * 1000
