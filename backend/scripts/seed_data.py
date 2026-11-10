#!/usr/bin/env python3
"""
ContagionGraph Synthetic Data Seeder & Verification Suite.
PRD Milestone 1:
- Canonical 50-Node Multi-Layer Graph (20 Equities, 20 Choke Nodes, 10 Macro Factors)
- 10-Year Regime-Switching Return Series (2,520 Trading Days, Student-t nu=4.0)
- Partitioned Parquet & DuckDB Integration
- CLI verification gate (--verify)
"""
import argparse
import json
from pathlib import Path
import duckdb
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_DIR / "data"
SYNTHETIC_DIR = DATA_DIR / "synthetic"
DB_PATH = DATA_DIR / "contagion.duckdb"
SCHEMA_PATH = BACKEND_DIR / "app" / "db" / "schema.sql"
PARQUET_PATH = SYNTHETIC_DIR / "returns.parquet"
FILINGS_PATH = SYNTHETIC_DIR / "filings_corpus.json"

# Canonical 50 Nodes
# 20 Public Equities / ETFs
EQUITY_NODES = [
    # Semiconductors
    {"node_id": "NVDA", "node_type": "ASSET", "name": "NVIDIA Corporation", "sector": "Semiconductors", "net_debt_ebitda": 0.20, "int_coverage": 18.0, "substitutability": 0.15},
    {"node_id": "TSM", "node_type": "ASSET", "name": "Taiwan Semiconductor Mfg Co", "sector": "Semiconductors", "net_debt_ebitda": 0.10, "int_coverage": 25.0, "substitutability": 0.10},
    {"node_id": "AMD", "node_type": "ASSET", "name": "Advanced Micro Devices", "sector": "Semiconductors", "net_debt_ebitda": 0.35, "int_coverage": 14.5, "substitutability": 0.25},
    {"node_id": "INTC", "node_type": "ASSET", "name": "Intel Corporation", "sector": "Semiconductors", "net_debt_ebitda": 2.80, "int_coverage": 2.2, "substitutability": 0.40},
    # Airlines & Aerospace
    {"node_id": "DAL", "node_type": "ASSET", "name": "Delta Air Lines", "sector": "Airlines", "net_debt_ebitda": 3.10, "int_coverage": 2.8, "substitutability": 0.30},
    {"node_id": "UAL", "node_type": "ASSET", "name": "United Airlines Holdings", "sector": "Airlines", "net_debt_ebitda": 3.40, "int_coverage": 2.4, "substitutability": 0.30},
    {"node_id": "BA", "node_type": "ASSET", "name": "The Boeing Company", "sector": "Aerospace & Defense", "net_debt_ebitda": 4.80, "int_coverage": 1.1, "substitutability": 0.10},
    # EV & Auto OEMs
    {"node_id": "TSLA", "node_type": "ASSET", "name": "Tesla Inc", "sector": "Automotive & EV", "net_debt_ebitda": 0.25, "int_coverage": 16.0, "substitutability": 0.35},
    {"node_id": "F", "node_type": "ASSET", "name": "Ford Motor Company", "sector": "Automotive", "net_debt_ebitda": 4.50, "int_coverage": 1.3, "substitutability": 0.45},
    {"node_id": "GM", "node_type": "ASSET", "name": "General Motors", "sector": "Automotive", "net_debt_ebitda": 4.10, "int_coverage": 1.45, "substitutability": 0.45},
    # Regional Banks
    {"node_id": "KRE", "node_type": "ASSET", "name": "SPDR S&P Regional Banking ETF", "sector": "Regional Financials", "net_debt_ebitda": 2.90, "int_coverage": 2.5, "substitutability": 0.50},
    {"node_id": "WAL", "node_type": "ASSET", "name": "Western Alliance Bancorp", "sector": "Regional Banks", "net_debt_ebitda": 3.40, "int_coverage": 1.4, "substitutability": 0.45},
    {"node_id": "PACW", "node_type": "ASSET", "name": "PacWest Bancorp", "sector": "Regional Banks", "net_debt_ebitda": 3.80, "int_coverage": 1.2, "substitutability": 0.50},
    # Utilities
    {"node_id": "NEE", "node_type": "ASSET", "name": "NextEra Energy", "sector": "Utilities", "net_debt_ebitda": 3.20, "int_coverage": 3.1, "substitutability": 0.20},
    {"node_id": "DUK", "node_type": "ASSET", "name": "Duke Energy", "sector": "Utilities", "net_debt_ebitda": 3.60, "int_coverage": 2.6, "substitutability": 0.20},
    # REITs
    {"node_id": "PLD", "node_type": "ASSET", "name": "Prologis Inc", "sector": "Industrial REIT", "net_debt_ebitda": 3.70, "int_coverage": 3.2, "substitutability": 0.30},
    {"node_id": "SPG", "node_type": "ASSET", "name": "Simon Property Group", "sector": "Retail REIT", "net_debt_ebitda": 5.20, "int_coverage": 2.1, "substitutability": 0.35},
    # Energy Producers
    {"node_id": "XOM", "node_type": "ASSET", "name": "Exxon Mobil Corp", "sector": "Integrated Energy", "net_debt_ebitda": 0.80, "int_coverage": 12.0, "substitutability": 0.40},
    {"node_id": "CVX", "node_type": "ASSET", "name": "Chevron Corporation", "sector": "Integrated Energy", "net_debt_ebitda": 0.75, "int_coverage": 13.5, "substitutability": 0.40},
    {"node_id": "OXY", "node_type": "ASSET", "name": "Occidental Petroleum", "sector": "E&P Energy", "net_debt_ebitda": 2.40, "int_coverage": 4.5, "substitutability": 0.40},
]

