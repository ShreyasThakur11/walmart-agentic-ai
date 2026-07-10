"""
Data generator script for the Walmart Smart Inventory & Restocking Assistant.
Generates realistic synthetic datasets representing Walmart retail operations:
1. inventory.csv
2. warehouse.csv
3. supplier.csv
4. sales_history.csv
5. transportation.csv
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# Set seed for reproducibility
np.random.seed(42)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Configuration for data size
NUM_STORES = 20
NUM_PRODUCTS = 10
NUM_WAREHOUSES = 5
NUM_SUPPLIERS = 5
NUM_DAYS_SALES = 30  # Generates 30 days of sales history

# Define items
STORES = [f"Store_{1000 + i}" for i in range(1, NUM_STORES + 1)]
WAREHOUSES = [f"WH_{200 + i}" for i in range(1, NUM_WAREHOUSES + 1)]
SUPPLIERS = [f"Supplier_{300 + i}" for i in range(1, NUM_SUPPLIERS + 1)]

PRODUCT_METADATA = [
    {"id": "Prod_001", "name": "Great Value Organic Whole Milk", "category": "Grocery", "min": 20, "max": 150, "base_cost": 2.50},
    {"id": "Prod_002", "name": "Purified Bottled Water 40-Pack", "category": "Grocery", "min": 50, "max": 400, "base_cost": 3.80},
    {"id": "Prod_003", "name": "Equate Ibuprofen 200mg", "category": "Pharmacy", "min": 15, "max": 100, "base_cost": 4.20},
    {"id": "Prod_004", "name": "Mainstays Metal Outdoor Patio Set", "category": "Home Goods", "min": 2, "max": 20, "base_cost": 120.00},
    {"id": "Prod_005", "name": "onn. 50-inch 4K UHD Smart TV", "category": "Electronics", "min": 5, "max": 30, "base_cost": 180.00},
    {"id": "Prod_006", "name": "Equate Allergy Relief Cetirizine", "category": "Pharmacy", "min": 10, "max": 80, "base_cost": 6.50},
    {"id": "Prod_007", "name": "Great Value Chocolate Chip Cookies", "category": "Grocery", "min": 30, "max": 200, "base_cost": 1.98},
    {"id": "Prod_008", "name": "HP 15.6-inch Laptop 8GB RAM", "category": "Electronics", "min": 3, "max": 25, "base_cost": 299.00},
    {"id": "Prod_009", "name": "Mainstays Bedding Set Queen", "category": "Home Goods", "min": 8, "max": 50, "base_cost": 25.00},
    {"id": "Prod_010", "name": "Athletic Works Men Running Shoes", "category": "Apparel", "min": 12, "max": 60, "base_cost": 18.50}
]

PRODUCT_IDS = [p["id"] for p in PRODUCT_METADATA]

def generate_inventory():
    records = []
    for store in STORES:
        for p in PRODUCT_METADATA:
            # Random current stock: some low (below threshold), some high, some stable
            # Seed-based deterministic scenarios for Store_1001 to Store_1005
            if store == "Store_1001" and p["id"] == "Prod_002":  # Scenario 1 Water low
                current_stock = 15
            elif store == "Store_1002" and p["id"] == "Prod_006":  # Scenario 2 Allergy low
                current_stock = 3
            elif store == "Store_1003" and p["id"] == "Prod_005":  # Scenario 3 TV low
                current_stock = 2
            elif store == "Store_1004" and p["id"] == "Prod_004":  # Scenario 4 Patio low
                current_stock = 1
            elif store == "Store_1005" and p["id"] == "Prod_001":  # Scenario 5 Milk low store 1005
                current_stock = 5
            elif store == "Store_1001" and p["id"] == "Prod_001":  # Scenario 5 Milk low store 1001
                current_stock = 8
            else:
                # Random distribution
                rand_val = np.random.rand()
                if rand_val < 0.25:
                    current_stock = np.random.randint(1, p["min"]) # Low Stock
                elif rand_val < 0.8:
                    current_stock = np.random.randint(p["min"] + 1, int(p["max"] * 0.7)) # Normal Stock
                else:
                    current_stock = np.random.randint(int(p["max"] * 0.8), p["max"]) # Overstock

            records.append({
                "StoreID": store,
                "ProductID": p["id"],
                "ProductName": p["name"],
                "CurrentStock": current_stock,
                "MinimumThreshold": p["min"],
                "MaximumCapacity": p["max"],
                "Category": p["category"]
            })
    df = pd.DataFrame(records)
    df.to_csv(DATA_DIR / "inventory.csv", index=False)
    print(f"Generated inventory.csv with {len(df)} records.")

def generate_warehouse():
    global WAREHOUSES
    # Adjust WAREHOUSES to 10 distribution centers
    WAREHOUSES = [f"WH_{200 + i}" for i in range(1, 11)]
    all_locations = [
        "Bentonville DC", "Dallas DC", "Chicago DC", "Atlanta DC", "Phoenix DC",
        "Los Angeles DC", "Seattle DC", "Miami DC", "New York DC", "Denver DC"
    ]
    wh_locations = {wh: loc for wh, loc in zip(WAREHOUSES, all_locations)}
    
    records = []
    for wh in WAREHOUSES:
        loc = wh_locations[wh]
        for p in PRODUCT_METADATA:
            if p["id"] == "Prod_006":
                available_stock = 0
            elif p["id"] == "Prod_001":
                available_stock = 12 if wh in ["WH_201", "WH_202"] else 0  # Limited milk
            else:
                available_stock = np.random.randint(100, 1000)
                
            records.append({
                "WarehouseID": wh,
                "Location": loc,
                "AvailableStock": available_stock,
                "ProductID": p["id"]
            })
            
    df = pd.DataFrame(records)
    df.to_csv(DATA_DIR / "warehouse.csv", index=False)
    print(f"Generated warehouse.csv with {len(df)} records.")

def generate_supplier():
    # Suppliers: 10 suppliers * 10 products = 100 records
    supplier_names = [
        "Dairy Farms Inc.", "Aquafina Distributors", "Equate Pharma Corp", "Mainstays Furnishings",
        "onn. Electronics Manufacturing", "Pfizer Labs Corp", "Nestle Foods", "HP Enterprise Sourcing",
        "Springs Window Fashions", "Nike Supply Logistics"
    ]
    # Adjust NUM_SUPPLIERS to 10
    global SUPPLIERS
    SUPPLIERS = [f"Supplier_{300 + i}" for i in range(1, 11)]
    sup_names = {sup: name for sup, name in zip(SUPPLIERS, supplier_names)}
    
    records = []
    for sup in SUPPLIERS:
        name = sup_names[sup]
        for p in PRODUCT_METADATA:
            # Supplier properties
            # Lead time in days
            # Special setup for Scenario 3: HP supplier has extreme lead time (e.g. 15 days) or low reliability
            if p["id"] == "Prod_005" and sup == "Supplier_305":  # Smart TV supplier
                lead_time = 14
                reliability = 0.65
                cost_factor = 0.85 # Cheaper but slow/unreliable
            elif p["id"] == "Prod_005" and sup == "Supplier_308":  # Alt TV supplier
                lead_time = 3
                reliability = 0.95
                cost_factor = 1.15 # Expensive but fast/reliable
            else:
                lead_time = np.random.randint(2, 10)
                reliability = round(np.random.uniform(0.75, 0.98), 2)
                cost_factor = round(np.random.uniform(0.9, 1.1), 2)
            
            unit_cost = round(p["base_cost"] * cost_factor, 2)
            
            records.append({
                "SupplierID": sup,
                "SupplierName": name,
                "ProductID": p["id"],
                "LeadTime": lead_time,
                "ReliabilityScore": reliability,
                "UnitCost": unit_cost
            })
            
    df = pd.DataFrame(records)
    df.to_csv(DATA_DIR / "supplier.csv", index=False)
    print(f"Generated supplier.csv with {len(df)} records.")

def generate_sales_history():
    records = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=NUM_DAYS_SALES)
    
    for i in range(NUM_DAYS_SALES):
        current_date = start_date + timedelta(days=i)
        date_str = current_date.strftime("%Y-%m-%d")
        
        # Holiday, Promotion, Season
        is_holiday = 1 if current_date.weekday() >= 5 else 0  # Weekend bias for simple mock
        # Select holiday names
        season = "Summer" if current_date.month in [6, 7, 8] else "Winter"
        
        for store in STORES:
            for p in PRODUCT_METADATA:
                is_promo = 0
                
                # Base units sold
                base_sales = np.random.randint(1, 10) if p["category"] != "Grocery" else np.random.randint(5, 20)
                
                # Apply scenarios
                # Scenario 1: Water spike pre-festival (e.g. last 5 days before festival)
                if store == "Store_1001" and p["id"] == "Prod_002" and i >= NUM_DAYS_SALES - 5:
                    is_promo = 1
                    base_sales = int(base_sales * np.random.uniform(3.0, 5.0))
                
                # Scenario 4: Patio Set Promotion
                if store == "Store_1004" and p["id"] == "Prod_004":
                    # Let's say a promo ran mid-month
                    if NUM_DAYS_SALES - 15 <= i <= NUM_DAYS_SALES - 5:
                        is_promo = 1
                        base_sales = int(base_sales * np.random.uniform(2.5, 4.0))
                        
                # Seasonality adjustment
                if season == "Summer" and p["id"] == "Prod_004": # Patio set sales higher in summer
                    base_sales = int(base_sales * 1.5)
                
                records.append({
                    "Date": date_str,
                    "StoreID": store,
                    "ProductID": p["id"],
                    "UnitsSold": base_sales,
                    "Promotion": is_promo,
                    "Holiday": is_holiday,
                    "Season": season
                })
                
    df = pd.DataFrame(records)
    df.to_csv(DATA_DIR / "sales_history.csv", index=False)
    print(f"Generated sales_history.csv with {len(df)} records.")

def generate_transportation():
    # Matrix between WAREHOUSES (10) and STORES (20) = 10 * 20 = 200 records
    records = []
    for wh in WAREHOUSES:
        for store in STORES:
            # Distance in miles
            # Let's make WH_201/WH_202 close to Store_1001-1005
            wh_num = int(wh.split("_")[1])
            store_num = int(store.split("_")[1])
            
            distance = int(abs(wh_num * 15 - store_num * 8) + np.random.randint(10, 50))
            
            # Truck availability (90% chance of Yes)
            truck_avail = "Yes" if np.random.rand() < 0.9 else "No"
            
            # Estimated Hours based on distance (avg 50 mph)
            est_hours = round(distance / 50.0 + np.random.uniform(0.5, 2.0), 1)
            
            records.append({
                "WarehouseID": wh,
                "StoreID": store,
                "Distance": distance,
                "TruckAvailability": truck_avail,
                "EstimatedHours": est_hours
            })
            
    df = pd.DataFrame(records)
    df.to_csv(DATA_DIR / "transportation.csv", index=False)
    print(f"Generated transportation.csv with {len(df)} records.")

if __name__ == "__main__":
    generate_inventory()
    generate_warehouse()
    generate_supplier()
    generate_sales_history()
    generate_transportation()
    print("All CSV datasets successfully generated.")
