"""Define the state structures for the tender search agent."""

from __future__ import annotations

from typing import TypedDict, Sequence

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from langgraph.managed import IsLastStep
from typing_extensions import Annotated

class InputState(TypedDict):
    """Defines the input state for the tender search agent.

    This class is used to define the initial state and structure of incoming data.
    """

    messages: Annotated[Sequence[AnyMessage], add_messages]
    """
    Messages tracking the primary execution state of the agent.

    Typically accumulates a pattern of:
    1. HumanMessage - user input (e.g., "有哪些大數據的專案")
    2. AIMessage with .tool_calls - agent picking tool(s) to search tenders
    3. ToolMessage(s) - the responses from the tender search tools
    4. AIMessage without .tool_calls - agent responding with formatted results

    The `add_messages` annotation ensures that new messages are merged with existing ones,
    updating by ID to maintain an "append-only" state unless a message with the same ID is provided.
    """

class State(InputState):
    """Represents the complete state of the tender search agent.

    This class extends InputState with additional attributes needed for the agent's lifecycle.
    """

    is_last_step: IsLastStep
    """
    Indicates whether the current step is the last one before the graph raises an error.

    This is a 'managed' variable, controlled by the state machine rather than user code.
    It is set to 'True' when the step count reaches recursion_limit - 1.
    """
