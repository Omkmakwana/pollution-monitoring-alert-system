from app.aqi import calculate_aqi


def test_calculate_aqi_pm25_only():
    aqi, category = calculate_aqi(pm25=40.0, pm10=None)
    assert aqi >= 101
    assert category == "Unhealthy for Sensitive Groups"


def test_calculate_aqi_uses_worst_pollutant():
    aqi, category = calculate_aqi(pm25=20.0, pm10=300.0)
    assert aqi >= 150
    assert category in {"Unhealthy", "Very Unhealthy"}
