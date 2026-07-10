"""
Unit tests for individual specialized operational agents.
"""

import pytest
from unittest.mock import MagicMock
from memory.state_manager import WorkflowState, InventoryState, DemandState, WarehouseAllocation, SupplierProposal
from agents.inventory_agent import InventoryAgent
from agents.demand_agent import DemandAgent
from agents.warehouse_agent import WarehouseAgent
from agents.supplier_agent import SupplierAgent
from agents.logistics_agent import LogisticsAgent
from agents.recommendation_agent import RecommendationAgent

def test_inventory_agent():
    agent = InventoryAgent()
    
    # Mock DB response
    agent.db.get_inventory = MagicMock(return_value={
        "StoreID": "Store_1001",
        "ProductID": "Prod_001",
        "ProductName": "Milk",
        "CurrentStock": 100,
        "MinimumThreshold": 20,
        "MaximumCapacity": 150,
        "Category": "Grocery"
    })
    
    state = WorkflowState(store_id="Store_1001", product_id="Prod_001")
    updated_state = agent.execute(state)
    
    assert updated_state.inventory is not None
    assert updated_state.inventory.status == "STABLE"
    assert updated_state.product_name == "Milk"

def test_demand_agent():
    agent = DemandAgent()
    agent.db.get_sales_history = MagicMock(return_value=[
        {"Date": "2026-07-01", "StoreID": "Store_1001", "ProductID": "Prod_001", "UnitsSold": 10, "Promotion": 0, "Holiday": 0, "Season": "Summer"},
        {"Date": "2026-07-02", "StoreID": "Store_1001", "ProductID": "Prod_001", "UnitsSold": 12, "Promotion": 0, "Holiday": 0, "Season": "Summer"}
    ])
    
    state = WorkflowState(store_id="Store_1001", product_id="Prod_001")
    state.inventory = InventoryState(status="UNDERSTOCK", current_stock=5, min_threshold=20, max_capacity=150)
    
    updated_state = agent.execute(state)
    
    assert updated_state.demand is not None
    assert updated_state.demand.average_daily_sales == 11.0
    assert updated_state.demand.reorder_quantity > 0

def test_warehouse_agent():
    agent = WarehouseAgent()
    agent.db.get_warehouse_stock = MagicMock(return_value=[
        {"WarehouseID": "WH_201", "Location": "Bentonville DC", "AvailableStock": 500, "ProductID": "Prod_001"}
    ])
    agent.db.get_logistics_details = MagicMock(return_value={
        "WarehouseID": "WH_201", "StoreID": "Store_1001", "Distance": 50, "TruckAvailability": "Yes", "EstimatedHours": 2.0
    })
    
    state = WorkflowState(store_id="Store_1001", product_id="Prod_001")
    state.demand = DemandState(forecast_units=80, reorder_quantity=50, average_daily_sales=10)
    
    updated_state = agent.execute(state)
    
    assert updated_state.warehouse is not None
    assert updated_state.warehouse.status == "ALLOCATED"
    assert updated_state.warehouse.transfer_qty == 50
    assert updated_state.warehouse.warehouse_id == "WH_201"

def test_supplier_agent():
    agent = SupplierAgent()
    agent.db.get_supplier_info = MagicMock(return_value=[
        {"SupplierID": "Supplier_301", "SupplierName": "Dairy Inc", "ProductID": "Prod_001", "LeadTime": 3, "ReliabilityScore": 0.95, "UnitCost": 2.50}
    ])
    
    state = WorkflowState(store_id="Store_1001", product_id="Prod_001")
    state.demand = DemandState(forecast_units=100, reorder_quantity=80, average_daily_sales=10)
    # Warehouse stock was insufficient (only 30 units transferred)
    state.warehouse = WarehouseAllocation(warehouse_id="WH_201", location="Bentonville DC", available_stock=30, distance_miles=50, transfer_time_days=0.5, transfer_qty=30, cost=10.0, status="INSUFFICIENT")
    
    updated_state = agent.execute(state)
    
    assert updated_state.supplier is not None
    assert updated_state.supplier.status == "PROPOSED"
    # Proposes 50 units (80 - 30)
    assert updated_state.supplier.order_qty == 50
    assert updated_state.supplier.supplier_id == "Supplier_301"

def test_logistics_agent():
    agent = LogisticsAgent()
    
    state = WorkflowState(store_id="Store_1001", product_id="Prod_001")
    state.inventory = InventoryState(status="CRITICAL_UNDERSTOCK", current_stock=2, min_threshold=20, max_capacity=150, stock_health="CRITICAL_UNDERSTOCK")
    state.warehouse = WarehouseAllocation(warehouse_id="WH_201", location="Bentonville DC", available_stock=100, distance_miles=150, transfer_time_days=0.5, transfer_qty=50, cost=20.0, status="ALLOCATED")
    
    updated_state = agent.execute(state)
    
    assert updated_state.logistics is not None
    assert updated_state.logistics.status == "SCHEDULED"
    assert updated_state.logistics.transport_mode == "EXPRESS_MOTOR"

def test_recommendation_agent():
    agent = RecommendationAgent()
    agent.db.get_supplier_info = MagicMock(return_value=[
        {"SupplierID": "Supplier_301", "SupplierName": "Dairy Inc", "ProductID": "Prod_001", "LeadTime": 3, "ReliabilityScore": 0.95, "UnitCost": 2.50}
    ])
    
    state = WorkflowState(store_id="Store_1001", product_id="Prod_001")
    state.inventory = InventoryState(status="UNDERSTOCK", current_stock=10, min_threshold=20, max_capacity=150)
    state.demand = DemandState(forecast_units=80, reorder_quantity=50, average_daily_sales=10)
    state.warehouse = WarehouseAllocation(warehouse_id="WH_201", location="Bentonville DC", available_stock=100, distance_miles=50, transfer_time_days=0.5, transfer_qty=50, cost=10.0, status="ALLOCATED")
    
    updated_state = agent.execute(state)
    
    assert updated_state.recommendation is not None
    assert updated_state.recommendation.action == "TRANSFER"
    assert updated_state.recommendation.risk_score > 0
    assert updated_state.recommendation.confidence_score > 0
