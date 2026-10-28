"""
loader.py — Loads and validates the device catalog JSON.
Spec Section 8.
"""
from pathlib import Path
import json
from functools import lru_cache
from app.schemas.catalog import DeviceCatalog, CatalogDevice
from app.schemas.design import DeviceRole

DEFAULT_CATALOG_PATH = Path(__file__).parent / "devices.json"


def load_catalog(path: Path | str | None = None) -> DeviceCatalog:
    """Loads and validates the catalog from the given path or the default JSON."""
    file_path = Path(path) if path else DEFAULT_CATALOG_PATH
    if not file_path.exists():
        raise FileNotFoundError(f"Device catalog not found at {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return DeviceCatalog.model_validate(data)


@lru_cache(maxsize=1)
def get_catalog() -> DeviceCatalog:
    """Returns the cached validated DeviceCatalog singleton."""
    return load_catalog()


def get_devices_by_role(role: DeviceRole, catalog: DeviceCatalog | None = None) -> list[CatalogDevice]:
    """Returns devices matching the given role."""
    cat = catalog or get_catalog()
    return [d for d in cat.devices if d.role == role]


def get_device_by_id(device_id: str, catalog: DeviceCatalog | None = None) -> CatalogDevice | None:
    """Finds a device by its ID."""
    cat = catalog or get_catalog()
    for d in cat.devices:
        if d.id == device_id:
            return d
    return None

