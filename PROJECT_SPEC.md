# AI-Based Intelligent Network Design Assistant for Automated Enterprise Network Planning

> **Purpose of this document:** Complete specification for building the project. It is written so an AI coding agent (Antigravity) can implement it phase by phase. Read Section 0 first; it contains the non-negotiable rules.

---

## 0. Rules for the implementing agent (READ FIRST)

1. **The design is deterministic.** Topology, devices, VLANs, IP subnets, routing, security, costs, and validation are computed by plain Python code. **The LLM never produces IP addresses, subnet masks, VLAN IDs, device counts, or prices.**
2. **The LLM (Gemini) only does language work:** (a) parse free-text requirements into a structured form, (b) write explanations of decisions the engine already made.
3. **The system must work with no LLM at all.** If Gemini fails, times out, or is rate-limited: input falls back to the form, and explanations fall back to template strings.
4. **Same input, same output.** The engine must be reproducible (no randomness, no time-dependent logic).
5. **All networking math uses Python's `ipaddress` module.** Never hand-roll bit math if `ipaddress` can do it.
6. **LLM output is never trusted.** Parse it as JSON, validate it with Pydantic, and let the user review it before use.
7. **Every design decision stores a machine-readable `reason_code` and parameters** so templates (and Gemini) can explain it later.
8. Keep modules small, typed (type hints), and unit-tested. Engine code must not import FastAPI or the LLM client.
9. Where this spec says "assumption", implement it as a **named constant in a config file**, not a magic number scattered in code.

---

## 1. Project summary

Users describe their organization (departments, headcount, floors, security needs, budget, growth, redundancy). The system generates a complete **single-campus enterprise LAN design**:

- Topology selection (star / collapsed core / three-tier)
- Device selection and cost estimate (from a built-in catalog)
- VLAN plan and IPv4 plan using VLSM
- Routing recommendation (static / RIP / OSPF)
- Security plan (firewall, DMZ, ACLs, NAT, VPN, port security, 802.1X)
- Bandwidth and oversubscription analysis
- Rule-based validation of the design
- Three variants: **Budget / Balanced / High-performance** with a comparison table
- Interactive network diagram with PNG/PDF export
- PDF design report and Cisco-style CLI configs
- Natural-language explanations of each decision (Gemini, with template fallback)

**Problem it addresses:** tools like Packet Tracer or GNS3 *simulate* a design you already have. This system *generates* one from high-level business requirements, explains it, and validates it.

---

## 2. Finalized decisions

| Area | Decision |
|---|---|
| App type | Web app |
| Backend | Python + **FastAPI** |
| Frontend | **React** (with Vite) |
| Persistence | **SQLite** (save, reload, compare past designs) |
| AI provider | **Google Gemini** (free-tier friendly) |
| AI role | Requirement parsing + explanations only |
| Core design logic | Deterministic rule engine |
| Input method | Structured form **plus** free-text box that auto-fills the form; user reviews before generating |
| Site scope | Single campus / building |
| Services | Wired + Wi-Fi (AP count, wireless VLANs/SSIDs) |
| Topologies | Auto-select among star, collapsed core, three-tier based on size |
| Routing | Static, RIP, or OSPF recommended by size |
| Security depth | ACLs, firewall placement, DMZ, VLAN segregation, NAT, VPN, port security, 802.1X |
| Redundancy | User input: `none` / `dual_uplink` / `full_ha` (HSRP, EtherChannel, redundant core) |
| IP addressing | IPv4 only, private ranges, VLSM, sized for growth |
| Growth | User sets growth % and horizon in years; report shows current vs future capacity |
| Bandwidth | Per-user traffic profile by department type; link speed selection; oversubscription check |
| Devices & cost | Built-in JSON catalog of representative devices with approximate prices |
| Validation | Rule-based only (overlap, exhaustion, VLAN conflicts, uplink oversubscription) |
| Alternatives | 3 variants (Budget / Balanced / High-performance) + comparison + LLM explanation |
| Diagram | Interactive graph in browser + export to PNG/PDF |
| Exports | PDF report + sample Cisco-style CLI configs (VLANs, SVIs, OSPF, ACLs) |
| UI flow | Multi-step wizard: Requirements → Review → Design results (tabs) → Export |
| LLM failure | Core works without LLM; template explanations and form-only input as fallback |
| Testing | Unit tests for VLSM engine and validator + 3–4 sample scenarios |

### Out of scope (list as "Future Work" in the report)

Multi-site/WAN/BGP, IPv6, VoIP/CCTV/IoT QoS, live vendor pricing, real device deployment, simulation of traffic. **Stretch (optional, after core is done):** Gemini design *reviewer* (advisory notes only; it never changes the design).

---

## 3. System architecture

