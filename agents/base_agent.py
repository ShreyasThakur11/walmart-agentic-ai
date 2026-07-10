"""
Base Agent Module.
Defines the standard interface, logging, and metrics-tracking wrapper for all specialized agents.
"""

import time
import traceback
import logging
from abc import ABC, abstractmethod
from memory.state_manager import WorkflowState

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"WalmartAgenticAI.{name}")

    @abstractmethod
    def _execute_logic(self, state: WorkflowState) -> WorkflowState:
        """Core execution logic of the specialized agent to be implemented by child classes."""
        pass

    def execute(self, state: WorkflowState) -> WorkflowState:
        """
        Wrapper around agent execution logic.
        Handles execution time recording, general logging, and robust exception catching.
        """
        self.logger.info(f"Starting execution of {self.name}")
        start_time = time.time()
        
        try:
            # Run the agent-specific logic
            state = self._execute_logic(state)
            
            # Calculate execution duration
            duration = round((time.time() - start_time) * 1000.0, 2)
            self.logger.info(f"Successfully completed {self.name} in {duration}ms")
            return state
            
        except Exception as e:
            duration = round((time.time() - start_time) * 1000.0, 2)
            error_msg = f"Error in {self.name}: {str(e)}\n{traceback.format_exc()}"
            self.logger.error(error_msg)
            
            # Register failure log in state history
            state.add_log(
                agent_name=self.name,
                message=f"FAILED with error: {str(e)}",
                action="ERROR",
                exec_time=duration
            )
            return state
