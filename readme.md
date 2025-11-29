# ✈️ Odyssey: Autonomous Travel Planner Agent

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-orange)
![Llama 3](https://img.shields.io/badge/Model-Llama_3_70B-purple)
![Status](https://img.shields.io/badge/Status-Prototype-green)

**Odyssey** is an autonomous AI agent that plans complete travel itineraries by orchestrating multiple research "workers" in parallel. Unlike standard chatbots that hallucinate travel details, Odyssey uses **LangGraph** to coordinate real-time web searches for flights, hotels, and activities, synthesizing them into a cohesive, day-by-day plan.

---

## 🤖 How It Works

Odyssey follows a **State Graph** architecture. Instead of a single LLM trying to do everything, the system splits the task into specialized nodes that pass data via a shared `TripState`.

[Image of AI travel planner workflow]

```mermaid
graph TD
    Start([User Request]) --> A[Node: Flight Search]
    A --> B[Node: Hotel Search]
    B --> C[Node: Activity Search]
    C --> D[Node: Itinerary Compiler]
    D --> End([Final PDF Plan])
Flight Node: Uses TavilySearch to find real-time flight prices and schedules.

Hotel Node: Scans for accommodation matching the user's budget and location preferences.

Activity Node: Finds local attractions based on user interests (e.g., "History", "Food").

Planner Node: Aggregates all gathered context and uses Llama 3 to generate a formatted markdown itinerary.

🛠️ Tech Stack
Brain: Groq API (Llama 3 70B for high-speed inference)

Tools: Tavily API (Optimized search engine for AI agents)

Framework: LangGraph (Stateful agent orchestration)

Environment: Python 3.10+

⚡ Quick Start
1. Clone the Repository
Bash

git clone [https://github.com/YOUR_USERNAME/odyssey-agent.git](https://github.com/YOUR_USERNAME/odyssey-agent.git)
cd odyssey-agent
2. Set Up Environment
Bash

python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
3. Install Dependencies
Bash

pip install -r requirements.txt
4. Configure API Keys
Create a .env file in the root directory:

Ini, TOML

GROQ_API_KEY="gsk_..."
TAVILY_API_KEY="tvly-..."
5. Run the Agent
Bash

python travel_agent.py
📝 Example Output
Input:

"Plan a 3-day trip to Kyoto, Japan. I love history, matcha tea, and calm nature."

Agent Output:

Markdown

# 🇯🇴 3-Day Kyoto Itinerary: History & Serenity

## ✈️ Logistics
* **Flight Estimate:** $850 (Round trip via ANA)
* **Accommodation:** "The Pocket Hotel Kyoto" (Budget-friendly, near train station)

## 🗓️ Day 1: The Historical Heart
* **Morning:** Visit **Kinkaku-ji (Golden Pavilion)**. Arrive at 9:00 AM to beat the crowd.
* **Lunch:** Matcha Soba at "Omen" near the Philosopher's Path.
* **Afternoon:** Walk the **Fushimi Inari Shrine** gates.
* ...
```
