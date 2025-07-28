from pydantic import BaseModel
from typing import Optional
from datetime import date, time, datetime
from decimal import Decimal


class JeccLogBase(BaseModel):
    cfs_number: Optional[int] = None
    address: Optional[str] = None
    call_type: Optional[str] = None
    log_date: date
    log_time: Optional[time] = None
    apt_suite: Optional[str] = None
    agency: Optional[str] = None
    disposition: Optional[str] = None
    incident_number: Optional[str] = None


class JeccLogCreate(JeccLogBase):
    pass


class JeccLogUpdate(JeccLogBase):
    log_date: Optional[date] = None


class JeccLog(JeccLogBase):
    id: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    geocoded_at: Optional[datetime] = None
    geocoded_address: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LogsResponse(BaseModel):
    logs: list[JeccLog]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class HealthResponse(BaseModel):
    status: str
    database: str
    cache: str