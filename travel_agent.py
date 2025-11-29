import os
from dotenv import load_dotenv
import numpy as np
import pandas as pd
from typing import TypedDict, Optional

# prefer official tavily package (per deprecation warning) and fall back to community
try:
    from langchain_tavily import TavilySearch as TavilySearchTool  # type: ignore
except Exception:
    try:
        from langchain_community.tools.tavily_search import TavilySearchResults as TavilySearchTool  # type: ignore
    except Exception:
        TavilySearchTool = None

# Groq LLM provider (optional)
try:
    from langchain_groq import ChatGroq  # type: ignore
except Exception:
    ChatGroq = None

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END


load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")

# Initialize LLM only if provider available and API key present. Model can be set via GROQ_MODEL env var.
llm = None
if ChatGroq is not None and os.getenv("GROQ_API_KEY"):
    groq_model = os.getenv("GROQ_MODEL", "")  # set GROQ_MODEL in .env to a model you have access to
    if groq_model:
        try:
            llm = ChatGroq(model=groq_model, temperature=0)
        except Exception as e:
            print("Warning: ChatGroq init failed:", e)
            llm = None
    else:
        print("Info: GROQ_MODEL not set; skipping ChatGroq initialization.")
else:
    if ChatGroq is None:
        print("Info: langchain_groq not installed.")
    else:
        print("Info: GROQ_API_KEY not set; skipping ChatGroq initialization.")

# Initialize Tavily search tool if available and API key present
search = None
if TavilySearchTool is not None and os.getenv("TAVILY_API_KEY"):
    try:
        # constructor name differs between packages: try sensible defaults
        try:
            search = TavilySearchTool(max_results=3)
        except TypeError:
            search = TavilySearchTool()
    except Exception as e:
        print("Warning: Tavily init failed:", e)
        search = None
else:
    if TavilySearchTool is None:
        print("Info: Tavily search package not installed (install langchain-tavily).")
    else:
        print("Info: TAVILY_API_KEY not set; Tavily searches will be skipped.")

class TripState(TypedDict, total=False):
    destination: str
    interests: str
    flight_info: str
    hotel_info: str
    activity_info: str
    itinerary: str

def _safe_search_query(query: str) -> str:
    if search is None:
        return f"[search skipped] {query}"
    try:
        results = search.invoke(query)
        return str(results)
    except Exception as e:
        return f"[search failed: {e}] {query}"

def search_flights(state: TripState):
    print(" Searching for flights...")
    query = f"Cheap flights to {state.get('destination','unknown')} next month prices"
    return {"flight_info": _safe_search_query(query)}

def search_hotels(state: TripState):
    print(" Searching for hotels...")
    query = f"Best budget hotels in {state.get('destination','unknown')} near city center"
    return {"hotel_info": _safe_search_query(query)}

def search_activities(state: TripState):
    print(" Searching for activities...")
    query = f"Top things to do in {state.get('destination','unknown')} for someone who likes {state.get('interests','varied')}"
    return {"activity_info": _safe_search_query(query)}

def _fallback_itinerary(state: TripState) -> str:
    dest = state.get("destination", "your destination")
    interests = state.get("interests", "general interests")
    return f"# 3-Day Itinerary for {dest}\n\nUser interests: {interests}\n\n(LLM not available — fallback itinerary.)"

def compile_itinerary(state: TripState):
    print(" Compiling final plan...")
    prompt = f"""
You are an expert Travel Agent. Create a 3-day itinerary for {state.get('destination','unknown')}.
User Interests: {state.get('interests','none')}

Flight Data: {state.get('flight_info','')}
Hotel Data: {state.get('hotel_info','')}
Activity Data: {state.get('activity_info','')}

Format as a clean Day-by-Day Markdown guide with estimated costs.
"""
    if llm is None:
        return {"itinerary": _fallback_itinerary(state)}

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        # handle different response shapes
        return {"itinerary": getattr(response, "content", str(response))}
    except Exception as e:
        print("Warning: LLM call failed:", e)
        return {"itinerary": _fallback_itinerary(state)}

# 4. BUILD THE GRAPH (The Workflow)
workflow = StateGraph(TripState)

# Add Nodes
workflow.add_node("flights", search_flights)
workflow.add_node("hotels", search_hotels)
workflow.add_node("activities", search_activities)
workflow.add_node("planner", compile_itinerary)

# For simplicity here: Flights -> Hotels -> Activities -> Planner
workflow.set_entry_point("flights")
workflow.add_edge("flights", "hotels")
workflow.add_edge("hotels", "activities")
workflow.add_edge("activities", "planner")
workflow.add_edge("planner", END)

# Compile the machine
app = workflow.compile()
#l

# 5. RUN IT
if __name__ == "__main__":
    trip_request = {
        "destination": "Kyoto, Japan",
        "interests": "History, Matcha tea, and calm nature"
    }

    print(f" Starting Odyssey Agent for: {trip_request['destination']}")
    result = app.invoke(trip_request)

    print("\n" + "="*50)
    print("FINAL ITINERARY")
    print("="*50)
    print(result.get("itinerary", "[no itinerary returned]"))