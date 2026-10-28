"""
catalog.py — Pydantic models for the device catalog.
Spec Section 8.
"""
from typing import Literal
from pydantic import BaseModel, Field
from app.schemas.design import DeviceRole

TierLevel = Literal["low", "mid", "high"]


class PortSpec(BaseModel):
    access: int = 0
    access_speed: str = "1G"
    uplink: int = 0
    uplink_speed: str = "10G"


class CatalogDevice(BaseModel):
    id: str
    role: DeviceRole
    model: str
    tier: TierLevel
    ports: PortSpec
    poe: bool = False
    throughput_gbps: float
    layer: int = 2
    price: float
    license_price: float = 0.0
    max_aps: int | None = None
    ha_capable: bool = True


class DeviceCatalog(BaseModel):
    currency: str = "USD"
    devices: list[CatalogDevice]

