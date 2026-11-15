# Feature 15: Interactive Geospatial Physical Lattice & Maritime Map

## Executive Overview
Supply chain risk is inherently geographical. Abstract network graph diagrams cannot convey the acute vulnerability of maritime straits, seismic fault lines, or localized factory clusters.

The **Interactive Geospatial World Map** projects the network onto a high-performance, dark-mode SVG Mercator world map (WGS84 projection). It plots semiconductor wafer fabs, critical assembly plants, maritime choke points (Taiwan Strait, Malacca, Suez, Panama), and global container ports with pulsing logistics transit arcs and interactive facility inspection drawers.

---

## Visual & Functional Capabilities

### 1. Geospatial Entity Types & Color Codes
- **Silicon GigaFabs (Cyan)**: TSMC Fab 18 (Tainan, Taiwan), TSMC Fab 21 (Phoenix, Arizona), Intel Ocotillo Fab 42, Samsung Austin.
- **Assembly Mega-Complexes (Purple)**: Foxconn Zhengzhou ("iPhone City"), Pegatron Shanghai.
- **Maritime Choke Points (Rose / Red Alert)**:
  - Taiwan Strait Corridor ($24.5^\circ\text{N}, 119.8^\circ\text{E}$)
  - Strait of Malacca ($2.5^\circ\text{N}, 101.5^\circ\text{E}$)
  - Suez Canal / Bab-el-Mandeb ($29.9^\circ\text{N}, 32.5^\circ\text{E}$)
- **Global Container Gateways (Blue)**: Port of Los Angeles / Long Beach, Port of Rotterdam, Port of Kaohsiung.

### 2. Supply Transit Arcs (Quadratic Bézier Curves)
Logistics shipping lanes between suppliers and destination assembly ports are drawn as dynamic quadratic Bézier curves with pulsing dashes indicating freight modality:
- `AIR_FREIGHT`: Rapid high-value components (e.g. TSM Fab 18 $\to$ Foxconn Zhengzhou).
- `CONTAINER_SHIP`: High-volume maritime freight (e.g. Foxconn $\to$ Port of Long Beach).
- `MARITIME_CORRIDOR`: Transit lanes transiting strategic choke points.

### 3. Facility Detail Inspection Drawer
Clicking any map node opens an interactive side panel revealing:
- Precise Latitude / Longitude coordinates.
- Criticality index ($0.0 - 1.0$) based on global production share.
- Inbound and outbound dependency arcs with % flow metrics.
- AIS satellite vessel traffic density and real-time choke point status.

---

## Technical Implementation

### File Locations
- **Backend Geospatial Endpoint**: `backend/app/main.py::get_geospatial_network`
- **Frontend Component**: `frontend/src/components/GeospatialMap.tsx`
- **API Endpoint**: `GET /api/v1/graph/geospatial`

### Mercator SVG Projection Formula
$$\begin{aligned}
x &= (lng + 180) \times \frac{W_{\text{map}}}{360} \\
\theta &= \text{lat} \times \frac{\pi}{180} \\
y &= \frac{H_{\text{map}}}{2} - \frac{W_{\text{map}}}{2\pi} \cdot \ln\left(\tan\left(\frac{\pi}{4} + \frac{\theta}{2}\right)\right)
\end{aligned}$$

---

## Verification & Test Coverage
- `backend/tests/integration/test_expansion_services.py::test_alerting_and_geospatial_endpoints`
- Verified in Next.js production build (`npm run build`) with zero linting errors.