```
┌───────────────────────────── React Frontend (Vite) ─────────────────────────────┐
│  Wizard: Requirements → Review → Results (tabs) → Export                        │
│  React Flow diagram · tables · comparison view · PNG/PDF export (frontend)      │
└──────────────────────────────────────┬──────────────────────────────────────────┘
                                       │ REST (JSON)
┌──────────────────────────────────────▼──────────────────────────────────────────┐
│                               FastAPI Backend                                   │
│  api/ routes ── services/ ── engine/ (pure Python, no web/LLM imports)          │
│                                                                                  │
│  engine pipeline:                                                                │
│   requirements → growth → bandwidth → topology → vlans → vlsm → devices         │
│                → routing → security → redundancy → validator → variants         │
│                                                                                  │
│  llm/  (Gemini client, parse + explain, with fallback templates)                │
│  exporters/ (PDF report, CLI configs, diagram image)                            │
│  db/ (SQLite via SQLAlchemy)                                                    │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### Tech stack

**Backend:** Python 3.11+, FastAPI, Uvicorn, Pydantic v2, SQLAlchemy 2 + SQLite, `ipaddress` (stdlib), NetworkX (graph model), Jinja2 (CLI config + explanation templates), ReportLab (PDF report), Matplotlib (static diagram for PDF), `google-genai` SDK for Gemini, pytest, python-dotenv.

**Frontend:** React 18 + Vite, React Router, **React Flow** (interactive diagram), `html-to-image` (PNG export), `jspdf` (diagram PDF export), Axios or fetch, a UI library such as Tailwind CSS (agent's choice), a form library (React Hook Form) for the wizard.

**Configuration (`.env`):**
```
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.5-flash      # verify the current free-tier model name in Google's docs
LLM_TIMEOUT_SECONDS=15
DATABASE_URL=sqlite:///./netdesign.db
```

---

## 4. Folder structure

```
network-design-assistant/
├── README.md
├── PROJECT_SPEC.md
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py                 # all tunable constants (thresholds, profiles, headroom)
│   │   ├── api/
│   │   │   ├── routes_design.py
│   │   │   ├── routes_llm.py
│   │   │   ├── routes_projects.py
│   │   │   └── routes_export.py
│   │   ├── schemas/                  # Pydantic models
│   │   │   ├── requirements.py
│   │   │   ├── design.py
│   │   │   └── validation.py
│   │   ├── engine/
│   │   │   ├── pipeline.py           # orchestrates all stages
│   │   │   ├── growth.py
│   │   │   ├── bandwidth.py
│   │   │   ├── topology.py
│   │   │   ├── vlans.py
│   │   │   ├── vlsm.py
│   │   │   ├── devices.py
│   │   │   ├── routing.py
│   │   │   ├── security.py
│   │   │   ├── redundancy.py
│   │   │   ├── cost.py
│   │   │   ├── validator.py
│   │   │   ├── variants.py
│   │   │   └── graph_builder.py      # nodes/edges for diagram
│   │   ├── catalog/
│   │   │   └── devices.json
│   │   ├── llm/
│   │   │   ├── client.py             # Gemini wrapper with timeout + retry
│   │   │   ├── parser.py             # free text → RequirementsInput
│   │   │   ├── explainer.py          # design → explanations
│   │   │   ├── prompts.py
│   │   │   └── fallback_templates.py # Jinja2 explanation templates
│   │   ├── exporters/
│   │   │   ├── pdf_report.py
│   │   │   ├── cli_config.py
│   │   │   ├── diagram_image.py
│   │   │   └── templates/            # Jinja2 .j2 files for IOS configs
│   │   └── db/
│   │       ├── models.py
│   │       └── session.py
│   ├── tests/
│   │   ├── test_vlsm.py
│   │   ├── test_validator.py
│   │   ├── test_topology.py
│   │   ├── test_bandwidth.py
│   │   ├── test_pipeline_scenarios.py
│   │   └── scenarios/                # school.json, hospital.json, it_company.json, small_office.json
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── pages/ (Wizard.jsx, Results.jsx, Projects.jsx)
    │   ├── components/
    │   │   ├── RequirementsForm.jsx
    │   │   ├── FreeTextBox.jsx
    │   │   ├── ReviewStep.jsx
    │   │   ├── TopologyDiagram.jsx   # React Flow
    │   │   ├── IpVlanTable.jsx
    │   │   ├── DevicesCostTable.jsx
    │   │   ├── SecurityPanel.jsx
    │   │   ├── ValidationPanel.jsx
    │   │   ├── ComparePanel.jsx
    │   │   └── ExportPanel.jsx
    │   ├── api/client.js
    │   └── App.jsx
    └── package.json
```

---

## 5. Data models (Pydantic)

### 5.1 Input

```python
class Department(BaseModel):
    name: str
    users: int                      # current headcount
    floor: int                      # 0 = ground
    dept_type: Literal["office","engineering","finance","hr","management","reception",
                       "lab","media","datacenter_ops","support"]   # drives traffic profile
    security_level: Literal["low","medium","high","critical"]
    needs_guest_access: bool = False
    wired_printers: int = 0
    notes: str = ""

class ServerSpec(BaseModel):
    count: int                      # internal servers
    public_facing: int = 0          # servers needing DMZ (web, mail)

