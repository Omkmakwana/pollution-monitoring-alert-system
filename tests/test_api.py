import time

from app.config import settings


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_station_reading_aqi_alert_flow(client):
    suffix = str(int(time.time() * 1000))

    station_payload = {
        "name": f"Station-{suffix}",
        "city": "Metro City",
        "latitude": 19.07,
        "longitude": 72.87,
    }
    station_resp = client.post("/stations", json=station_payload)
    assert station_resp.status_code == 201
    station_id = station_resp.json()["id"]

    rule_payload = {
        "pollutant": "PM2.5",
        "threshold": 100,
        "duration_minutes": 1,
        "severity": "critical",
    }
    rule_resp = client.post("/alert-rules", json=rule_payload)
    assert rule_resp.status_code == 201

    reading_pm25 = {
        "station_id": station_id,
        "pollutant": "PM2.5",
        "value": 120.0,
    }
    read_resp = client.post("/readings", json=reading_pm25)
    assert read_resp.status_code == 201

    reading_pm10 = {
        "station_id": station_id,
        "pollutant": "PM10",
        "value": 60.0,
    }
    read_resp_2 = client.post("/readings", json=reading_pm10)
    assert read_resp_2.status_code == 201

    latest_aqi = client.get(f"/stations/{station_id}/aqi/latest")
    assert latest_aqi.status_code == 200
    assert latest_aqi.json()["aqi"] >= 0

    alerts_resp = client.get("/alerts")
    assert alerts_resp.status_code == 200
    station_alerts = [item for item in alerts_resp.json() if item["station_id"] == station_id]
    assert len(station_alerts) >= 1

    alert_id = station_alerts[0]["id"]
    ack_resp = client.post(f"/alerts/{alert_id}/ack")
    assert ack_resp.status_code == 200
    assert ack_resp.json()["status"] == "acknowledged"


def test_subscriber_and_dashboard_summary(client):
    suffix = str(int(time.time() * 1000))

    station_payload = {
        "name": f"DashStation-{suffix}",
        "city": "Harbor City",
        "latitude": 18.52,
        "longitude": 73.86,
    }
    station_resp = client.post("/stations", json=station_payload)
    assert station_resp.status_code == 201
    station_id = station_resp.json()["id"]

    subscriber_payload = {
        "name": "Control Room",
        "channel": "email",
        "destination": f"ops-{suffix}@example.com",
    }
    sub_resp = client.post("/subscribers", json=subscriber_payload)
    assert sub_resp.status_code == 201

    readings = [
        {"station_id": station_id, "pollutant": "PM2.5", "value": 45.0},
        {"station_id": station_id, "pollutant": "PM10", "value": 80.0},
    ]
    for payload in readings:
        r = client.post("/readings", json=payload)
        assert r.status_code == 201

    summary_resp = client.get("/dashboard/summary")
    assert summary_resp.status_code == 200
    data = summary_resp.json()
    assert "stations" in data
    assert "overview" in data
    assert "cities" in data
    assert "pollutant_snapshot" in data
    assert data["overview"]["total_stations"] >= 1
    assert data["overview"]["total_subscribers"] >= 1
    assert isinstance(data["cities"], list)
    assert any(item["label"] == "PM2.5" for item in data["pollutant_snapshot"])
    assert any(item["station_id"] == station_id for item in data["stations"])

    recent_resp = client.get(f"/stations/{station_id}/readings/recent")
    assert recent_resp.status_code == 200
    assert len(recent_resp.json()) >= 2


def test_station_coordinate_validation(client):
    response = client.post(
        "/stations",
        json={
            "name": "Bad Station",
            "city": "Nowhere",
            "latitude": 120.0,
            "longitude": 72.0,
        },
    )
    assert response.status_code == 422


def test_duplicate_subscriber_is_rejected(client):
    suffix = str(int(time.time() * 1000))
    payload = {
        "name": "Ops Team",
        "channel": "email",
        "destination": f"dup-{suffix}@example.com",
    }

    first = client.post("/subscribers", json=payload)
    assert first.status_code == 201

    second = client.post("/subscribers", json=payload)
    assert second.status_code == 409


def test_subscriber_destination_validation(client):
    bad_email = client.post(
        "/subscribers",
        json={"name": "Ops", "channel": "email", "destination": "not-an-email"},
    )
    assert bad_email.status_code == 422

    bad_sms = client.post(
        "/subscribers",
        json={"name": "Ops", "channel": "sms", "destination": "1234567890"},
    )
    assert bad_sms.status_code == 422


def test_recent_readings_limit_validation(client):
    suffix = str(int(time.time() * 1000))

    station_resp = client.post(
        "/stations",
        json={
            "name": f"LimitStation-{suffix}",
            "city": "Hill Valley",
            "latitude": 18.5,
            "longitude": 73.9,
        },
    )
    assert station_resp.status_code == 201
    station_id = station_resp.json()["id"]

    response = client.get(f"/stations/{station_id}/readings/recent?limit=0")
    assert response.status_code == 422


def test_pagination_and_filtering_endpoints(client):
    suffix = str(int(time.time() * 1000))

    s1 = client.post(
        "/stations",
        json={
            "name": f"A-{suffix}",
            "city": "CityA",
            "latitude": 18.1,
            "longitude": 72.1,
        },
    )
    assert s1.status_code == 201

    s2 = client.post(
        "/stations",
        json={
            "name": f"B-{suffix}",
            "city": "CityB",
            "latitude": 18.2,
            "longitude": 72.2,
        },
    )
    assert s2.status_code == 201

    station_id = s1.json()["id"]
    client.post(
        "/alert-rules",
        json={"pollutant": "PM2.5", "threshold": 10, "duration_minutes": 1, "severity": "high"},
    )
    client.post("/readings", json={"station_id": station_id, "pollutant": "PM2.5", "value": 15})

    stations_filtered = client.get("/stations?city=CityA&limit=1")
    assert stations_filtered.status_code == 200
    assert len(stations_filtered.json()) == 1
    assert stations_filtered.json()[0]["city"] == "CityA"

    alerts_filtered = client.get(f"/alerts?station_id={station_id}&status=open")
    assert alerts_filtered.status_code == 200
    assert all(item["station_id"] == station_id for item in alerts_filtered.json())


def test_write_endpoints_require_api_key_when_enabled(client):
    original_api_key = settings.api_key
    settings.api_key = "secret-key"
    try:
        missing_key = client.post(
            "/stations",
            json={
                "name": "Protected Station",
                "city": "SecureCity",
                "latitude": 18.8,
                "longitude": 73.0,
            },
        )
        assert missing_key.status_code == 401

        with_key = client.post(
            "/stations",
            headers={"X-API-Key": "secret-key"},
            json={
                "name": "Protected Station 2",
                "city": "SecureCity",
                "latitude": 18.9,
                "longitude": 73.1,
            },
        )
        assert with_key.status_code == 201
    finally:
        settings.api_key = original_api_key
