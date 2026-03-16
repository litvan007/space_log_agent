from __future__ import annotations

from datetime import datetime
from typing import Any


def patch_sgr_agent_logging() -> None:
    """Patch SGRAgent logging to keep full reasoning and tool results."""

    from sgr_agent_core.base_agent import BaseAgent
    from sgr_agent_core.tools import BaseTool, ReasoningTool

    if getattr(BaseAgent, "_space_log_agent_full_logging_patch", False):
        return

    def _log_reasoning(self: BaseAgent, result: ReasoningTool) -> None:
        """Log the full reasoning payload without library-side truncation."""

        next_step = result.remaining_steps[0] if result.remaining_steps else "Completing"
        self.logger.info(
            f"""
    ###############################################
    LLM RESPONSE DEBUG:
       Reasoning Steps: {result.reasoning_steps}
       Current Situation: '{result.current_situation}'
       Plan Status: '{result.plan_status}'
       Searches Done: {self._context.searches_used}
       Clarifications Done: {self._context.clarifications_used}
       Enough Data: {result.enough_data}
       Remaining Steps: {result.remaining_steps}
       Task Completed: {result.task_completed}
       Next Step: {next_step}
    ###############################################"""
        )
        self.log.append(
            {
                "step_number": self._context.iteration,
                "timestamp": datetime.now().isoformat(),
                "step_type": "reasoning",
                "agent_reasoning": result.model_dump(mode="json"),
            }
        )

    def _log_tool_execution(self: BaseAgent, tool: BaseTool, result: str) -> None:
        """Log the full tool execution result without library-side truncation."""

        self.logger.info(
            f"""
###############################################
TOOL EXECUTION DEBUG:
    Tool Name: {tool.tool_name}
    Tool Model: {tool.model_dump_json(indent=2)}
    Result: '{result}'
###############################################"""
        )
        self.log.append(
            {
                "step_number": self._context.iteration,
                "timestamp": datetime.now().isoformat(),
                "step_type": "tool_execution",
                "tool_name": tool.tool_name,
                "agent_tool_context": tool.model_dump(mode="json"),
                "agent_tool_execution_result": result,
            }
        )

    BaseAgent._log_reasoning = _log_reasoning
    BaseAgent._log_tool_execution = _log_tool_execution
    BaseAgent._space_log_agent_full_logging_patch = True