class RequirementsInput(BaseModel):
    org_name: str
    org_type: Literal["school","hospital","it_company","corporate","government","other"]
    floors: int
    departments: list[Department]
    servers: ServerSpec
    wifi_enabled: bool = True
    wifi_user_ratio: float = 0.6    # share of users also on Wi-Fi
    guest_wifi: bool = True
    remote_access_vpn: bool = True
    internet_bandwidth_mbps: int = 200
    redundancy: Literal["none","dual_uplink","full_ha"] = "none"
    growth_percent: float = 30.0
    growth_years: int = 3
    budget: float | None = None     # in catalog currency; None = no limit
    base_network: str = "10.0.0.0/16"   # private pool; auto-expands if exhausted
```

### 5.2 Output (core structures)

```python
class Vlan(BaseModel):
    vlan_id: int; name: str; purpose: str; dept: str | None

class Subnet(BaseModel):
    vlan_id: int | None; name: str
    network: str; prefix: int; mask: str
    gateway: str; usable_hosts: int
    required_hosts: int; utilization_pct: float
    first_host: str; last_host: str; broadcast: str
    hsrp: dict | None                # {"virtual": ..., "active": ..., "standby": ...}

class DeviceItem(BaseModel):
    role: Literal["core","distribution","access","firewall","router","wlc","ap","server_switch"]
    catalog_id: str; model: str; quantity: int
    unit_price: float; total_price: float; location: str

class Decision(BaseModel):
    stage: str                      # "topology", "routing", ...
    choice: str
    reason_code: str                # e.g. "TOPO_THREE_TIER_LARGE_USERS"
    params: dict                    # numbers used in the decision
    explanation: str | None = None  # filled by Gemini or template

class ValidationIssue(BaseModel):
    code: str; severity: Literal["error","warning","info"]
    message: str; related: list[str] = []

class DesignResult(BaseModel):
    variant: Literal["budget","balanced","high_performance"]
    topology: str
    vlans: list[Vlan]
    subnets: list[Subnet]
    p2p_links: list[Subnet]
    devices: list[DeviceItem]
    routing: dict
    security: dict
    bandwidth: dict                 # per-link demand, speed, oversubscription
    cost: dict                      # breakdown + total
    capacity: dict                  # current vs future per subnet
    graph: dict                     # nodes + edges for diagram
    decisions: list[Decision]
    validation: list[ValidationIssue]
```

---

## 6. Engine pipeline and algorithms

The pipeline in `engine/pipeline.py` runs stages in order. Each stage is a pure function `(state) -> state`. All numeric thresholds live in `config.py`.

### 6.1 Growth (`growth.py`)

```
planned_users(dept) = ceil(dept.users * (1 + growth_percent/100))
```
Store **both** current and planned values. VLSM and port counts use **planned** values. The report shows current vs future capacity.

### 6.2 Bandwidth (`bandwidth.py`)

Per-user traffic profile by `dept_type` (assumption values, Mbps average per active user):

| dept_type | Mbps/user |
|---|---|
| reception, hr, support | 3 |
| office, finance, management | 5 |
| engineering | 15 |
| lab | 20 |
| media | 40 |
| datacenter_ops | 25 |

```
CONCURRENCY = 0.6                         # share of users active at once (config)
dept_demand_mbps = planned_users * mbps_per_user * CONCURRENCY
```

Aggregate upward:
- `access_switch_demand` = sum of its departments' demand
- `distribution_demand` = sum of its access switches
- `core_demand` = sum of distribution demand + server traffic + internet traffic

**Link speed selection:** choose the smallest speed from `[1G, 10G, 40G]` where `demand <= 0.7 * link_speed` (70% target utilization, config). Use EtherChannel bundles (e.g. 2×10G) before jumping speed class when `full_ha` or `dual_uplink` is set.

**Oversubscription check** (Cisco design guideline values, configurable):
- Access → Distribution: ratio ≤ **20:1**
- Distribution → Core: ratio ≤ **4:1**

```
oversub = (sum of active downlink port speeds) / uplink_capacity
```
If exceeded, the engine **first tries upgrading the uplink**; if no faster uplink exists in the catalog, the validator raises an issue.

### 6.3 Topology selection (`topology.py`)

Thresholds (assumption, in config):

```
total_planned_users, floors, access_switch_count (estimated)

if total_planned_users <= 100 and floors <= 2:
    topology = "star"
elif total_planned_users <= 800 and floors <= 4 and access_switch_count <= 24:
    topology = "collapsed_core"
else:
    topology = "three_tier"
```
Store a `Decision` with `reason_code` and the numbers used.

- **star:** one L3 switch (or router + switch) connecting access switches; firewall at edge.
- **collapsed_core:** core/distribution merged; access switches uplink to core pair (or single core if no redundancy).
- **three_tier:** core ← distribution (per floor group, roughly one pair per 2 floors or per 8 access switches) ← access.

### 6.4 VLAN plan (`vlans.py`)

| VLAN ID | Name | Notes |
|---|---|---|
| 10 | MGMT | device management |
| 20 | SERVERS | internal servers |
| 30 | DMZ | only if `public_facing > 0` |
| 40 | GUEST | only if any `needs_guest_access` or `guest_wifi` |
| 50 | WIFI-CORP | only if `wifi_enabled` |
| 100, 110, 120 … | one per department | `100 + 10*index` |
| 999 | NATIVE/BLACKHOLE | unused ports, native VLAN |

Wi-Fi SSIDs: `Corp-WiFi` → VLAN 50 (802.1X when security high), `Guest-WiFi` → VLAN 40 (isolated, rate-limited, internet only).

### 6.5 VLSM allocation (`vlsm.py`) — core algorithm

**Required hosts per subnet:**
```
required = planned_users (or planned_wifi_users / servers / etc.)
         + fixed_extras (printers, APs on that VLAN)
         + gateway_addresses   (1, or 3 if full_ha for HSRP: virtual + 2 real)
