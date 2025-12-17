import json
from typing import Literal
from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from brain.agent_state import MessagesState
from brain.llm_config.config import LLMConfig
from langgraph.graph import START, StateGraph, END
from brain.llm_config.prompts import get_system_prompt
from brain.tools.config import setup_agent_tools
from dotenv import load_dotenv
import os
from server.services.google_calendar import GoogleCalendarService
from langgraph.checkpoint.postgres import PostgresSaver

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
CHECKPOINTER = None
if DATABASE_URL:
    try:
      # 1. Instantiate the saver
      _cm = PostgresSaver.from_conn_string(DATABASE_URL)
      CHECKPOINTER = _cm.__enter__()    # enter once, keep alive
      # 2. CRITICAL: Call setup() to create the tables
      # This must be done the first time it is run.
      CHECKPOINTER.setup() 
      print("INFO: LangGraph Postgres checkpointer initialized and tables ensured.")
        
    except Exception as e:
        print(f"ERROR: Failed to initialize Postgres checkpointer: {e}")
        CHECKPOINTER = None # Disable if setup fails
        
else:
    print("WARNING: DATABASE_URL not set, checkpointer disabled")

class BookingAgent:
   def __init__(self,google_calendar_service: GoogleCalendarService):
      llm_config = LLMConfig()
      self.tools, self.tool_by_name = setup_agent_tools(google_calendar_service)
      self.llm_with_tools = llm_config.llm.bind_tools(self.tools)
      
      agent_builder = StateGraph(MessagesState)
      agent_builder.add_node("llm_call", self.llm_call)
      agent_builder.add_node("environment", self.tool_node)

      agent_builder.add_edge(START, "llm_call")
      agent_builder.add_conditional_edges(
         "llm_call",
         self.should_continue,
         {
               # Name returned by should_continue : Name of next node to visit
               "Action": "environment",
               END: END,
         }
      )
      agent_builder.add_edge("environment", "llm_call")

      if CHECKPOINTER:
         self._booking_agent = agent_builder.compile(checkpointer=CHECKPOINTER)
      else:
         self._booking_agent = agent_builder.compile()

   def get_booking_agent(self):
      return self._booking_agent

   def llm_call(self,state: MessagesState):
      print("--- Entering LLM Call Node ---")
      curr_messages = state.get("messages", [])
      
      has_system_message = any(isinstance(msg, SystemMessage) for msg in curr_messages)
      if not has_system_message:
         system_message = SystemMessage(content=get_system_prompt())
         full_message_list = [system_message] + curr_messages
      else:
         # System message already exists, don't add it again
         full_message_list = curr_messages
      # 3. Invoke the LLM with the complete message list
      response_message = self.llm_with_tools.invoke(full_message_list)
      print(response_message.pretty_print)
      return {
            "messages": [response_message]
      }

   def tool_node(self,state: dict):
      '''Excecute the tool call'''
      print("--- Entering Environment (Tool) Node ---")
      result = []
      print(f"Tool Call Request: {state['messages'][-1].tool_calls}")
      for tool_call in state["messages"][-1].tool_calls:
            tool = self.tool_by_name[tool_call["name"]]
            if tool.name == "get_current_date":
                  observation = (
                     f"User current time is {state.get('client_time')} "
                     f"in timezone {state.get("timezone")}"
                  )
            else:
               observation = tool.invoke(tool_call["args"])
            observation_str: str
            if isinstance(observation, (dict, list)):
                # Convert structured output to a JSON string
                observation_str = json.dumps(observation)
            elif observation is not None:
                # Convert all other non-None objects (like Pydantic models, dates) to string
                observation_str = str(observation)
            else:
                observation_str = "Tool executed successfully with no direct output." # Handle None/empty output
            result.append(
               ToolMessage(content=observation_str,tool_call_id=tool_call["id"],name=tool_call["name"])
            )
      print("--- Exiting Environment (Tool) Node ---")
      return {"messages": result}

   def should_continue(self,state: MessagesState) -> Literal["environment", END]:
      """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""

      messages = state["messages"]
      last_message = messages[-1]
      print("-----------------------Should conitnue -------------------------------")
      print(last_message.tool_calls)
      print("----------------------------------------------------------------------")
      # If the LLM makes a tool call, then perform an action
      if last_message.tool_calls:
            return "Action"
      # Otherwise, we stop (reply to the user)

      return END