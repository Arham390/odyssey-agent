import os
from typing import TypedDict, Literal
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

# 1. CONFIGURATION
load_dotenv()
# USE THE CORRECT MODEL ID HERE
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
search = TavilySearchResults(max_results=3)

# 2. DEFINE SOPHISTICATED STATE
class TripState(TypedDict):
    destination: str
    interests: str
    budget: int            # New: User's max budget
    current_cost_estimate: int # New: AI's running calculation
    revision_count: int    # New: To prevent infinite loops
    flight_info: str
    hotel_info: str
    activity_info: str
    itinerary: str
    feedback: str          # New: Message passing for "Find cheaper stuff"

# 3. DEFINE NODES

def search_flights(state: TripState):
    print(f"✈️ Searching flights to {state['destination']}...")
    # If we are revising, search for budget airlines
    query_prefix = "Cheapest budget" if state.get("revision_count", 0) > 0 else "Best"
    results = search.invoke(f"{query_prefix} flights to {state['destination']} prices")
    return {"flight_info": str(results)}

def search_hotels(state: TripState):
    print(f"🏨 Searching hotels (Attempt {state.get('revision_count', 0) + 1})...")
    # Dynamic Query: If revising, strictly search for "Cheap/Hostel"
    if state.get("feedback"):
        print(f"   ⚠️ Feedback received: {state['feedback']}")
        query = f"Extremely cheap budget hostels/hotels in {state['destination']} under ${state['budget']//5} per night"
    else:
        query = f"Nice hotels in {state['destination']} city center"
    
    results = search.invoke(query)
    return {"hotel_info": str(results)}

def search_activities(state: TripState):
    print("🎨 Searching activities...")
    results = search.invoke(f"Things to do in {state['destination']} related to {state['interests']}")
    return {"activity_info": str(results)}

def planner_node(state: TripState):
    print("📝 Assessing Budget & Planning...")
    
    # We ask the LLM to do two things: 
    # 1. Estimate total cost.
    # 2. Write the itinerary OR request a revision.
    
    prompt = f"""
    You are a Travel Agent. The user's TOTAL budget is ${state['budget']}.
    
    Data Found:
    - Flights: {state['flight_info']}
    - Hotels: {state['hotel_info']}
    - Activities: {state['activity_info']}
    
    TASK:
    1. Estimate the total cost (Flights + 3 nights Hotel + Activities).
    2. IF the cost is > ${state['budget']}, write ONLY the word "TOO EXPENSIVE".
    3. IF the cost is okay, write a detailed Day-by-Day Markdown Itinerary.
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content
    
    if "TOO EXPENSIVE" in content:
        # We assume the cost is high (heuristic)
        return {"itinerary": "REVISE", "current_cost_estimate": 99999}
    else:
        return {"itinerary": content, "current_cost_estimate": 0}

# 4. CONDITIONAL LOGIC (The "Guardrail")
def should_continue(state: TripState) -> Literal["search_hotels", "__end__"]:
    # Logic: If output was "REVISE" and we haven't tried too many times...
    if state["itinerary"] == "REVISE":
        if state["revision_count"] < 2: # Limit to 2 retries
            print("💰 Trip is over budget! Looping back to find cheaper hotels...")
            return "search_hotels"
        else:
            print("⚠️ Budget impossible. Finalizing best effort.")
            return "__end__"
    return "__end__"

def revise_budget_strategy(state: TripState):
    # This node simply updates the state before looping back
    return {
        "revision_count": state["revision_count"] + 1,
        "feedback": "Price is too high. Find cheaper accommodation."
    }

# 5. BUILD THE GRAPH
workflow = StateGraph(TripState)

workflow.add_node("flights", search_flights)
workflow.add_node("hotels", search_hotels)
workflow.add_node("activities", search_activities)
workflow.add_node("planner", planner_node)
workflow.add_node("reviser", revise_budget_strategy)

# Flow
workflow.set_entry_point("flights")
workflow.add_edge("flights", "hotels")
workflow.add_edge("hotels", "activities")
workflow.add_edge("activities", "planner")

# The Conditional Edge
workflow.add_conditional_edges(
    "planner",
    should_continue,
    {
        "search_hotels": "reviser", # Go to reviser first to update state
        "__end__": END
    }
)

workflow.add_edge("reviser", "hotels") # Loop back to hotels

app = workflow.compile()