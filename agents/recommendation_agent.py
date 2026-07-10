"""
Business Recommendation Agent.
Consolidates sourcing and logistics details into an actionable, manager-ready restock recommendation.
"""

from agents.base_agent import BaseAgent
from memory.state_manager import WorkflowState, FinalRecommendation
from tools.db_tools import DatabaseTools
from prompts.templates import RECOMMENDATION_AGENT_PROMPT

class RecommendationAgent(BaseAgent):
    def __init__(self):
        super().__init__("RecommendationAgent")
        self.db = DatabaseTools()

    def _execute_logic(self, state: WorkflowState) -> WorkflowState:
        # Check if restock is even needed
        reorder_qty = state.demand.reorder_quantity if state.demand else 0
        
        if reorder_qty <= 0:
            state.recommendation = FinalRecommendation(
                action="MONITOR",
                details="Inventory is at a healthy operating level. Continue standard daily monitoring. No restock needed.",
                business_impact="Maintains zero additional holding cost and keeps warehouse utilization stable.",
                confidence_score=98.0,
                estimated_savings=0.0,
                stockout_reduction_pct=0.0,
                risk_score=5.0
            )
            state.add_log(self.name, "Consolidated recommendation: MONITOR inventory.", "COMPLETE")
            return state

        # Sourcing breakdown
        transfer_qty = state.warehouse.transfer_qty if state.warehouse else 0
        order_qty = state.supplier.order_qty if state.supplier else 0
        
        wh_loc = state.warehouse.location if state.warehouse else ""
        sup_name = state.supplier.supplier_name if state.supplier else ""
        
        # Calculate cost savings
        # Warehouse transfers save money because we don't purchase new items, we use existing network stock.
        # Savings = transfer_qty * (supplier_unit_cost) - transfer_logistics_cost.
        # Let's find a representative supplier unit cost for the product to calculate what it would have cost to buy them all.
        supplier_quotes = self.db.get_supplier_info(state.product_id)
        avg_supplier_price = sum(s["UnitCost"] for s in supplier_quotes) / len(supplier_quotes) if supplier_quotes else 10.0
        
        wh_logistics_cost = state.warehouse.cost if state.warehouse else 0.0
        savings = max(0.0, round((transfer_qty * avg_supplier_price) - wh_logistics_cost, 2))
        
        # Delivery times
        logistics_eta = state.logistics.estimated_delivery_days if state.logistics else 3.0
        
        # Calculate risk score (0 to 100)
        # Higher risk if current stock is low and delivery time is high
        stock_status = state.inventory.stock_health if state.inventory else "STABLE"
        
        base_risk = 10.0
        if stock_status == "CRITICAL_UNDERSTOCK":
            base_risk = 80.0
        elif stock_status == "UNDERSTOCK":
            base_risk = 45.0
            
        # Logistics speed reduces or increases risk
        risk_adjustment = logistics_eta * 4.0
        if logistics_eta <= 1.0:
            risk_adjustment = -15.0
            
        final_risk = min(99.0, max(5.0, base_risk + risk_adjustment))
        
        # Stockout reduction percentage
        if transfer_qty + order_qty >= reorder_qty:
            reduction_pct = 100.0 - (final_risk * 0.1) # nearly complete reduction
        else:
            reduction_pct = round(((transfer_qty + order_qty) / reorder_qty) * 100.0, 1)

        # Confidence score (0.0 to 100.0)
        # Combination of supplier reliability and transport mode
        sup_reliability = state.supplier.reliability_score if (state.supplier and order_qty > 0) else 1.0
        log_reliability = 0.95 if (state.logistics and state.logistics.transport_mode != "AIR_CARGO") else 0.88
        
        confidence = round((sup_reliability * 0.6 + log_reliability * 0.4) * 100.0, 1)
        
        # Formulate action action details
        action = "TRANSFER"
        details = ""
        impact = ""
        
        if transfer_qty > 0 and order_qty > 0:
            action = "DUAL_SOURCE"
            details = f"Transfer {transfer_qty} units from {wh_loc} and purchase {order_qty} units from {sup_name}."
            impact = f"Expedites coverage of low stock while filling the remaining demand gap with backup supplier."
        elif transfer_qty > 0:
            action = "TRANSFER"
            details = f"Transfer {transfer_qty} units from {wh_loc} to Store {state.store_id}."
            impact = f"Reduces stockout probability by utilizing nearby Walmart distribution network, saving ${savings} in purchasing costs."
        elif order_qty > 0:
            action = "PROCURE"
            details = f"Procure {order_qty} units from {sup_name}."
            impact = f"Fulfills low stock directly through external vendor as no inventory was available in our regional distribution centers."
            
        state.recommendation = FinalRecommendation(
            action=action,
            details=details,
            business_impact=impact,
            confidence_score=confidence,
            estimated_savings=savings,
            stockout_reduction_pct=round(reduction_pct, 1),
            risk_score=round(final_risk, 1)
        )
        
        state.add_log(
            agent_name=self.name,
            message=f"Consolidated final recommendation: {action}. Details: {details}. Est. Savings: ${savings}. Risk Score: {round(final_risk, 1)}",
            action="COMPLETE"
        )
        
        return state