prefix   = 32 - ceil(log2(required + 2))
```

**Algorithm:**
1. Build the list of all subnet requests (department VLANs, MGMT, SERVERS, DMZ, GUEST, WIFI-CORP).
2. Sort by required size **descending** (largest first).
3. Allocate sequentially from the base pool, **aligned to the subnet's own boundary**.
4. Point-to-point links get `/30` (or `/31`) from a **separate block** (last /24 of the pool); loopbacks get `/32` from another small block.
5. If the pool is exhausted: auto-expand `10.0.0.0/16 → /12 → /8` and add an `info` decision. If even that fails, raise a validation `error`.
6. Gateway = first usable address. With HSRP: `.1` virtual, `.2` active, `.3` standby.
7. Record utilization = `required / usable_hosts`.

**Worked example:**

| Subnet | Required | Prefix | Network | Gateway |
|---|---|---|---|---|
| Engineering | 300 | /23 (510) | 10.0.0.0/23 | 10.0.0.1 |
| Finance | 120 | /25 (126) | 10.0.2.0/25 | 10.0.2.1 |
| HR | 60 | /26 (62) | 10.0.2.128/26 | 10.0.2.129 |
| Reception | 25 | /27 (30) | 10.0.2.192/27 | 10.0.2.193 |

Use `ipaddress.ip_network(...).subnets(new_prefix=...)` and check overlaps with `.overlaps()`.

**Capacity table:** for each subnet, record `current_hosts`, `planned_hosts`, `usable_hosts`, and `max_growth_percent_before_exhaustion`.

### 6.6 Device selection and sizing (`devices.py`)

**Access switches (per floor):**
```
ports_needed = floor_planned_wired_users + printers + APs_on_floor + 4 (spare/uplink-adjacent)
switch ports: use 48-port if ports_needed > 24, else 24-port
count = ceil(ports_needed / (ports_per_switch * (1 - PORT_HEADROOM)))
PORT_HEADROOM = 0.10 (budget) / 0.20 (balanced) / 0.30 (high_performance)
```
Choose PoE models when APs are present.

**Access points:**
```
aps_per_floor = max(1, ceil(floor_planned_users * wifi_user_ratio / 25))
```
(25 concurrent clients per AP, config). Add a wireless controller (or note cloud/controller-less) when total APs > 10.

**Core / distribution / firewall / router:** pick from catalog by required throughput, port counts, and speeds, choosing the cheapest model that satisfies requirements for the variant's tier. Redundancy doubles core/distribution/firewall (see 6.9).

**Cabling and misc cost (assumption):** `cost_per_drop` (per planned wired user port) and a flat rack/UPS allowance, in config.

### 6.7 Routing (`routing.py`)

```
subnet_count = number of non-P2P subnets
if topology == "star" and subnet_count <= 8 and redundancy == "none":
    routing = "static"      (default route to ISP, static routes on router)
elif subnet_count <= 8 and L3 devices <= 2 and redundancy == "none":
    routing = "static"
else:
    routing = "OSPF"        (single area 0; multi-area noted as a future option)
