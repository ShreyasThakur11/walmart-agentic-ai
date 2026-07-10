"""
Inventory Monitoring Agent.
Reads inventory levels and evaluates stock health against capacity limits and minimum thresholds.
"""

import time
from agents.base_agent import BaseAgent
from memory.state_manager import WorkflowState, InventoryState
from tools.db_tools import DatabaseTools
from tools.rules_engine import RulesEngine
from prompts.templates import INVENTORY_AGENT_PROMPT

class InventoryAgent(BaseAgent):
    def __init__(self):
        super().__init__("InventoryAgent")
        self.db = DatabaseTools()

    def _execute_logic(self, state: WorkflowState) -> WorkflowState:
        # Load inventory information from DB
        inv = self.db.get_inventory(state.store_id, state.product_id)
        
        if not inv:
            raise ValueError(f"Inventory record not found for Store: {state.store_id}, Product: {state.product_id}")
            
        current_stock = inv["CurrentStock"]
        min_threshold = inv["MinimumThreshold"]
        max_capacity = inv["MaximumCapacity"]
        product_name = inv["ProductName"]
        
        # Save product name to global state
        state.product_name = product_name
        
        # Evaluate health
        health = RulesEngine.get_stock_health_label(current_stock, min_threshold, max_capacity)
        
        # Generate warnings
        alerts = []
        if health == "CRITICAL_UNDERSTOCK":
            alerts.append(f"CRITICAL WARNING: Stock level ({current_stock}) is severely low! Immediate action required.")
        elif health == "UNDERSTOCK":
            alerts.append(f"WARNING: Stock level ({current_stock}) is below safety threshold ({min_threshold}).")
        elif health == "OVERSTOCK":
            alerts.append(f"INFO: Stock level ({current_stock}) is high. Optimize storage layout.")
            
        # Update the state
        state.inventory = InventoryState(
            status=health,
            current_stock=current_stock,
            min_threshold=min_threshold,
            max_capacity=max_capacity,
            stock_health=health,
            alerts=alerts
        )
        
        # Log entry in history
        state.add_log(
            agent_name=self.name,
            message=f"Analyzed inventory for {product_name}. Health status is {health}. Alerts generated: {len(alerts)}",
            action="PROCEED"
        )
        
        return state