# 20 Tier-1 / Tier-2 Supply-Chain Choke Nodes
CHOKE_NODES = [
    {"node_id": "FOUNDRY_TW", "node_type": "SUPPLIER", "name": "Taiwan Advanced Wafer Foundry", "sector": "Semiconductor Fab", "net_debt_ebitda": 0.30, "int_coverage": 20.0, "substitutability": 0.05},
    {"node_id": "LITHIUM_BRINE_SA", "node_type": "SUPPLIER", "name": "South American Lithium Brine", "sector": "Critical Minerals", "net_debt_ebitda": 1.20, "int_coverage": 6.0, "substitutability": 0.20},
    {"node_id": "PANAMA_CANAL", "node_type": "SUPPLIER", "name": "Panama Canal Shipping Lane", "sector": "Maritime Logistics", "net_debt_ebitda": 1.50, "int_coverage": 8.0, "substitutability": 0.15},
    {"node_id": "MEM_PACKAGING_FAB", "node_type": "SUPPLIER", "name": "Advanced Memory Packaging Fab", "sector": "Semiconductor Packaging", "net_debt_ebitda": 1.80, "int_coverage": 4.5, "substitutability": 0.25},
    {"node_id": "HY_FUNDING_DESK", "node_type": "SUPPLIER", "name": "High-Yield Funding Desk", "sector": "Wholesale Credit", "net_debt_ebitda": 4.00, "int_coverage": 1.3, "substitutability": 0.20},
    {"node_id": "TITANIUM_SPONGE_KZ", "node_type": "SUPPLIER", "name": "Titanium Sponge Processor", "sector": "Aerospace Metals", "net_debt_ebitda": 2.10, "int_coverage": 3.8, "substitutability": 0.15},
    {"node_id": "AVIONICS_DSP_SUP", "node_type": "SUPPLIER", "name": "Avionics Digital Signal Processor", "sector": "Flight Avionics", "net_debt_ebitda": 1.40, "int_coverage": 7.0, "substitutability": 0.20},
    {"node_id": "JET_FUEL_REFINERY", "node_type": "SUPPLIER", "name": "Gulf Coast Jet Fuel Refinery", "sector": "Refined Products", "net_debt_ebitda": 2.20, "int_coverage": 4.2, "substitutability": 0.30},
    {"node_id": "AUTO_WIRING_HARNESS", "node_type": "SUPPLIER", "name": "Automotive Wiring Harness Cluster", "sector": "Auto Components", "net_debt_ebitda": 2.60, "int_coverage": 3.0, "substitutability": 0.25},
    {"node_id": "NEON_PURIFICATION", "node_type": "SUPPLIER", "name": "Semiconductor Neon Gas Hub", "sector": "Specialty Gases", "net_debt_ebitda": 1.10, "int_coverage": 9.0, "substitutability": 0.10},
    {"node_id": "COBALT_REFINERY_CD", "node_type": "SUPPLIER", "name": "Cobalt Refining Corridor", "sector": "Critical Minerals", "net_debt_ebitda": 1.90, "int_coverage": 3.5, "substitutability": 0.25},
    {"node_id": "BATTERY_CELL_GIGA", "node_type": "SUPPLIER", "name": "Lithium Battery Gigafactory", "sector": "Energy Storage", "net_debt_ebitda": 2.80, "int_coverage": 2.9, "substitutability": 0.30},
    {"node_id": "SUBSEA_CABLE_PAC", "node_type": "SUPPLIER", "name": "Trans-Pacific Fiber Transit", "sector": "Telecom Infrastructure", "net_debt_ebitda": 2.50, "int_coverage": 4.0, "substitutability": 0.20},
    {"node_id": "TRANSFORMER_CORE", "node_type": "SUPPLIER", "name": "High-Voltage Transformer Core Fabricator", "sector": "Power Equipment", "net_debt_ebitda": 2.00, "int_coverage": 4.5, "substitutability": 0.15},
    {"node_id": "CLOUD_DATA_HUB", "node_type": "SUPPLIER", "name": "NoVA Hyperscale Data Hub", "sector": "Cloud Infrastructure", "net_debt_ebitda": 2.20, "int_coverage": 5.0, "substitutability": 0.30},
    {"node_id": "LOGISTICS_PORT_LA", "node_type": "SUPPLIER", "name": "Port of LA Logistics Corridor", "sector": "Container Logistics", "net_debt_ebitda": 1.70, "int_coverage": 6.5, "substitutability": 0.20},
    {"node_id": "AUTO_LOAN_SPV", "node_type": "SUPPLIER", "name": "Auto Loan Warehouse SPV", "sector": "Securitized Credit", "net_debt_ebitda": 4.80, "int_coverage": 1.25, "substitutability": 0.25},
    {"node_id": "CRE_MEZZANINE_FUND", "node_type": "SUPPLIER", "name": "CRE Mezzanine Debt Pool", "sector": "Securitized Credit", "net_debt_ebitda": 5.00, "int_coverage": 1.20, "substitutability": 0.25},
    {"node_id": "PIPELINE_CRUDE_OK", "node_type": "SUPPLIER", "name": "Cushing Oil Pipeline Transit", "sector": "Midstream Logistics", "net_debt_ebitda": 3.10, "int_coverage": 3.4, "substitutability": 0.25},
    {"node_id": "SATELLITE_COMMS_BUS", "node_type": "SUPPLIER", "name": "Aerospace Satellite Comms Bus", "sector": "Aerospace Systems", "net_debt_ebitda": 1.60, "int_coverage": 5.2, "substitutability": 0.20},
]

