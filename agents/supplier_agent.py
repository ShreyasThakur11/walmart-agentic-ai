"""
Supplier Intelligence Agent.
Evaluates and scores commercial suppliers for replenishment orders when warehouses lack stock.
"""

from agents.base_agent import BaseAgent
from memory.state_manager import WorkflowState, SupplierProposal
from tools.db_tools import DatabaseTools
from tools.rules_engine import RulesEngine
from prompts.templates import SUPPLIER_AGENT_PROMPT

class SupplierAgent(BaseAgent):
    def __init__(self):
        super().__init__("SupplierAgent")
        self.db = DatabaseTools()

    def _execute_logic(self, state: WorkflowState) -> WorkflowState:
        if not state.demand:
            raise ValueError("Demand Forecast State must be populated before Supplier Intelligence.")
            
        reorder_qty = state.demand.reorder_quantity
        
        # Calculate how much is already covered by warehouse transfer
        transfer_qty = state.warehouse.transfer_qty if state.warehouse else 0
        remaining_qty = reorder_qty - transfer_qty
        
        # If no supplier quantity is needed, skip
        if remaining_qty <= 0:
            state.supplier = SupplierProposal(status="SKIPPED")
            state.add_log(self.name, "Sourcing fully satisfied by warehouse transfer. Supplier order skipped.", "SKIP")
            return state

        # Query supplier quotes for this product
        suppliers_list = self.db.get_supplier_info(state.product_id)
        
        if not suppliers_list:
            state.supplier = SupplierProposal(status="SKIPPED")
            state.add_log(self.name, "No supplier options found in database.", "PROCEED")
            return state
            
        # Score each supplier based on lead time, reliability, and unit cost
        scored_suppliers = []
        for sup in suppliers_list:
            # We can use default cost/speed weights of 0.5/0.5
            cost_weight = 0.5
            speed_weight = 0.5
            
            # Scenario specific adjustments to weights
            # In Scenario 3, supplier delays mean we care more about speed/reliability
            if "delay" in state.scenario_name.lower():
                cost_weight = 0.2
                speed_weight = 0.8
                
            score = RulesEngine.evaluate_supplier_score(
                lead_time=sup["LeadTime"],
                reliability=sup["ReliabilityScore"],
                unit_cost=sup["UnitCost"],
                cost_weight=cost_weight,
                speed_weight=speed_weight
            )
            
            scored_suppliers.append({
                "SupplierID": sup["SupplierID"],
                "SupplierName": sup["SupplierName"],
                "LeadTime": sup["LeadTime"],
                "ReliabilityScore": sup["ReliabilityScore"],
                "UnitCost": sup["UnitCost"],
                "Score": score
            })
            
        # Sort by score (lower score is better)
        scored_suppliers = sorted(scored_suppliers, key=lambda x: x["Score"])
        best_sup = scored_suppliers[0]
        
        total_cost = round(best_sup["UnitCost"] * remaining_qty, 2)
        
        state.supplier = SupplierProposal(
            supplier_id=best_sup["SupplierID"],
            supplier_name=best_sup["SupplierName"],
            lead_time_days=int(best_sup["LeadTime"]),
            reliability_score=float(best_sup["ReliabilityScore"]),
            unit_cost=float(best_sup["UnitCost"]),
            order_qty=remaining_qty,
            total_cost=total_cost,
            status="PROPOSED"
        )
        
        state.add_log(
            agent_name=self.name,
            message=f"Selected supplier {best_sup['SupplierName']} ({best_sup['SupplierID']}) with score {best_sup['Score']}. Proposed order: {remaining_qty} units at ${best_sup['UnitCost']}/unit.",
            action="PROCEED"
        )
        
        return state
