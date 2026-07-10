"""
Integration tests for Supervisor workflow and dynamic routing logic.
"""

import pytest
from unittest.mock import MagicMock
from memory.state_manager import WorkflowState, InventoryState, DemandState, WarehouseAllocation, SupplierProposal, LogisticsPlan, FinalRecommendation
from agents.supervisor import SupervisorAgent

def test_supervisor_stable_inventory_early_stop():
    supervisor = SupervisorAgent()
    
    # Mock Inventory Agent to return STABLE status in-place
    def mock_inventory(state):
        state.inventory = InventoryState(status="STABLE", current_stock=100, min_threshold=20, max_capacity=150, stock_health="STABLE")
        state.add_log("InventoryAgent", "Inventory is stable", "PROCEED")
        return state
    supervisor.inventory_agent.execute = MagicMock(side_effect=mock_inventory)
    
    # Mock Recommendation Agent in-place
    def mock_recommendation(state):
        state.recommendation = FinalRecommendation(action="MONITOR")
        state.add_log("RecommendationAgent", "Consolidated recommendation: MONITOR", "COMPLETE")
        return state
    supervisor.recommendation_agent.execute = MagicMock(side_effect=mock_recommendation)
    
    # Run supervisor generator
    generator = supervisor.run_workflow(
        store_id="Store_1001",
        product_id="Prod_001",
        scenario_name="Standard Assessment"
    )
    
    final_state = None
    for state in generator:
        final_state = state
        
    assert final_state is not None
    # Supervisor should stop early and only run Inventory and Recommendation agents
    assert "DemandAgent" not in final_state.routing_path
    assert "WarehouseAgent" not in final_state.routing_path
    assert "SupplierAgent" not in final_state.routing_path
    assert "LogisticsAgent" not in final_state.routing_path
    assert "InventoryAgent" in final_state.routing_path
    assert "RecommendationAgent" in final_state.routing_path
    assert final_state.is_complete

def test_supervisor_low_stock_warehouse_sufficient():
    supervisor = SupervisorAgent()
    
    # Mock Inventory in-place
    def mock_inventory(state):
        state.inventory = InventoryState(status="UNDERSTOCK", current_stock=10, min_threshold=20, max_capacity=150, stock_health="UNDERSTOCK")
        state.add_log("InventoryAgent", "Stock is low", "PROCEED")
        return state
    supervisor.inventory_agent.execute = MagicMock(side_effect=mock_inventory)
    
    # Mock Demand in-place
    def mock_demand(state):
        state.demand = DemandState(forecast_units=80, reorder_quantity=50)
        state.add_log("DemandAgent", "Demand forecast is 80, reorder 50", "PROCEED")
        return state
    supervisor.demand_agent.execute = MagicMock(side_effect=mock_demand)
    
    # Mock Warehouse in-place
    def mock_warehouse(state):
        state.warehouse = WarehouseAllocation(warehouse_id="WH_201", location="Dallas DC", available_stock=100, distance_miles=150, transfer_time_days=0.5, transfer_qty=50, cost=20.0, status="ALLOCATED")
        state.add_log("WarehouseAgent", "Warehouse stock is allocated", "PROCEED")
        return state
    supervisor.warehouse_agent.execute = MagicMock(side_effect=mock_warehouse)
    
    # Mock Logistics in-place
    def mock_logistics(state):
        state.logistics = LogisticsPlan(status="SCHEDULED", transport_mode="STANDARD_FREIGHT")
        state.add_log("LogisticsAgent", "Logistics scheduled", "PROCEED")
        return state
    supervisor.logistics_agent.execute = MagicMock(side_effect=mock_logistics)
    
    # Mock Recommendation in-place
    def mock_recommendation(state):
        state.recommendation = FinalRecommendation(action="TRANSFER")
        state.add_log("RecommendationAgent", "Consolidated recommendation: TRANSFER", "COMPLETE")
        return state
    supervisor.recommendation_agent.execute = MagicMock(side_effect=mock_recommendation)
    
    generator = supervisor.run_workflow(
        store_id="Store_1001",
        product_id="Prod_001",
        scenario_name="Standard Assessment"
    )
    
    final_state = None
    for state in generator:
        final_state = state
        
    assert final_state is not None
    # Routing path should contain Warehouse but NOT Supplier agent
    assert "InventoryAgent" in final_state.routing_path
    assert "DemandAgent" in final_state.routing_path
    assert "WarehouseAgent" in final_state.routing_path
    assert "SupplierAgent" not in final_state.routing_path
    assert "LogisticsAgent" in final_state.routing_path
    assert "RecommendationAgent" in final_state.routing_path