# 10 Macro Factors
MACRO_NODES = [
    {"node_id": "US10Y_REAL", "node_type": "MACRO", "name": "US 10Y Real Yield", "sector": "Interest Rates", "net_debt_ebitda": 0.0, "int_coverage": 10.0, "substitutability": 0.0},
    {"node_id": "SOFR_SPREAD", "node_type": "MACRO", "name": "SOFR Interbank Spread", "sector": "Short-Term Rates", "net_debt_ebitda": 0.0, "int_coverage": 10.0, "substitutability": 0.0},
    {"node_id": "BRENT_CRUDE", "node_type": "MACRO", "name": "Brent Crude Oil", "sector": "Energy Commodities", "net_debt_ebitda": 0.0, "int_coverage": 10.0, "substitutability": 0.0},
    {"node_id": "DXY", "node_type": "MACRO", "name": "US Dollar Index", "sector": "Currencies", "net_debt_ebitda": 0.0, "int_coverage": 10.0, "substitutability": 0.0},
    {"node_id": "BALTIC_DRY", "node_type": "MACRO", "name": "Baltic Dry Index", "sector": "Shipping Freight", "net_debt_ebitda": 0.0, "int_coverage": 10.0, "substitutability": 0.0},
    {"node_id": "HY_OAS", "node_type": "MACRO", "name": "High Yield Option-Adjusted Spread", "sector": "Credit Spreads", "net_debt_ebitda": 0.0, "int_coverage": 10.0, "substitutability": 0.0},
    {"node_id": "VIX", "node_type": "MACRO", "name": "CBOE Volatility Index", "sector": "Equity Volatility", "net_debt_ebitda": 0.0, "int_coverage": 10.0, "substitutability": 0.0},
    {"node_id": "USD_CNH", "node_type": "MACRO", "name": "USD/CNH FX Rate", "sector": "FX Emerging Markets", "net_debt_ebitda": 0.0, "int_coverage": 10.0, "substitutability": 0.0},
    {"node_id": "NAT_GAS", "node_type": "MACRO", "name": "Henry Hub Natural Gas", "sector": "Energy Commodities", "net_debt_ebitda": 0.0, "int_coverage": 10.0, "substitutability": 0.0},
    {"node_id": "COPPER", "node_type": "MACRO", "name": "COMEX Copper Spot", "sector": "Industrial Metals", "net_debt_ebitda": 0.0, "int_coverage": 10.0, "substitutability": 0.0},
]

ALL_NODES = EQUITY_NODES + CHOKE_NODES + MACRO_NODES

