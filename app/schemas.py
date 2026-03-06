from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    city: str = Field(min_length=2, max_length=120)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class StationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    city: str
    latitude: float
    longitude: float
    is_active: bool


class ReadingCreate(BaseModel):
    station_id: int
    pollutant: str = Field(pattern=r"^(PM2\.5|PM10|CO|NO2|SO2|O3)$")
    value: float = Field(ge=0)
    timestamp: datetime | None = None


class ReadingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    station_id: int
    pollutant: str
    value: float
    timestamp: datetime
    quality_flag: str


class AQIRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    station_id: int
    aqi: int
    category: str
    timestamp: datetime


class AlertRuleCreate(BaseModel):
    pollutant: str = Field(pattern=r"^(PM2\.5|PM10|CO|NO2|SO2|O3)$")
    threshold: float = Field(gt=0)
    duration_minutes: int = Field(ge=1, le=1440)
    severity: str = Field(default="high", pattern=r"^(low|medium|high|critical)$")


class AlertRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pollutant: str
    threshold: float
    duration_minutes: int
    severity: str
    is_enabled: bool


class AlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    station_id: int
    pollutant: str
    severity: str
    message: str
    status: str
    started_at: datetime
    ended_at: datetime | None


class NotificationSubscriberCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    channel: str = Field(pattern=r"^(email|sms)$")
    destination: str = Field(min_length=3, max_length=200)

    @model_validator(mode="after")
    def validate_destination_for_channel(self) -> "NotificationSubscriberCreate":
        destination = self.destination.strip()
        if self.channel == "email":
            if "@" not in destination or destination.startswith("@") or destination.endswith("@"):
                raise ValueError("Destination must be a valid email address for email channel")
        if self.channel == "sms":
            if not destination.startswith("+") or not destination[1:].isdigit():
                raise ValueError("Destination must be in E.164 format for sms channel")

        self.destination = destination
        return self


class NotificationSubscriberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    channel: str
    destination: str
    is_active: bool
    created_at: datetime


class StationDashboardRead(BaseModel):
    station_id: int
    station_name: str
    city: str
    latitude: float
    longitude: float
    latest_aqi: int | None
    latest_category: str | None
    latest_pm25: float | None
    latest_pm10: float | None


class DashboardSummaryRead(BaseModel):
    stations: list[StationDashboardRead]
    open_alerts: int
    active_alerts: list[AlertRead]