```
- **Inter-VLAN routing:** SVIs on the L3 core (or collapsed core); router-on-a-stick only for the smallest star designs.
- **Always output a comparison note:** RIP is evaluated and rejected for non-trivial designs (15-hop limit, slow convergence, no VLSM support in RIPv1; RIPv2 supported but outperformed by OSPF). RIP may be chosen only if the user explicitly asks (optional override flag).
- Edge: default route to ISP with `ip route 0.0.0.0 0.0.0.0 <ISP>`, redistributed/propagated into OSPF (`default-information originate`).

### 6.8 Security (`security.py`)

Security level of each department drives the policy. Base rules:

| Level | Policies |
|---|---|
| low | Standard ACL to internet, basic port security |
| medium | + inter-VLAN ACL restricting access to servers by role |
| high | + 802.1X on access ports, DHCP snooping, DAI |
| critical | + dedicated VLAN isolation, no direct internet, allow-list ACLs, logging |

Always include (when applicable):
- **Perimeter firewall** between internet and core (HA pair if `full_ha`).
- **DMZ** VLAN for public-facing servers; internet → DMZ allowed on specific ports; DMZ → internal denied.
- **Guest VLAN**: internet only; blocked from all internal subnets.
- **NAT/PAT** at the firewall for outbound traffic; static NAT for DMZ servers.
- **Remote-access VPN** on the firewall when `remote_access_vpn` is true.
- **Port security** (max MAC per port, shutdown/restrict violation) on access switches; unused ports in VLAN 999 and shut down.
- **Management hardening:** SSH only, management VLAN ACL, AAA/RADIUS recommended.
- **ACL matrix:** rows = source VLAN, columns = destination VLAN, value = permit / deny / limited (ports). The matrix is generated by rules and also drives the CLI ACLs.

### 6.9 Redundancy (`redundancy.py`)

| Level | Effect |
|---|---|
| `none` | Single core/distribution, single uplink per access switch, single firewall/ISP link |
| `dual_uplink` | Each access switch has two uplinks (EtherChannel or STP-blocked); single core, dual ISP-facing link noted |
| `full_ha` | Redundant core (and distribution in three-tier), **HSRP** per VLAN, **EtherChannel** between core pair and to distribution, redundant firewall pair, dual uplinks per access switch |

### 6.10 Variants (`variants.py`)

Run the pipeline three times with different parameter sets:

| Parameter | Budget | Balanced | High-performance |
|---|---|---|---|
| Device tier selection | cheapest satisfying | mid-tier | top tier |
| Port headroom | 10% | 20% | 30% |
| Access uplink speed | minimum that passes checks | 10G where demand > ~50% | 10G always, 40G core if available |
| Redundancy applied | user's choice | user's choice | user's choice **+ one step up** (noted in the table) |
| Target utilization | 0.8 | 0.7 | 0.5 |

Comparison table fields: total cost, topology, device counts, core/uplink speeds, redundancy, oversubscription worst case, validation issue count, and budget status (within/over budget if a budget was given).

### 6.11 Cost (`cost.py`)

`total = devices + licenses (catalog field) + cabling/drops + rack/UPS allowance`. Currency comes from the catalog (`USD` default; configurable). If `budget` is set, mark variants as within or over budget and add a `warning` if the Budget variant exceeds it.

### 6.12 Graph builder (`graph_builder.py`)

Produces a JSON graph for the UI and PDF diagram:

```json
{
  "nodes": [{"id":"fw1","type":"firewall","label":"FW-1","layer":"edge","floor":null,"model":"..."}],
  "edges": [{"source":"fw1","target":"core1","speed":"10G","type":"fiber","label":"10G"}]
}
```
Node types: `internet`, `isp_router`, `firewall`, `core`, `distribution`, `access`, `ap`, `server_switch`, `dmz`, `wlc`. Layout hint field `layer` (edge/core/distribution/access/endpoint) so the frontend can lay out top-to-bottom.

---

## 7. Validator (`validator.py`)

Rule-based, deterministic. Each rule returns zero or more `ValidationIssue`s with a stable `code`.

| Code | Severity | Check |
|---|---|---|
| `ADDR_OVERLAP` | error | Any two subnets overlap (`ip_network.overlaps`) |
| `ADDR_EXHAUSTED` | error | Address pool cannot fit all requested subnets |
| `ADDR_OUTSIDE_PRIVATE` | error | Subnet not in RFC1918 space |
| `ADDR_HOSTS_INSUFFICIENT` | error | `usable_hosts < required_hosts` for any subnet |
| `ADDR_LOW_HEADROOM` | warning | Subnet utilization > 85% after growth |
| `ADDR_GATEWAY_INVALID` | error | Gateway not inside subnet or equals network/broadcast |
| `VLAN_DUPLICATE_ID` | error | Duplicate VLAN ID |
| `VLAN_DUPLICATE_NAME` | warning | Duplicate VLAN name |
| `VLAN_RESERVED_ID` | error | Use of reserved IDs (0, 1, 1002–1005, >4094) |
| `VLAN_NO_SUBNET` | error | VLAN with no subnet (or the reverse) |
| `LINK_OVERSUB_ACCESS` | error/warning | Access uplink oversubscription > 20:1 |
| `LINK_OVERSUB_DIST` | error/warning | Distribution uplink oversubscription > 4:1 |
| `LINK_UTIL_HIGH` | warning | Link demand > target utilization |
| `PORT_INSUFFICIENT` | error | Switch ports < required ports |
| `SPOF_CORE` | warning | Single core with redundancy requested ≠ none |
| `SPOF_FIREWALL` | warning | Single firewall under `full_ha` |
| `SECURITY_NO_FIREWALL` | error | No perimeter firewall |
| `SECURITY_DMZ_MISSING` | error | Public servers exist but no DMZ |
| `SECURITY_GUEST_NOT_ISOLATED` | error | Guest VLAN can reach internal subnets |
| `SECURITY_HIGH_NO_8021X` | warning | High/critical department without 802.1X |
| `COST_OVER_BUDGET` | warning | Total cost exceeds budget |
| `CATALOG_NO_MATCH` | error | No catalog device satisfies a requirement |

The validator runs on every variant and results are shown in the Validation tab (grouped by severity), with a summary count in the comparison table.

---

## 8. Device catalog (`catalog/devices.json`)

Generic/representative devices with approximate prices (not real vendor quotes). Schema:

```json
{
  "currency": "USD",
  "devices": [
    {
      "id": "acc-24-poe-1g",
      "role": "access",
      "model": "Generic Access Switch 24-port PoE 1G, 4x10G SFP+ uplinks",
      "tier": "mid",
      "ports": {"access": 24, "access_speed": "1G", "uplink": 4, "uplink_speed": "10G"},
      "poe": true,
      "throughput_gbps": 128,
      "layer": 2,
      "price": 900,
      "license_price": 0
    }
  ]
}
```

Include at least these roles and 2–3 tiers (`low`, `mid`, `high`) each:
- `access` — 24/48-port, PoE and non-PoE, 1G ports with 1G/10G uplinks
- `distribution` — L3, 24–48 ports of 10G
- `core` — L3, 10G/40G ports, high throughput
- `firewall` — by throughput (1G / 5G / 10G), HA-capable flag
- `router` — edge router, by WAN throughput
- `ap` — Wi-Fi 6/6E AP, PoE
- `wlc` — wireless controller, max APs
- `server_switch` — 10G ToR for server VLAN

The catalog is loaded once and validated with Pydantic at startup. Prices are placeholders the user may edit.

---

## 9. LLM layer (Gemini)

**Use the `google-genai` SDK.** Verify the current model name and free-tier limits in Google's documentation at implementation time; the model is set by env var.

### 9.1 Requirement parsing (`llm/parser.py`)

- Endpoint receives free text. Gemini is instructed to return **JSON only**, matching the `RequirementsInput` schema (use structured output / JSON mode if the SDK supports it).
- Prompt rules: do not invent values; use `null` for unknown fields; do not compute anything; output only JSON.
- Backend validates with Pydantic, fills defaults for missing optional fields, and returns a `ParseResult`:
  ```json
  { "requirements": { ... }, "missing_fields": ["floors"], "uncertain_fields": ["growth_percent"], "source": "llm" }
  ```
- The frontend auto-fills the form and highlights `missing_fields` and `uncertain_fields`. **The user must confirm in the Review step.**

### 9.2 Explanations (`llm/explainer.py`)

- Input: list of `Decision` objects (stage, choice, reason_code, params), the validation summary, and variant comparison data. **Not** the raw prompt of the whole design.
- Prompt rules: "Explain only using the facts provided. Do not introduce numbers not present in the input. Do not suggest changing the design. 2–3 sentences per decision." Output: JSON mapping `decision_id → explanation`, plus a variant comparison summary paragraph.
- **Sanity guard:** after generation, check that numbers in the explanation exist in the decision params; if not, discard and use the template.

### 9.3 Fallback (`llm/fallback_templates.py`)

Jinja2 templates keyed by `reason_code`, e.g.:
```
TOPO_THREE_TIER_LARGE_USERS:
"A three-tier design was selected because the network supports {{ users }} planned users across {{ floors }} floors, which exceeds the collapsed-core limits ({{ max_users }} users / {{ max_floors }} floors)."
```
The API response includes `explanation_source: "llm" | "template"` so the UI can show which was used.

### 9.4 Error handling

Timeout (config), one retry with backoff, catch rate-limit errors, never crash the request: return the design with template explanations and a notice. Cache explanation results by hash of the decisions to save free-tier quota.

---

## 10. API endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/llm/parse` | Free text → `ParseResult` (falls back with `source:"none"` and a message if LLM unavailable) |
| POST | `/api/design/generate` | `RequirementsInput` → 3 `DesignResult` variants + comparison + explanations |
| POST | `/api/design/validate` | Re-run validator on a given design (used after edits) |
| GET | `/api/catalog` | Return device catalog |
| POST | `/api/projects` | Save project (requirements + results) |
| GET | `/api/projects` | List saved projects |
| GET | `/api/projects/{id}` | Load a project |
| DELETE | `/api/projects/{id}` | Delete a project |
| GET | `/api/projects/compare?ids=1,2` | Compare saved designs |
| POST | `/api/export/pdf` | Generate PDF report (body: project id or design + variant; optional diagram PNG base64) |
| POST | `/api/export/config` | CLI configs for a variant (ZIP or JSON by device) |
| GET | `/api/health` | Health + LLM availability flag |