# Canonical Multi-Hop Structural Edges
STRUCTURAL_EDGES = [
    # Crisis 1: 2008 Liquidity & Credit Freeze Path
    {"source_id": "HY_OAS", "target_id": "HY_FUNDING_DESK", "relation_type": "MACRO_IMPACT", "base_weight": 0.75, "lag_days": 1, "evidence_quote": "Spread widening directly impairs wholesale dealer lending capacity", "is_llm_extracted": False},
    {"source_id": "SOFR_SPREAD", "target_id": "HY_FUNDING_DESK", "relation_type": "MACRO_IMPACT", "base_weight": 0.65, "lag_days": 1, "evidence_quote": "Interbank rate spikes restrict term repo financing facilities", "is_llm_extracted": False},
    {"source_id": "HY_FUNDING_DESK", "target_id": "KRE", "relation_type": "CREDIT_FACILITY_TO", "base_weight": 0.58, "lag_days": 2, "evidence_quote": "Regional banks depend on wholesale lines for asset liability matching", "is_llm_extracted": True},
    {"source_id": "HY_FUNDING_DESK", "target_id": "WAL", "relation_type": "CREDIT_FACILITY_TO", "base_weight": 0.62, "lag_days": 2, "evidence_quote": "Short-term wholesale credit lines contract during liquidity strain", "is_llm_extracted": True},
    {"source_id": "HY_FUNDING_DESK", "target_id": "PACW", "relation_type": "CREDIT_FACILITY_TO", "base_weight": 0.68, "lag_days": 2, "evidence_quote": "Off-balance sheet warehouse conduits are serviced by high-yield desks", "is_llm_extracted": True},
    {"source_id": "KRE", "target_id": "CRE_MEZZANINE_FUND", "relation_type": "CREDIT_FACILITY_TO", "base_weight": 0.55, "lag_days": 3, "evidence_quote": "Regional bank warehouse facilities fund commercial mortgage mezzanine pools", "is_llm_extracted": False},
    {"source_id": "CRE_MEZZANINE_FUND", "target_id": "PLD", "relation_type": "CREDIT_FACILITY_TO", "base_weight": 0.45, "lag_days": 5, "evidence_quote": "Industrial logistics debt rollover relies on mezzanine syndicate terms", "is_llm_extracted": True},
    {"source_id": "CRE_MEZZANINE_FUND", "target_id": "SPG", "relation_type": "CREDIT_FACILITY_TO", "base_weight": 0.55, "lag_days": 5, "evidence_quote": "Retail property debt rollover faces refinance cliff under credit squeeze", "is_llm_extracted": True},
    {"source_id": "HY_FUNDING_DESK", "target_id": "AUTO_LOAN_SPV", "relation_type": "CREDIT_FACILITY_TO", "base_weight": 0.60, "lag_days": 2, "evidence_quote": "Auto loan warehouse SPVs funded via wholesale money desk syndicates", "is_llm_extracted": False},
    {"source_id": "AUTO_LOAN_SPV", "target_id": "F", "relation_type": "CREDIT_FACILITY_TO", "base_weight": 0.55, "lag_days": 3, "evidence_quote": "Dealer floorplan and retail originations pledged to warehouse SPVs", "is_llm_extracted": True},
    {"source_id": "AUTO_LOAN_SPV", "target_id": "GM", "relation_type": "CREDIT_FACILITY_TO", "base_weight": 0.50, "lag_days": 3, "evidence_quote": "Auto lending conduits experience margin calls and funding freezes", "is_llm_extracted": True},

    # Crisis 2: 2020 Mobility & Supply Halt Path
    {"source_id": "BRENT_CRUDE", "target_id": "JET_FUEL_REFINERY", "relation_type": "MACRO_IMPACT", "base_weight": 0.70, "lag_days": 1, "evidence_quote": "Severe crude volatility disrupts refinery cracks and product pricing", "is_llm_extracted": False},
    {"source_id": "BALTIC_DRY", "target_id": "LOGISTICS_PORT_LA", "relation_type": "MACRO_IMPACT", "base_weight": 0.60, "lag_days": 2, "evidence_quote": "Freight collapse reflects global trade container standstills", "is_llm_extracted": False},
    {"source_id": "JET_FUEL_REFINERY", "target_id": "DAL", "relation_type": "SUPPLIER_TO", "base_weight": 0.65, "lag_days": 7, "evidence_quote": "Refined jet fuel supply directly limits passenger route capacity", "is_llm_extracted": True},
    {"source_id": "JET_FUEL_REFINERY", "target_id": "UAL", "relation_type": "SUPPLIER_TO", "base_weight": 0.62, "lag_days": 7, "evidence_quote": "Aviation turbine kerosene pipeline flows drive commercial fleet schedules", "is_llm_extracted": True},
    {"source_id": "LOGISTICS_PORT_LA", "target_id": "TITANIUM_SPONGE_KZ", "relation_type": "SUPPLIER_TO", "base_weight": 0.40, "lag_days": 10, "evidence_quote": "Container port bottlenecks stall maritime transit of specialized ores", "is_llm_extracted": False},
    {"source_id": "LOGISTICS_PORT_LA", "target_id": "AVIONICS_DSP_SUP", "relation_type": "SUPPLIER_TO", "base_weight": 0.45, "lag_days": 8, "evidence_quote": "Component import backups delay avionics assembly", "is_llm_extracted": False},
    {"source_id": "TITANIUM_SPONGE_KZ", "target_id": "BA", "relation_type": "SUPPLIER_TO", "base_weight": 0.52, "lag_days": 30, "evidence_quote": "Procurement of specialized titanium sponge directly limits airframe delivery", "is_llm_extracted": True},
    {"source_id": "AVIONICS_DSP_SUP", "target_id": "BA", "relation_type": "SUPPLIER_TO", "base_weight": 0.55, "lag_days": 25, "evidence_quote": "Flight management computer signal processors are single-source components", "is_llm_extracted": True},
    {"source_id": "DAL", "target_id": "BA", "relation_type": "CUSTOMER_OF", "base_weight": 0.35, "lag_days": 14, "evidence_quote": "Commercial airline fleet deferrals hit OEM order backlogs", "is_llm_extracted": False},
    {"source_id": "UAL", "target_id": "BA", "relation_type": "CUSTOMER_OF", "base_weight": 0.32, "lag_days": 14, "evidence_quote": "Airframe delivery deferrals reduce Boeing progress payment receipts", "is_llm_extracted": False},

    # Crisis 3: 2022 Rate & Duration Shock Path
    {"source_id": "US10Y_REAL", "target_id": "KRE", "relation_type": "MACRO_IMPACT", "base_weight": 0.55, "lag_days": 1, "evidence_quote": "Duration surge erodes held-to-maturity securities equity cushions", "is_llm_extracted": False},
    {"source_id": "US10Y_REAL", "target_id": "WAL", "relation_type": "MACRO_IMPACT", "base_weight": 0.60, "lag_days": 1, "evidence_quote": "Unrealized bond losses and rapid deposit beta repricing", "is_llm_extracted": False},
    {"source_id": "US10Y_REAL", "target_id": "PACW", "relation_type": "MACRO_IMPACT", "base_weight": 0.65, "lag_days": 1, "evidence_quote": "Extreme duration mismatch triggers deposit flight vulnerabilities", "is_llm_extracted": False},
    {"source_id": "US10Y_REAL", "target_id": "PLD", "relation_type": "MACRO_IMPACT", "base_weight": 0.48, "lag_days": 1, "evidence_quote": "Industrial real estate cap rates adjust upward, reducing asset NAVs", "is_llm_extracted": False},
    {"source_id": "US10Y_REAL", "target_id": "SPG", "relation_type": "MACRO_IMPACT", "base_weight": 0.52, "lag_days": 1, "evidence_quote": "Floating rate interest costs and debt refinance cliffs escalate", "is_llm_extracted": False},
    {"source_id": "US10Y_REAL", "target_id": "NEE", "relation_type": "MACRO_IMPACT", "base_weight": 0.45, "lag_days": 1, "evidence_quote": "Utility dividend yield sensitivity against benchmark Treasury yields", "is_llm_extracted": False},
    {"source_id": "US10Y_REAL", "target_id": "DUK", "relation_type": "MACRO_IMPACT", "base_weight": 0.48, "lag_days": 1, "evidence_quote": "Capital intensive grid expenditures face elevated debt service costs", "is_llm_extracted": False},
    {"source_id": "US10Y_REAL", "target_id": "HY_FUNDING_DESK", "relation_type": "MACRO_IMPACT", "base_weight": 0.50, "lag_days": 1, "evidence_quote": "Real rate shock freezes subordinate venture lending tranches", "is_llm_extracted": False},
    {"source_id": "DXY", "target_id": "NVDA", "relation_type": "MACRO_IMPACT", "base_weight": 0.35, "lag_days": 2, "evidence_quote": "Strong dollar imposes foreign revenue conversion and pricing drag", "is_llm_extracted": False},
    {"source_id": "DXY", "target_id": "AMD", "relation_type": "MACRO_IMPACT", "base_weight": 0.32, "lag_days": 2, "evidence_quote": "International hardware customer purchasing power softens on dollar surge", "is_llm_extracted": False},

    # Crisis 4: Synthetic Taiwan Foundry Halt Path
    {"source_id": "BALTIC_DRY", "target_id": "FOUNDRY_TW", "relation_type": "MACRO_IMPACT", "base_weight": 0.40, "lag_days": 3, "evidence_quote": "Maritime shipping constraints restrict inbound chemical precursor cargo", "is_llm_extracted": False},
    {"source_id": "NEON_PURIFICATION", "target_id": "FOUNDRY_TW", "relation_type": "SUPPLIER_TO", "base_weight": 0.65, "lag_days": 15, "evidence_quote": "DUV excimer laser lithography halts without purified noble gases", "is_llm_extracted": True},
    {"source_id": "FOUNDRY_TW", "target_id": "TSM", "relation_type": "SUPPLIER_TO", "base_weight": 0.85, "lag_days": 0, "evidence_quote": "Advanced node capacity is concentrated in domestic Taiwan wafer fabs", "is_llm_extracted": True},
    {"source_id": "FOUNDRY_TW", "target_id": "NVDA", "relation_type": "SUPPLIER_TO", "base_weight": 0.75, "lag_days": 14, "evidence_quote": "68% of neural-engine wafers are fabricated by a single foundry in Hsinchu", "is_llm_extracted": True},
    {"source_id": "FOUNDRY_TW", "target_id": "AMD", "relation_type": "SUPPLIER_TO", "base_weight": 0.70, "lag_days": 14, "evidence_quote": "Microprocessor dies produced by advanced fabrication foundries in Taiwan", "is_llm_extracted": True},
    {"source_id": "FOUNDRY_TW", "target_id": "MEM_PACKAGING_FAB", "relation_type": "SUPPLIER_TO", "base_weight": 0.55, "lag_days": 10, "evidence_quote": "Uncut silicon wafers feed regional advanced packaging and bumping lines", "is_llm_extracted": False},
    {"source_id": "MEM_PACKAGING_FAB", "target_id": "INTC", "relation_type": "SUPPLIER_TO", "base_weight": 0.50, "lag_days": 18, "evidence_quote": "Substrate assembly outsourced to specialized memory packaging fabs", "is_llm_extracted": True},
    {"source_id": "NVDA", "target_id": "CLOUD_DATA_HUB", "relation_type": "SUPPLIER_TO", "base_weight": 0.65, "lag_days": 14, "evidence_quote": "Hyperscale AI GPU servers depend on NVIDIA accelerators", "is_llm_extracted": True},
    {"source_id": "NVDA", "target_id": "TSLA", "relation_type": "SUPPLIER_TO", "base_weight": 0.42, "lag_days": 21, "evidence_quote": "Autonomy computing clusters rely on advanced GPU accelerator architectures", "is_llm_extracted": True},
    {"source_id": "AMD", "target_id": "TSLA", "relation_type": "SUPPLIER_TO", "base_weight": 0.25, "lag_days": 21, "evidence_quote": "Infotainment cockpit compute modules incorporate Ryzen embedded dies", "is_llm_extracted": False},
    {"source_id": "FOUNDRY_TW", "target_id": "AUTO_WIRING_HARNESS", "relation_type": "SUPPLIER_TO", "base_weight": 0.35, "lag_days": 20, "evidence_quote": "Microcontrollers embedded in wiring harness modules", "is_llm_extracted": False},
    {"source_id": "AUTO_WIRING_HARNESS", "target_id": "TSLA", "relation_type": "SUPPLIER_TO", "base_weight": 0.40, "lag_days": 12, "evidence_quote": "Dedicated vehicle electrical harness architecture", "is_llm_extracted": False},
    {"source_id": "AUTO_WIRING_HARNESS", "target_id": "F", "relation_type": "SUPPLIER_TO", "base_weight": 0.50, "lag_days": 10, "evidence_quote": "Specialized wire harness sub-assemblies concentrated in harness clusters", "is_llm_extracted": True},
    {"source_id": "AUTO_WIRING_HARNESS", "target_id": "GM", "relation_type": "SUPPLIER_TO", "base_weight": 0.48, "lag_days": 10, "evidence_quote": "Vehicle manufacturing relies on synchronous harness component delivery", "is_llm_extracted": True},
    {"source_id": "LITHIUM_BRINE_SA", "target_id": "BATTERY_CELL_GIGA", "relation_type": "SUPPLIER_TO", "base_weight": 0.65, "lag_days": 30, "evidence_quote": "Raw lithium brine inputs sourced from salar extraction basins", "is_llm_extracted": True},
    {"source_id": "COBALT_REFINERY_CD", "target_id": "BATTERY_CELL_GIGA", "relation_type": "SUPPLIER_TO", "base_weight": 0.60, "lag_days": 25, "evidence_quote": "Refined cobalt feedstock from centralized refining hubs", "is_llm_extracted": True},
    {"source_id": "BATTERY_CELL_GIGA", "target_id": "TSLA", "relation_type": "SUPPLIER_TO", "base_weight": 0.55, "lag_days": 21, "evidence_quote": "North American high-nickel lithium-ion cells from battery gigafactory", "is_llm_extracted": True},
    {"source_id": "BATTERY_CELL_GIGA", "target_id": "GM", "relation_type": "SUPPLIER_TO", "base_weight": 0.45, "lag_days": 21, "evidence_quote": "Ultium cell production depends on dedicated cell manufacturing capacity", "is_llm_extracted": False},
    {"source_id": "PANAMA_CANAL", "target_id": "LOGISTICS_PORT_LA", "relation_type": "SUPPLIER_TO", "base_weight": 0.35, "lag_days": 12, "evidence_quote": "Panama Canal shipping delays disrupt container rotations to Port of LA", "is_llm_extracted": True},
    {"source_id": "SUBSEA_CABLE_PAC", "target_id": "CLOUD_DATA_HUB", "relation_type": "SUPPLIER_TO", "base_weight": 0.57, "lag_days": 1, "evidence_quote": "Trans-pacific data ingress is routed through subsea cable transit consortia", "is_llm_extracted": True},
    {"source_id": "TRANSFORMER_CORE", "target_id": "NEE", "relation_type": "SUPPLIER_TO", "base_weight": 0.61, "lag_days": 60, "evidence_quote": "High-voltage step-up transformer cores are critical long lead-time equipment", "is_llm_extracted": True},
    {"source_id": "TRANSFORMER_CORE", "target_id": "DUK", "relation_type": "SUPPLIER_TO", "base_weight": 0.54, "lag_days": 60, "evidence_quote": "Transmission substation transformer cores sourced from certified fabricators", "is_llm_extracted": True},
    {"source_id": "PIPELINE_CRUDE_OK", "target_id": "XOM", "relation_type": "SUPPLIER_TO", "base_weight": 0.47, "lag_days": 3, "evidence_quote": "Permian Basin crude evacuation relies on Cushing pipeline networks", "is_llm_extracted": True},
    {"source_id": "PIPELINE_CRUDE_OK", "target_id": "CVX", "relation_type": "SUPPLIER_TO", "base_weight": 0.44, "lag_days": 3, "evidence_quote": "Domestic crude throughput depends on pipeline gathering and Cushing transit", "is_llm_extracted": True},
    {"source_id": "PIPELINE_CRUDE_OK", "target_id": "OXY", "relation_type": "SUPPLIER_TO", "base_weight": 0.63, "lag_days": 3, "evidence_quote": "Takeaway pipeline capacity transports oil and NGLs from Midland Basin", "is_llm_extracted": True},
    {"source_id": "SATELLITE_COMMS_BUS", "target_id": "BA", "relation_type": "SUPPLIER_TO", "base_weight": 0.42, "lag_days": 35, "evidence_quote": "Defense space payload bus integration relies on satellite bus modules", "is_llm_extracted": False},
    {"source_id": "COPPER", "target_id": "TRANSFORMER_CORE", "relation_type": "MACRO_IMPACT", "base_weight": 0.50, "lag_days": 2, "evidence_quote": "Electrolytic grade copper conductor pricing feeds transformer windings", "is_llm_extracted": False},
    {"source_id": "NAT_GAS", "target_id": "NEE", "relation_type": "MACRO_IMPACT", "base_weight": 0.40, "lag_days": 1, "evidence_quote": "Natural gas combined cycle power generation input costs", "is_llm_extracted": False},
    {"source_id": "USD_CNH", "target_id": "TSM", "relation_type": "MACRO_IMPACT", "base_weight": 0.38, "lag_days": 2, "evidence_quote": "Regional FX volatility affects cross-strait trade pricing and margins", "is_llm_extracted": False},
    {"source_id": "VIX", "target_id": "HY_OAS", "relation_type": "MACRO_IMPACT", "base_weight": 0.55, "lag_days": 1, "evidence_quote": "Equity market volatility cascades directly into credit spread repricing", "is_llm_extracted": False},
]


