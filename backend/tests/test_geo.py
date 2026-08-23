"""Geo maths: distance, bounding boxes, grid bucketing, service-area check."""

from __future__ import annotations

import pytest

from app.utils.geo import (
    bounding_box,
    grid_cell,
    grid_cell_center,
    haversine_meters,
    is_within_city,
)

BHOPAL_CENTER = (23.2599, 77.4126)
HABIBGANJ = (23.2331, 77.4344)
MUMBAI = (19.0760, 72.8777)


def test_haversine_zero_distance():
    assert haversine_meters(*BHOPAL_CENTER, *BHOPAL_CENTER) == pytest.approx(0, abs=1e-6)


def test_haversine_known_distance():
    # Bhopal centre to Habibganj is roughly 3.6 km.
    distance = haversine_meters(*BHOPAL_CENTER, *HABIBGANJ)
    assert 3000 < distance < 4500


def test_haversine_is_symmetric():
    forward = haversine_meters(*BHOPAL_CENTER, *HABIBGANJ)
    backward = haversine_meters(*HABIBGANJ, *BHOPAL_CENTER)
    assert forward == pytest.approx(backward)


def test_haversine_long_distance():
    # Bhopal to Mumbai is about 660 km great-circle.
    distance = haversine_meters(*BHOPAL_CENTER, *MUMBAI)
    assert 600_000 < distance < 720_000


def test_bounding_box_contains_the_circle():
    lat, lon = HABIBGANJ
    radius = 500.0
    box = bounding_box(lat, lon, radius)
    assert box.min_lat < lat < box.max_lat
    assert box.min_lon < lon < box.max_lon
    # A point at the radius due north must fall inside the box.
    north = haversine_meters(box.max_lat, lon, lat, lon)
    assert north >= radius


def test_grid_cell_groups_nearby_points():
    a = grid_cell(23.23310, 77.43440, 500)
    b = grid_cell(23.23345, 77.43455, 500)  # ~45 m away
    assert a == b


def test_grid_cell_separates_distant_points():
    a = grid_cell(23.23310, 77.43440, 500)
    b = grid_cell(23.27980, 77.39810, 500)  # ~6 km away
    assert a != b


def test_grid_cell_center_is_inside_the_cell():
    lat, lon = HABIBGANJ
    cell = grid_cell(lat, lon, 500)
    center_lat, center_lon = grid_cell_center(cell, 500, reference_lat=lat)
    # The centre must be within one cell diagonal of the original point.
    assert haversine_meters(lat, lon, center_lat, center_lon) < 800


def test_is_within_city_accepts_bhopal():
    assert is_within_city(*HABIBGANJ, *BHOPAL_CENTER, 40)


def test_is_within_city_rejects_mumbai():
    assert not is_within_city(*MUMBAI, *BHOPAL_CENTER, 40)
