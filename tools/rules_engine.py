"""
Rules engine for the Walmart Smart Inventory & Restocking Assistant.
Maintains business logic thresholds, stock health rankings, and priority calculations.
"""

from typing import Dict, Literal

class RulesEngine:
    @staticmethod
    def get_stock_health_label(current_stock: int, min_threshold: int, max_capacity: int) -> Literal["CRITICAL_UNDERSTOCK", "UNDERSTOCK", "STABLE", "OVERSTOCK"]:
        """Evaluates stock health category based on boundaries."""
        if current_stock <= min_threshold * 0.3:
            return "CRITICAL_UNDERSTOCK"
        elif current_stock < min_threshold:
            return "UNDERSTOCK"
        elif current_stock > max_capacity * 0.9:
            return "OVERSTOCK"
        return "STABLE"

    @staticmethod
    def calculate_reorder_quantity(current_stock: int, forecast_demand: int, max_capacity: int) -> int:
        """Calculates optimal reorder quantity to restore inventory without overstocking."""
        # Calculate target stock level as maximum capacity
        needed = max_capacity - current_stock
        # If forecast demand is higher than normal, make sure we cover forecast + buffer
        buffer = int(forecast_demand * 0.2)
        total_target = forecast_demand + buffer
        
        # We need to replenish at least up to the min_threshold, but capped at max_capacity
        optimal_qty = max(needed, total_target)
        # Cap reorder quantity so we don't exceed max capacity
        final_qty = min(optimal_qty, max_capacity - current_stock)
        return max(0, int(final_qty))

    @staticmethod
    def evaluate_supplier_score(lead_time: int, reliability: float, unit_cost: float, cost_weight: float = 0.5, speed_weight: float = 0.5) -> float:
        """
        Calculates a ranking score for a supplier.
        Lower score is better (represents lower cost / faster lead time / higher reliability).
        """
        # Normalize variables (assuming reasonable max values for normalization)
        # Lead time: 0-14 days -> normalize by 14
        norm_lead_time = min(lead_time / 14.0, 1.0)
        
        # Reliability: 0.0 - 1.0 -> invert reliability so lower is better (0.0 is perfect, 1.0 is bad)
        norm_unreliability = 1.0 - reliability
        
        # Combine speed factors (lead time & unreliability)
        speed_factor = (norm_lead_time * 0.6) + (norm_unreliability * 0.4)
        
        # Cost factor: Unit Cost. Higher cost is worse.
        # Since cost values differ per product, we evaluate suppliers relative to others in the actual agent,
        # but here we return a weighted sum of normalized factors.
        # Score = cost_weight * cost_factor + speed_weight * speed_factor
        # We assume unit_cost represents direct cost.
        return round((cost_weight * unit_cost) + (speed_weight * speed_factor * 10.0), 4)
