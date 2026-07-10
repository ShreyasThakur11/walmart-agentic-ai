"""
Demand Forecast Agent.
Analyzes historical sales to predict future demand and determine optimal reorder quantity.
"""

import pandas as pd
from agents.base_agent import BaseAgent
from memory.state_manager import WorkflowState, DemandState
from tools.db_tools import DatabaseTools
from tools.rules_engine import RulesEngine
from prompts.templates import DEMAND_AGENT_PROMPT

class DemandAgent(BaseAgent):
    def __init__(self):
        super().__init__("DemandAgent")
        self.db = DatabaseTools()

    def _execute_logic(self, state: WorkflowState) -> WorkflowState:
        # Load sales history
        sales = self.db.get_sales_history(state.store_id, state.product_id)
        
        if not sales:
            # Fallback if no history exists (e.g. 5 units average daily sales)
            avg_daily = 5.0
            has_promo = False
            trend = "STABLE"
        else:
            df = pd.DataFrame(sales)
            avg_daily = float(df["UnitsSold"].mean())
            # Check if recent promotion or holiday was active
            recent_sales = df.tail(7)
            has_promo = bool((recent_sales["Promotion"] == 1).any())
            
            # Trend determination
            if has_promo:
                trend = "SPIKE"
            elif (recent_sales["Holiday"] == 1).any():
                trend = "SEASONAL"
            else:
                trend = "STABLE"

        # Apply multiplier based on active scenario name
        multiplier = 1.0
        explanation = "Steady consumer demand pattern."
        
        if "spike" in state.scenario_name.lower() or "festival" in state.scenario_name.lower():
            multiplier = 3.5
            trend = "SPIKE"
            explanation = "Demand spike expected due to holiday festival and marketing promotions."
        elif "promotion" in state.scenario_name.lower():
            multiplier = 2.8
            trend = "SPIKE"
            explanation = "Elevated volume driven by target retail discount flyer promotion."
        elif "contention" in state.scenario_name.lower():
            multiplier = 2.0
            trend = "SEASONAL"
            explanation = "High demand across regional stores due to winter season stocking."
            
        # Restocking window: let's assume a standard 7-day replenishment window
        forecast_units = int(avg_daily * 7 * multiplier)
        
        # Determine reorder quantity using RulesEngine
        current_stock = state.inventory.current_stock if state.inventory else 0
        max_capacity = state.inventory.max_capacity if state.inventory else 100
        
        reorder_qty = RulesEngine.calculate_reorder_quantity(
            current_stock=current_stock,
            forecast_demand=forecast_units,
            max_capacity=max_capacity
        )
        
        # Populate demand state
        state.demand = DemandState(
            forecast_units=forecast_units,
            trend_type=trend,
            has_promotion=has_promo,
            average_daily_sales=round(avg_daily, 2),
            reorder_quantity=reorder_qty,
            explanation=explanation
        )
        
        # Log entry in history
        state.add_log(
            agent_name=self.name,
            message=f"Forecasted demand of {forecast_units} units ({trend} trend). Reorder recommendation: {reorder_qty} units.",
            action="PROCEED"
        )
        
        return state
