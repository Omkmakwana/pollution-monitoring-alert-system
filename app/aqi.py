from __future__ import annotations

from math import floor


PM25_BREAKPOINTS = [
    (0.0, 12.0, 0, 50, "Good"),
    (12.1, 35.4, 51, 100, "Moderate"),
    (35.5, 55.4, 101, 150, "Unhealthy for Sensitive Groups"),
    (55.5, 150.4, 151, 200, "Unhealthy"),
    (150.5, 250.4, 201, 300, "Very Unhealthy"),
    (250.5, 500.4, 301, 500, "Hazardous"),
]

PM10_BREAKPOINTS = [
    (0, 54, 0, 50, "Good"),
    (55, 154, 51, 100, "Moderate"),
    (155, 254, 101, 150, "Unhealthy for Sensitive Groups"),
    (255, 354, 151, 200, "Unhealthy"),
    (355, 424, 201, 300, "Very Unhealthy"),
    (425, 604, 301, 500, "Hazardous"),
]


def _sub_index(concentration: float, table: list[tuple[float, float, int, int, str]]) -> tuple[int, str]:
    for c_low, c_high, i_low, i_high, category in table:
        if c_low <= concentration <= c_high:
            score = ((i_high - i_low) / (c_high - c_low)) * (concentration - c_low) + i_low
            return floor(score), category
    return 500, "Hazardous"


def calculate_aqi(pm25: float | None, pm10: float | None) -> tuple[int, str]:
    candidates: list[tuple[int, str]] = []

    if pm25 is not None:
        candidates.append(_sub_index(pm25, PM25_BREAKPOINTS))
    if pm10 is not None:
        candidates.append(_sub_index(pm10, PM10_BREAKPOINTS))

    if not candidates:
        return 0, "Unknown"

    aqi, category = max(candidates, key=lambda item: item[0])
    return aqi, category