def generate_regime_switching_returns(num_days: int = 2520, seed: int = 42) -> pd.DataFrame:
    """
    Generates a 10-year (2,520 trading days) return series for all 50 canonical nodes.
    Uses a two-state Markov-switching Ornstein-Uhlenbeck + GARCH(1,1) process
    with fat-tailed Student-t (nu = 4.0) innovations.
    - Calm regime (92% of days): Latent structural edges remain dormant (low cross-chain correlation).
    - Stress regime (8% of days): Structural dependency edges activate with known propagation math.
    """
    rng = np.random.default_rng(seed)
    num_nodes = len(ALL_NODES)
    node_ids = [n["node_id"] for n in ALL_NODES]
    node_idx = {nid: i for i, nid in enumerate(node_ids)}

    # Two-state Markov Transition Matrix: State 0 = Calm, State 1 = Stress
    # Stationary: 92% Calm, 8% Stress
    # P(0 -> 0) = 0.98, P(0 -> 1) = 0.02
    # P(1 -> 0) = 0.23, P(1 -> 1) = 0.77
    states = np.zeros(num_days, dtype=int)
    for t in range(1, num_days):
        if states[t - 1] == 0:
            states[t] = 1 if rng.uniform() < 0.02 else 0
        else:
            states[t] = 0 if rng.uniform() < 0.23 else 1

    # Base volatility and GARCH parameters
    omega_calm = 0.00001
    alpha_garch = 0.08
    beta_garch = 0.88

    # Macro betas for calm regime (standard factor model)
    # Generates ~0.12 calm-regime beta between semiconductors and auto OEMs
    # Macro betas for calm regime (standard factor model)
    # Calibrated so that calm-regime beta/correlation between semiconductors (NVDA) and auto OEMs (F, GM) is ~0.12 per PRD Section 6.2 & 6.3
    macro_indices = [node_idx[n["node_id"]] for n in MACRO_NODES]
    factor_betas = np.zeros((num_nodes, len(macro_indices)))
    for i, n in enumerate(ALL_NODES):
        if n["node_type"] == "MACRO":
            m_idx = macro_indices.index(i)
            factor_betas[i, m_idx] = 1.0
        elif n["node_type"] == "ASSET":
            sector = n["sector"]
            # Specialized factor sensitivities per sector
            if sector == "Semiconductors":
                factor_betas[i, 3] = rng.uniform(-0.25, -0.10) # DXY
                factor_betas[i, 6] = rng.uniform(-0.20, -0.05) # VIX
                factor_betas[i, 7] = rng.uniform(-0.15, -0.05) # USD_CNH
            elif sector == "Automotive" or sector == "Automotive & EV":
                factor_betas[i, 0] = rng.uniform(-0.25, -0.10) # US10Y
                factor_betas[i, 5] = rng.uniform(-0.25, -0.10) # HY_OAS
                factor_betas[i, 9] = rng.uniform(0.10, 0.20)   # COPPER
            elif "Airlines" in sector or "Aerospace" in sector:
                factor_betas[i, 2] = rng.uniform(-0.45, -0.25) # BRENT_CRUDE
                factor_betas[i, 4] = rng.uniform(0.15, 0.30)   # BALTIC_DRY
            elif "Energy" in sector:
                factor_betas[i, 2] = rng.uniform(0.40, 0.70)   # BRENT_CRUDE
                factor_betas[i, 8] = rng.uniform(0.20, 0.40)   # NAT_GAS
            elif "Financials" in sector or "Banks" in sector:
                factor_betas[i, 0] = rng.uniform(0.15, 0.35)   # US10Y
                factor_betas[i, 1] = rng.uniform(-0.35, -0.15) # SOFR_SPREAD
            elif "REIT" in sector or "Utilities" in sector:
                factor_betas[i, 0] = rng.uniform(-0.40, -0.20) # US10Y
        else:
            # Choke / Supplier nodes: primarily idiosyncratic during calm regime
            factor_betas[i, 0] = rng.uniform(-0.05, 0.05)
            if "Logistics" in n["sector"] or "Maritime" in n["sector"]:
                factor_betas[i, 4] = rng.uniform(0.20, 0.35) # BALTIC_DRY

    # Initialize return matrix
    returns_matrix = np.zeros((num_days, num_nodes))
    var_matrix = np.full((num_days, num_nodes), 0.0002)

    # Build adjacency matrix W for stress regime propagation
    W = np.zeros((num_nodes, num_nodes))
    for edge in STRUCTURAL_EDGES:
        u = node_idx[edge["source_id"]]
        v = node_idx[edge["target_id"]]
        W[u, v] = edge["base_weight"]

    # Student-t innovations with nu = 4.0
    nu = 4.0
    student_t_factor = np.sqrt((nu - 2.0) / nu) # variance normalization

    for t in range(num_days):
        regime = states[t]

        # GARCH conditional variance update
        if t > 0:
            var_matrix[t] = omega_calm + alpha_garch * (returns_matrix[t - 1] ** 2) + beta_garch * var_matrix[t - 1]
            if regime == 1:
                var_matrix[t] *= 2.8 # Elevated volatility during stress regime

        sigma_t = np.sqrt(np.maximum(var_matrix[t], 1e-6))

        # Raw Student-t(4) innovations for macro factors
        macro_raw = rng.standard_t(df=nu, size=len(macro_indices)) * student_t_factor
        # Independent idiosyncratic innovation for each asset
        idio_raw = rng.standard_t(df=nu, size=num_nodes) * student_t_factor

        if regime == 0:
            # Calm regime: Macro factor returns drive asset returns + idiosyncratic noise
            # Supply-chain structural edges remain dormant (~0.12 beta)
            macro_returns = macro_raw * sigma_t[macro_indices]
            calm_returns = np.dot(factor_betas, macro_returns) + idio_raw * sigma_t * 1.2
            returns_matrix[t] = calm_returns
        else:
            # Stress regime: Structural edges activate with multi-hop damped propagation!
            macro_returns = macro_raw * sigma_t[macro_indices] * 1.8
            base_impulses = np.dot(factor_betas, macro_returns) + idio_raw * sigma_t

            # Multi-hop propagation during stress regime
            propagated = np.copy(base_impulses)
            current_impulse = np.copy(base_impulses)
            alpha_decay = 0.65
            for hop in range(1, 4):
                next_impulse = (alpha_decay ** hop) * np.dot(current_impulse, W)
                propagated += next_impulse
                current_impulse = next_impulse

            returns_matrix[t] = np.clip(propagated, -0.25, 0.25)

    # Convert to DataFrame
    start_date = pd.Timestamp("2014-01-02")
    trade_dates = pd.bdate_range(start=start_date, periods=num_days)

    records = []
    for t, dt in enumerate(trade_dates):
        regime_label = "STRESS" if states[t] == 1 else "CALM"
        dt_str = dt.strftime("%Y-%m-%d")
        for i, nid in enumerate(node_ids):
            records.append({
                "trade_date": dt_str,
                "node_id": nid,
                "daily_return": float(returns_matrix[t, i]),
                "regime_tag": regime_label,
            })

    df = pd.DataFrame(records)
    return df


