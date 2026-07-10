"""
Warehouse Allocation Agent.
Queries regional distribution centers to identify the nearest stock transfer source.
"""

from agents.base_agent import BaseAgent
from memory.state_manager import WorkflowState, WarehouseAllocation
from tools.db_tools import DatabaseTools
from prompts.templates import WAREHOUSE_AGENT_PROMPT

class WarehouseAgent(BaseAgent):
    def __init__(self):
        super().__init__("WarehouseAgent")
        self.db = DatabaseTools()

    def _execute_logic(self, state: WorkflowState) -> WorkflowState:
        if not state.demand:
            raise ValueError("Demand Forecast State must be populated before Warehouse Allocation.")
            
        reorder_qty = state.demand.reorder_quantity
        
        # If no reorder needed, skip warehouse
        if reorder_qty <= 0:
            state.warehouse = WarehouseAllocation(status="SKIPPED")
            state.add_log(self.name, "No replenishment needed. Skipped warehouse transfer.", "SKIP")
            return state

        # Query warehouse stock
        wh_stock_list = self.db.get_warehouse_stock(state.product_id)
        
        candidates = []
        for wh in wh_stock_list:
            wh_id = wh["WarehouseID"]
            avail = wh["AvailableStock"]
            
            # Fetch transportation metrics to our store
            logistics = self.db.get_logistics_details(wh_id, state.store_id)
            if logistics and avail > 0:
                candidates.append({
                    "WarehouseID": wh_id,
                    "Location": wh["Location"],
                    "AvailableStock": avail,
                    "Distance": logistics["Distance"],
                    "TransferTime": logistics["EstimatedHours"] / 24.0,  # Convert hours to days
                    "TruckAvailability": logistics["TruckAvailability"]
                })
                
        # Sort by distance (nearest distribution center first)
        candidates = sorted(candidates, key=lambda x: x["Distance"])
        
        if not candidates:
            # No warehouse has stock
            state.warehouse = WarehouseAllocation(status="INSUFFICIENT")
            state.add_log(self.name, "Zero inventory available across all distribution centers.", "PROCEED")
            return state
            
        # Select closest candidate
        best_wh = candidates[0]
        
        # Check if warehouse can fully cover the demand
        transfer_qty = min(reorder_qty, best_wh["AvailableStock"])
        status = "ALLOCATED" if transfer_qty >= reorder_qty else "INSUFFICIENT"
        
        # Approximate transfer cost: $0.15 per mile per unit, plus $50 flat fee
        wh_cost = round(50.0 + (best_wh["Distance"] * 0.15 * transfer_qty), 2)
        
        state.warehouse = WarehouseAllocation(
            warehouse_id=best_wh["WarehouseID"],
            location=best_wh["Location"],
            available_stock=best_wh["AvailableStock"],
            distance_miles=float(best_wh["Distance"]),
            transfer_time_days=round(best_wh["TransferTime"], 2),
            transfer_qty=transfer_qty,
            cost=wh_cost,
            status=status
        )
        
        state.add_log(
            agent_name=self.name,
            message=f"Identified {best_wh['Location']} ({best_wh['WarehouseID']}) at distance {best_wh['Distance']} miles. Proposing transfer of {transfer_qty} units. Status: {status}",
            action="PROCEED"
        )
        
        return state