`/api/design/generate` response shape:
```json
{
  "variants": {"budget": {...}, "balanced": {...}, "high_performance": {...}},
  "comparison": [ {"metric":"total_cost","budget":..,"balanced":..,"high_performance":..} ],
  "comparison_summary": "...",
  "explanation_source": "llm"
}
```

---

## 11. Database (SQLite via SQLAlchemy)

```
projects
  id INTEGER PK
  name TEXT
  org_type TEXT
  created_at DATETIME
  requirements_json TEXT       -- RequirementsInput
  results_json TEXT            -- all variants + comparison
  explanation_source TEXT
```
Keep it simple: store JSON blobs; no need to normalize.

---

## 12. Exporters

### 12.1 CLI configs (`exporters/cli_config.py`, Jinja2)

Generate **sample** Cisco IOS-style configs per device (core, distribution, access, firewall/edge router). Include a comment header: `! Generated sample, review before deployment.`

Per **L3 core/distribution**:
- hostname, management SVI, SSH
- `vlan <id>` / `name <name>`
- `interface vlan <id>` with `ip address`, `ip helper-address` (optional), HSRP `standby` lines (when `full_ha`)
- OSPF: `router ospf 1`, `router-id`, `network ... area 0`, passive interfaces on user VLANs, `default-information originate`
- ACLs from the ACL matrix applied inbound on SVIs
- EtherChannel (`channel-group ... mode active`) where applicable

