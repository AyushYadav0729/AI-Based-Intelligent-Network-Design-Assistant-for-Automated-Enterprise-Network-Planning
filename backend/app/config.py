"""
config.py — all tunable constants for the network design engine.
All assumption values referenced in PROJECT_SPEC.md live here as named constants.
"""
from pydantic_settings import BaseSettings
from typing import ClassVar

class Settings(BaseSettings):
    # LLM
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    llm_timeout_seconds: int = 15

    # Database
    database_url: str = "sqlite:///./netdesign.db"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

# ─── Traffic profiles (Mbps per active user, by dept_type) ───────────────────
TRAFFIC_PROFILE_MBPS: dict[str, float] = {
    "reception":     3.0,
    "hr":            3.0,
    "support":       3.0,
    "office":        5.0,
    "finance":       5.0,
    "management":    5.0,
    "engineering":  15.0,
    "lab":          20.0,
    "media":        40.0,
    "datacenter_ops": 25.0,
}

# ─── Concurrency ─────────────────────────────────────────────────────────────
CONCURRENCY: float = 0.6   # share of users active at once

# ─── Link speed options (Mbps) ───────────────────────────────────────────────
LINK_SPEEDS_MBPS: list[int] = [1_000, 10_000, 40_000]   # 1G, 10G, 40G

# ─── Target utilization per variant ──────────────────────────────────────────
TARGET_UTIL_BUDGET: float       = 0.8
TARGET_UTIL_BALANCED: float     = 0.7
TARGET_UTIL_HIGH_PERF: float    = 0.5

# ─── Oversubscription limits ──────────────────────────────────────────────────
OVERSUB_ACCESS_TO_DIST_MAX: float  = 20.0   # 20:1
OVERSUB_DIST_TO_CORE_MAX: float    =  4.0   #  4:1

# ─── Topology thresholds ─────────────────────────────────────────────────────
TOPO_STAR_MAX_USERS:  int   = 100
TOPO_STAR_MAX_FLOORS: int   =   2
TOPO_COLLAPSED_MAX_USERS:    int = 800
TOPO_COLLAPSED_MAX_FLOORS:   int =   4
TOPO_COLLAPSED_MAX_ACCESS_SW: int = 24

# ─── Wireless ────────────────────────────────────────────────────────────────
CLIENTS_PER_AP: int          = 25
WIFI_USER_RATIO: float       = 0.6
GUEST_USER_RATIO: float      = 0.2    # estimated guest user ratio relative to total planned users
WLC_THRESHOLD_APS: int       = 10   # add WLC when total APs exceed this

# ─── Port sizing ─────────────────────────────────────────────────────────────
PORT_HEADROOM_BUDGET:       float = 0.10
PORT_HEADROOM_BALANCED:     float = 0.20
PORT_HEADROOM_HIGH_PERF:    float = 0.30
ACCESS_SWITCH_SPARE_PORTS:  int   = 4    # spare/uplink-adjacent ports per access sw

PORTS_24:  int = 24
PORTS_48:  int = 48

# ─── IP addressing ───────────────────────────────────────────────────────────
BASE_NETWORK_DEFAULT: str  = "10.0.0.0/16"
POOL_EXPANSION_ORDER: list[str] = ["10.0.0.0/12", "10.0.0.0/8"]
P2P_LINK_PREFIX:  int = 30    # /30 for point-to-point links
LOOPBACK_PREFIX:  int = 32
MGMT_DEFAULT_HOSTS: int = 20  # minimum management hosts allocated for switches/routers/APs

# ─── Subnet headroom warning ─────────────────────────────────────────────────
SUBNET_LOW_HEADROOM_PCT: float = 0.85   # warn if utilization > 85%

# ─── Cost / cabling ──────────────────────────────────────────────────────────
COST_PER_DROP_USD:      float = 150.0   # per planned wired user port
RACK_UPS_ALLOWANCE_USD: float = 2000.0  # flat per rack/UPS unit
CURRENCY: str = "USD"
