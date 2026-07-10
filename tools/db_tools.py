"""
Database access tools for Walmart Smart Inventory & Restocking Assistant.
Simulates an enterprise ERP/inventory database by querying CSV files.
"""

import os
import pandas as pd
from typing import Dict, List, Optional
from pathlib import Path
import config

class DatabaseTools:
    def __init__(self):
        self.inventory_path = config.INVENTORY_CSV
        self.warehouse_path = config.WAREHOUSE_CSV
        self.supplier_path = config.SUPPLIER_CSV
        self.sales_path = config.SALES_HISTORY_CSV
        self.transportation_path = config.TRANSPORTATION_CSV

    def _read_csv(self, path: Path) -> pd.DataFrame:
        """Reads a CSV file or raises FileNotFoundError."""
        if not path.exists():
            raise FileNotFoundError(f"Database file not found: {path}. Please run the data generator first.")
        return pd.read_csv(path)

    def get_inventory(self, store_id: str, product_id: str) -> Optional[Dict]:
        """Retrieves inventory details for a specific store and product."""
        df = self._read_csv(self.inventory_path)
        row = df[(df["StoreID"] == store_id) & (df["ProductID"] == product_id)]
        if row.empty:
            return None
        return row.iloc[0].to_dict()

    def get_all_stores(self) -> List[str]:
        """Retrieves a list of all store IDs."""
        df = self._read_csv(self.inventory_path)
        return sorted(df["StoreID"].unique().tolist())

    def get_store_products(self, store_id: str) -> List[Dict]:
        """Retrieves all product inventory records for a specific store."""
        df = self._read_csv(self.inventory_path)
        store_df = df[df["StoreID"] == store_id]
        return store_df.to_dict(orient="records")

    def get_warehouse_stock(self, product_id: str) -> List[Dict]:
        """Retrieves stock availability for a product across all warehouses."""
        df = self._read_csv(self.warehouse_path)
        prod_df = df[df["ProductID"] == product_id]
        return prod_df.to_dict(orient="records")

    def get_supplier_info(self, product_id: str) -> List[Dict]:
        """Retrieves supplier quotes and lead times for a specific product."""
        df = self._read_csv(self.supplier_path)
        prod_df = df[df["ProductID"] == product_id]
        return prod_df.to_dict(orient="records")

    def get_sales_history(self, store_id: str, product_id: str) -> List[Dict]:
        """Retrieves sales history records for a store-product combination."""
        df = self._read_csv(self.sales_path)
        sales_df = df[(df["StoreID"] == store_id) & (df["ProductID"] == product_id)]
        return sales_df.to_dict(orient="records")

    def get_logistics_details(self, warehouse_id: str, store_id: str) -> Optional[Dict]:
        """Retrieves transit distance and transportation estimates."""
        df = self._read_csv(self.transportation_path)
        row = df[(df["WarehouseID"] == warehouse_id) & (df["StoreID"] == store_id)]
        if row.empty:
            return None
        return row.iloc[0].to_dict()

    def update_inventory_stock(self, store_id: str, product_id: str, qty_change: int) -> bool:
        """Updates (locally in memory for simulation) the stock levels of a product in a store."""
        try:
            df = self._read_csv(self.inventory_path)
            idx = df[(df["StoreID"] == store_id) & (df["ProductID"] == product_id)].index
            if len(idx) == 0:
                return False
            df.at[idx[0], "CurrentStock"] = max(0, df.at[idx[0], "CurrentStock"] + qty_change)
            df.to_csv(self.inventory_path, index=False)
            return True
        except Exception:
            return False