Per **access switch**:
- VLAN definitions, access port ranges per department, trunk uplink(s), port security, DHCP snooping, unused ports shutdown in VLAN 999, 802.1X snippets for high-security VLANs

Per **firewall/edge**: interface zones, NAT/PAT, DMZ rules, VPN placeholder lines (clearly marked as template).

### 12.2 PDF report (`exporters/pdf_report.py`, ReportLab)

Sections: cover page → requirements summary → topology and diagram → VLAN table → IP plan with capacity (current vs future) → devices and cost → bandwidth and oversubscription → routing → security plan + ACL matrix → validation results → variant comparison → decision explanations → assumptions and limitations.

### 12.3 Diagram export

- **In browser:** React Flow canvas → PNG via `html-to-image`; PDF via `jspdf` wrapping the PNG.
- **In report:** frontend may send the PNG (base64) with the export request. If absent, backend renders a static diagram from the graph using NetworkX + Matplotlib.

---

## 13. Frontend wizard

**Step 1: Requirements.** Org info, floors, department rows (add/remove), servers, Wi-Fi/guest/VPN toggles, internet bandwidth, redundancy select, growth % and years, optional budget. Top of the page has the **free-text box** + "Auto-fill" button. If LLM is unavailable, show a small notice and keep the form usable.

**Step 2: Review.** Read-only summary of all inputs with highlights for fields filled by AI (marked "AI-filled, please verify") and missing/uncertain fields. User can go back and edit, then click **Generate design**.

**Step 3: Design results.** Variant switcher (Budget / Balanced / High-performance) and tabs:
1. **Topology** — interactive React Flow diagram (top-to-bottom layout by `layer`), node click shows device details, legend, zoom/pan, PNG/PDF buttons
2. **IP / VLAN plan** — table of VLANs and subnets (network, mask, gateway, usable hosts, utilization bar), capacity current vs future
3. **Devices & Cost** — device table with quantities and prices, cost breakdown chart, budget status
4. **Security** — firewall/DMZ/NAT/VPN summary, ACL matrix heatmap, per-department policy
5. **Validation** — issues grouped by severity with codes; green "no issues" state
6. **Compare** — side-by-side table of the three variants plus the explanation summary

Each decision shows an "Why?" expandable explanation with a small badge: *AI explanation* or *Template explanation*.

**Step 4: Export.** Buttons: Download PDF report, Download CLI configs (ZIP), Download diagram PNG/PDF, **Save project**.

**Projects page:** list saved designs; open, delete, or select two to compare.

---

## 14. Sample scenarios (for tests and demo)

Create these as JSON files in `tests/scenarios/`.

1. **Small office** — 1 floor, 3 departments (Admin 15, Sales 20, Support 15), 2 servers, `redundancy: none`, growth 20%/3y → expect `star`, static routing.
2. **School** — 3 floors; Admin 20, Staff 60, Computer Lab 80 (lab), Library 30, Students Wi-Fi heavy; guest Wi-Fi; 6 servers, 2 public (website); `dual_uplink`; growth 25%/5y → expect `collapsed_core`, OSPF.
3. **Hospital** — 4 floors; Emergency 60 (critical), Wards 150 (high), Radiology 40 (lab, critical), Pharmacy 25 (high), Admin 80 (medium), Management 20; 20 servers (patient records, critical), 3 public; `full_ha`; growth 30%/5y → expect `collapsed_core` or `three_tier` depending on thresholds, OSPF, HSRP, 802.1X.
4. **IT company** — 6 floors; Engineering 400 (engineering), QA 80, DevOps 40 (datacenter_ops), HR 20, Finance 25, Management 15, Sales 60; 40 servers; `full_ha`; growth 40%/3y → expect `three_tier`, OSPF.

Each scenario test asserts: no overlapping subnets, no `error`-severity validation issues, expected topology and routing choice, and snapshot of subnet allocations (deterministic).

---

## 15. Testing

**Unit tests (pytest):**

- `test_vlsm.py`: prefix selection for host counts (1, 2, 30, 31, 62, 63, 126, 510, 1000), sort-descending allocation, alignment, no overlaps, pool exhaustion and auto-expansion, gateway/HSRP addressing, /30 P2P allocation.
- `test_validator.py`: one test per rule code (build a bad design deliberately and assert the issue appears; good design returns no errors).
- `test_topology.py`: threshold boundaries (100, 101, 800, 801 users; 2/3/4/5 floors).
- `test_bandwidth.py`: demand aggregation, speed selection, oversubscription ratios and the uplink upgrade fallback.
- `test_pipeline_scenarios.py`: end-to-end for the four scenarios; determinism (run twice → identical JSON).
- `test_llm_fallback.py`: mock Gemini failure/timeout/invalid JSON → verify fallback templates and form-only behavior; verify numeric sanity guard rejects explanations containing unknown numbers.
- `test_exporters.py`: configs render without template errors; PDF generates a non-empty file.

