"""
Configuration file for the Walmart Smart Inventory & Restocking Assistant.
Sets up file paths, logging configurations, and operational constants.
"""

import os
from pathlib import Path
import logging

# Base Directory Setup
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# File Paths
INVENTORY_CSV = DATA_DIR / "inventory.csv"
WAREHOUSE_CSV = DATA_DIR / "warehouse.csv"
SUPPLIER_CSV = DATA_DIR / "supplier.csv"
SALES_HISTORY_CSV = DATA_DIR / "sales_history.csv"
TRANSPORTATION_CSV = DATA_DIR / "transportation.csv"

# Sourcing Constraints
MIN_ORDER_QTY = 10
LOGISTICS_AVG_SPEED_MPH = 50.0

# Logging Setup
LOG_FILE = LOGS_DIR / "execution.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("WalmartAgenticAI")
logger.info("Configuration loaded and logger initialized.")
