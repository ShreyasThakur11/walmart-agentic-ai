"""
Supervisor Agent.
Serves as the main routing brain of the multi-agent system.
Coordinates execution flow dynamically, handles early stops, and tracks execution paths.
"""

import time
from typing import Generator
from memory.state_manager import WorkflowState
from agents.inventory_agent import InventoryAgent
from agents.demand_agent import DemandAgent
from agents.warehouse_agent import WarehouseAgent
from agents.supplier_agent import SupplierAgent
from agents.logistics_agent import LogisticsAgent
from agents.recommendation_agent import RecommendationAgent

class SupervisorAgent:
    def __init__(self):
        self.inventory_agent = InventoryAgent()
        self.demand_agent = DemandAgent()
        self.warehouse_agent = WarehouseAgent()
        self.supplier_agent = SupplierAgent()
        self.logistics_agent = LogisticsAgent()
        self.recommendation_agent = RecommendationAgent()

    def run_workflow(self, store_id: str, product_id: str, scenario_name: str) -> Generator[WorkflowState, None, WorkflowState]:
        """
        Runs the multi-agent orchestration loop step-by-step.
        Yields the intermediate state after each agent execution, allowing the Streamlit UI
        to display live agent execution steps.
        """
        # 1. Initialize State
        state = WorkflowState(
            store_id=store_id,
            product_id=product_id,
            scenario_name=scenario_name,
            current_step="SUPERVISOR_DECIDING"
        )
        state.add_log("Supervisor", f"Initializing multi-agent workflow for Store {store_id}, Product {product_id} under scenario: {scenario_name}")
        yield state

        # 2. Invoke Inventory Agent (Always run first)
        state.current_step = "INVENTORY_MONITORING"
        yield state
        
        state = self.inventory_agent.execute(state)
        yield state

        # Check stock health
        health = state.inventory.status if state.inventory else "UNKNOWN"
        is_low_stock = health in ["CRITICAL_UNDERSTOCK", "UNDERSTOCK"]
        
        # Decide if we need to forecast demand
        # We forecast if stock is low OR if the scenario specifies an upcoming demand surge (e.g. promo or festival)
        is_spike_scenario = any(x in scenario_name.lower() for x in ["spike", "promotion", "festival", "contention"])
        
        if not is_low_stock and not is_spike_scenario:
            state.add_log("Supervisor", "Stock is stable and no demand spike scenarios active. Routing directly to recommendation.", "ROUTE_SHORTCUT")
            state.current_step = "RECOMMENDATION_GENERATION"
            yield state
            
            state = self.recommendation_agent.execute(state)
            state.is_complete = True
            state.current_step = "COMPLETE"
            yield state
            return state

        # 3. Invoke Demand Forecast Agent
        state.current_step = "DEMAND_FORECASTING"
        yield state
        
        state = self.demand_agent.execute(state)
        yield state

        reorder_qty = state.demand.reorder_quantity if state.demand else 0
        
        if reorder_qty <= 0:
            state.add_log("Supervisor", "Forecast shows no replenishment needed. Routing directly to recommendation.", "ROUTE_SHORTCUT")
            state.current_step = "RECOMMENDATION_GENERATION"
            yield state
            
            state = self.recommendation_agent.execute(state)
            state.is_complete = True
            state.current_step = "COMPLETE"
            yield state
            return state

        # 4. Invoke Warehouse Allocation Agent (First replenishment source)
        state.current_step = "WAREHOUSE_ALLOCATION"
        yield state
        
        state = self.warehouse_agent.execute(state)
        yield state

        # Check if warehouse could satisfy the order
        wh_status = state.warehouse.status if state.warehouse else "SKIPPED"
        transfer_qty = state.warehouse.transfer_qty if state.warehouse else 0
        
        # 5. Invoke Supplier Intelligence Agent (If warehouse is insufficient)
        if wh_status == "INSUFFICIENT" or transfer_qty < reorder_qty:
            state.current_step = "SUPPLIER_INTELLIGENCE"
            yield state
            
            state = self.supplier_agent.execute(state)
            yield state
        else:
            state.add_log("Supervisor", "Warehouse stock is sufficient. Skipping Supplier Intelligence.", "ROUTE_SKIP")
            yield state

        # 6. Invoke Logistics Planning Agent (If we are transferring or purchasing)
        has_wh = state.warehouse and state.warehouse.transfer_qty > 0
        has_sup = state.supplier and state.supplier.order_qty > 0
        
        if has_wh or has_sup:
            state.current_step = "LOGISTICS_PLANNING"
            yield state
            
            state = self.logistics_agent.execute(state)
            yield state
        else:
            state.add_log("Supervisor", "No transport needed. Skipping Logistics Planning.", "ROUTE_SKIP")
            yield state

        # 7. Invoke Business Recommendation Agent (Consolidate output)
        state.current_step = "RECOMMENDATION_GENERATION"
        yield state
        
        state = self.recommendation_agent.execute(state)
        state.is_complete = True
        state.current_step = "COMPLETE"
        yield state
        
        return state