**Manual / evaluation:** run the four scenarios through the UI, import the generated configs into Packet Tracer (optional bonus) to confirm syntax and connectivity.

---

## 16. Build plan for Antigravity (phases with acceptance criteria)

**Phase 1: Project skeleton**
- Create backend/frontend folders, FastAPI app with `/api/health`, React app with routing, `.env` handling.
- *Done when:* both run locally and the frontend shows backend health.

**Phase 2: Schemas and config**
- Pydantic models (Section 5), `config.py` constants, device catalog JSON and loader.
- *Done when:* sample scenario JSONs validate against `RequirementsInput`; catalog loads and validates.

**Phase 3: Core engine, part 1 (addressing)**
- `growth.py`, `vlans.py`, `vlsm.py` with full unit tests.
- *Done when:* all VLSM tests pass, including exhaustion and alignment cases.

**Phase 4: Core engine, part 2 (design)**
- `bandwidth.py`, `topology.py`, `devices.py`, `redundancy.py`, `routing.py`, `security.py`, `cost.py`, `graph_builder.py`, `pipeline.py`.
- *Done when:* all four scenarios generate a full `DesignResult` for one variant deterministically.

**Phase 5: Validator and variants**
- `validator.py` (all rules in Section 7), `variants.py` with comparison table.
- *Done when:* validator tests pass; scenarios return 3 variants with comparison.

**Phase 6: API and persistence**
- Routes for generate/validate/catalog/projects; SQLite models.
- *Done when:* generate → save → list → load → delete works via API docs (`/docs`).

**Phase 7: Frontend wizard and results**
- Requirements form, Review step, Results tabs, React Flow diagram, comparison view, projects page.
- *Done when:* a full scenario can be entered, generated, viewed in all tabs, and saved.

**Phase 8: LLM integration**
- Gemini client, parser, explainer, fallback templates, sanity guard, caching, free-text box in UI.
- *Done when:* free text auto-fills the form; explanations show up; with the API key removed, the app works fully with template explanations.

**Phase 9: Exporters**
- CLI config templates, PDF report, diagram PNG/PDF export.
- *Done when:* all exports download and open correctly for every scenario.

**Phase 10: Polish and documentation**
- Error states, loading states, responsive layout, README with setup steps, demo script using the four scenarios, final assumptions and limitations list.

**Phase 11 (stretch): Gemini design reviewer**
- New module `llm/reviewer.py` and a `POST /api/design/review` endpoint. Input: the final design summary. Output: advisory notes (e.g. single points of failure, missing hardening). Displayed in a separate "AI Review" panel labeled **advisory only**; it must **never modify the design or the validator results**.
- *Done when:* reviewer is optional, off by default, and fails gracefully.

---

## 17. Assumptions and defaults (all editable in `config.py`)

| Assumption | Default |
|---|---|
| Concurrency (active users at once) | 0.6 |
| Traffic profile (Mbps/user) | Table in 6.2 |
| Target link utilization | 0.5 / 0.7 / 0.8 by variant |
| Access:Distribution oversubscription limit | 20:1 |
| Distribution:Core oversubscription limit | 4:1 |
| Topology thresholds | star ≤100 users and ≤2 floors; collapsed core ≤800 users, ≤4 floors, ≤24 access switches; else three-tier |
| Clients per AP | 25 |
| Wi-Fi user ratio | 0.6 |
| Port headroom | 10% / 20% / 30% |
| Subnet low-headroom warning | utilization > 85% |
| Currency | USD (catalog-level setting) |
| Base address pool | 10.0.0.0/16, expands to /12 then /8 |
| Routing | static (small) / OSPF area 0 (otherwise) |
| Cabling cost | per-drop allowance in config |

---

## 18. Limitations and future work (include in the report)

- Single-site LAN only; no WAN, BGP, or multi-site design
- IPv4 only; IPv6 / dual-stack planned as an extension
- Device catalog is representative, not live vendor pricing
- Bandwidth model uses planning estimates, not measured traffic
- No VoIP/CCTV/IoT QoS modelling
- Configs are samples and require review before deployment
- Optional extensions: Gemini design reviewer, multi-area OSPF, IPv6, multi-site WAN, importing/exporting to Packet Tracer or GNS3 topology files, user accounts

---

## 19. Suggested demo flow (for presentation or viva)

1. Type free text: *"Hospital with 4 floors and about 400 staff, critical emergency and radiology departments, 20 servers, full redundancy, 30% growth over 5 years."* → show the form auto-filling and the Review step.
2. Generate the design → show the three variants and the comparison table.
3. Walk through Topology, then the VLSM table (show current vs future capacity), then Security and the ACL matrix.
4. Show the Validation tab; deliberately break an input (e.g. shrink the base pool) to show validator errors.
5. Show an explanation with the AI/Template badge; disable the API key to show the fallback.
6. Export the PDF report and CLI configs.
7. Emphasize: *the AI interprets and explains; deterministic algorithms design and the validator verifies.*