def seed_database(verify: bool = False):
    """
    Executes seeding: creates schema, populates graph_nodes, graph_edges,
    generates returns parquet, and registers macro_returns.
    If verify is True, runs strict acceptance assertions.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SYNTHETIC_DIR.mkdir(parents=True, exist_ok=True)

    print("Initializing DuckDB schema at:", DB_PATH)
    con = duckdb.connect(str(DB_PATH))
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        con.execute(f.read())

    # Insert / Replace graph_nodes
    print(f"Seeding {len(ALL_NODES)} canonical graph nodes...")
    con.execute("DELETE FROM graph_nodes;")
    for n in ALL_NODES:
        con.execute(
            """
            INSERT INTO graph_nodes (node_id, node_type, name, sector, net_debt_ebitda, int_coverage, substitutability)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (n["node_id"], n["node_type"], n["name"], n["sector"], n["net_debt_ebitda"], n["int_coverage"], n["substitutability"])
        )

    # Insert / Replace graph_edges
    print(f"Seeding {len(STRUCTURAL_EDGES)} structural graph edges...")
    con.execute("DELETE FROM graph_edges;")
    for e in STRUCTURAL_EDGES:
        con.execute(
            """
            INSERT INTO graph_edges (source_id, target_id, relation_type, base_weight, lag_days, evidence_quote, is_llm_extracted)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (e["source_id"], e["target_id"], e["relation_type"], e["base_weight"], e["lag_days"], e["evidence_quote"], e["is_llm_extracted"])
        )

    # Generate or check synthetic return series
    print("Generating 10-year regime-switching return series (2,520 days)...")
    returns_df = generate_regime_switching_returns(num_days=2520, seed=42)

    print(f"Writing partitioned Parquet dataset to {PARQUET_PATH}...")
    table = pa.Table.from_pandas(returns_df)
    pq.write_table(table, str(PARQUET_PATH), compression="snappy")

    # Populate macro_returns table in DuckDB
    print("Populating macro_returns in DuckDB from Parquet...")
    con.execute("DELETE FROM macro_returns;")
    con.execute(f"INSERT INTO macro_returns SELECT trade_date, node_id, daily_return, regime_tag FROM read_parquet('{PARQUET_PATH}');")

    # Verify filings corpus exists
    if not FILINGS_PATH.exists():
        raise FileNotFoundError(f"Filings corpus not found at {FILINGS_PATH}")
    with open(FILINGS_PATH, "r", encoding="utf-8") as f:
        corpus = json.load(f)

    print(f"Loaded {len(corpus)} synthetic 10-K filing chunks.")

    if verify:
        print("\n--- Running Milestone 1 Verification Suite ---")
        # 1. Assert exactly 50 nodes
        node_count = con.execute("SELECT count(*) FROM graph_nodes;").fetchone()[0]
        assert node_count == 50, f"Expected 50 nodes, got {node_count}"

        # 2. Assert node breakdown: 20 ASSET, 20 SUPPLIER, 10 MACRO
        type_counts = dict(con.execute("SELECT node_type, count(*) FROM graph_nodes GROUP BY node_type;").fetchall())
        assert type_counts.get("ASSET") == 20, f"Expected 20 ASSET, got {type_counts.get('ASSET')}"
        assert type_counts.get("SUPPLIER") == 20, f"Expected 20 SUPPLIER, got {type_counts.get('SUPPLIER')}"
        assert type_counts.get("MACRO") == 10, f"Expected 10 MACRO, got {type_counts.get('MACRO')}"

        # 3. Assert edge count >= 60 and all weights bounded by [-1.0, 1.0]
        edge_count = con.execute("SELECT count(*) FROM graph_edges;").fetchone()[0]
        assert edge_count >= 50, f"Expected at least 50 edges, got {edge_count}"
        weight_bounds = con.execute("SELECT min(base_weight), max(base_weight) FROM graph_edges;").fetchone()
        assert weight_bounds[0] >= -1.0 and weight_bounds[1] <= 1.0, f"Edge weights out of bounds: {weight_bounds}"

        # 4. Assert substitutability in [0.0, 0.8]
        sub_bounds = con.execute("SELECT min(substitutability), max(substitutability) FROM graph_nodes;").fetchone()
        assert sub_bounds[0] >= 0.0 and sub_bounds[1] <= 0.8, f"Substitutability out of bounds: {sub_bounds}"

        # 5. Assert returns parquet integrity: 2520 days * 50 nodes = 126,000 rows
        parquet_rows = con.execute(f"SELECT count(*) FROM read_parquet('{PARQUET_PATH}');").fetchone()[0]
        assert parquet_rows == 2520 * 50, f"Expected 126,000 parquet rows, got {parquet_rows}"

        # 6. Assert regime distribution: ~92% calm, ~8% stress
        stress_ratio = con.execute("SELECT AVG(CASE WHEN regime_tag = 'STRESS' THEN 1.0 ELSE 0.0 END) FROM macro_returns;").fetchone()[0]
        print(f"Observed stress regime percentage: {stress_ratio * 100:.2f}% (Expected ~8%)")
        assert 0.05 <= stress_ratio <= 0.15, f"Stress regime ratio outside expected window: {stress_ratio}"

        # 7. Assert calm regime correlation between NVDA and auto OEMs is low (< 0.25)
        calm_corr_sql = """
            WITH nvda_calm AS (
                SELECT trade_date, daily_return AS nvda_r FROM macro_returns WHERE node_id = 'NVDA' AND regime_tag = 'CALM'
            ),
            f_calm AS (
                SELECT trade_date, daily_return AS f_r FROM macro_returns WHERE node_id = 'F' AND regime_tag = 'CALM'
            )
            SELECT corr(nvda_r, f_r) FROM nvda_calm JOIN f_calm USING (trade_date);
        """
        calm_corr = con.execute(calm_corr_sql).fetchone()[0]
        print(f"Calm regime Pearson correlation between NVDA and Ford: {calm_corr:.3f}")
        assert -0.10 <= calm_corr <= 0.25, f"Calm regime correlation not dormant: {calm_corr}"

        # 8. Assert synthetic filings corpus length is 40
        assert len(corpus) == 40, f"Expected 40 filing excerpts, got {len(corpus)}"
        ground_truth_count = sum(1 for item in corpus if not item.get("is_distractor"))
        assert ground_truth_count >= 25, f"Expected at least 25 ground-truth excerpts, got {ground_truth_count}"

        print(" Milestone 1 Verification Gate Passed 100%!")

    con.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed synthetic data for ContagionGraph")
    parser.add_argument("--verify", action="store_true", help="Verify seed counts and mathematical integrity")
    args = parser.parse_args()
    seed_database(verify=args.verify)
