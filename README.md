# 🤖 Multi-Agent AI Hub

> A unified Streamlit application hosting **6 specialized AI agents** across **6 different domains** — built with LangChain, Groq LLM, and SQLite. Production-style modular architecture with auto-discovery registry.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-1.x-green?logo=langchain&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red?logo=streamlit&logoColor=white)
![SQLite](https://img.shields.io/badge/Database-SQLite-blue?logo=sqlite&logoColor=white)
![Groq](https://img.shields.io/badge/LLM-Groq%20GPT--OSS--20B-orange)

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Live Agents](#-live-agents)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Features](#-features)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Test Cases](#-test-cases)
- [Concepts Demonstrated](#-concepts-demonstrated)
- [Roadmap](#-roadmap)
- [License](#-license)

---

## 🎯 Overview

**Multi-Agent AI Hub** is a modular, production-style application that demonstrates how to build, organize, and deploy multiple AI agents in a single unified interface. Instead of building separate chatbots for different tasks, this project uses an **auto-discovery registry** pattern — drop a new agent folder in, and it automatically appears in the UI sidebar.

Every agent follows a strict contract (the `BaseAgent` abstract class) ensuring consistency, while retaining the flexibility to define its own tools, prompts, and UI.

### Why This Project?

- ✅ **6 Ready-to-Use Agents** covering real-world domains
- ✅ **Modular Architecture** — add new agents without touching `app.py`
- ✅ **34 Custom Tools** — agents can take real actions, not just chat
- ✅ **6 SQLite Databases** — persistent storage per domain
- ✅ **No heavy infrastructure** — runs locally with free APIs

---

## 🤖 Live Agents

| # | Agent | Domain | Purpose | Tools |
|---|-------|--------|---------|-------|
| 1 | 📧 **EmailCraft** | Business | Multi-agent Writer + Reviewer system for professional emails | 4 |
| 2 | 🔍 **News Researcher** | Research | Web news search + stock price tracking + gain calculator | 3 |
| 3 | 🍲 **RecipeGenie** | Food | Transform any recipe to diet-specific (Vegan, Keto, GF, etc.) | 5 |
| 4 | 💰 **PropWealth** | Finance | Real estate investment analyzer (ROI, cash flow, risk) | 9 |
| 5 | 📝 **QuizMaster Pro** | Education | Upload PDF → generate adaptive quizzes → track mastery | 7 |
| 6 | 💊 **MediScan** | Medical | Drug-drug + drug-food interaction checker with alternatives | 6 |

**Total: 34 custom tools across 6 agents**

---

## 🏗️ Architecture

This project follows a **3-Layer Modular Architecture**:

```
┌─────────────────────────────────────────────────────────────┐
│                  USER INTERFACE (Streamlit)                  │
│                                                             │
│   Sidebar: Domain → Agent Selector                          │
│   Main Area: Selected Agent's Custom UI                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              AGENT ORCHESTRATION (LangChain)                 │
│                                                             │
│   ┌─────────────────────────────────────────────────┐       │
│   │  BaseAgent (Abstract Class)                     │       │
│   │  - NAME, ICON, DOMAIN attributes               │       │
│   │  - run() abstract method                       │       │
│   │  - render_ui() abstract method                 │       │
│   └──────────────────┬──────────────────────────────┘       │
│                      │ Inheritance                            │
│      ┌───────┬───────┼───────┬───────┬───────┐              │
│      ▼       ▼       ▼       ▼       ▼       ▼              │
│   EmailCraft Researcher RecipeGenie PropWealth QuizMaster MediScan│
│      └───────┴───────┴───────┴───────┴───────┘              │
│                  Auto-Discovery (registry)                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              TOOLS + DATABASE LAYER                          │
│                                                             │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│   │ @tool    │ │ @tool    │ │ @tool    │ │ @tool    │      │
│   │ funcs    │ │ funcs    │ │ funcs    │ │ funcs    │      │
│   └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘      │
│        │            │            │            │              │
│        ▼            ▼            ▼            ▼              │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│   │ SQLite   │ │ SQLite   │ │ SQLite   │ │ SQLite   │      │
│   │ .db      │ │ .db      │ │ .db      │ │ .db      │      │
│   └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└─────────────────────────────────────────────────────────────┘

Plus: Groq LLM (gpt-oss-20b) + Tavily Search API (shared by all)
```

### Key Architectural Decisions

1. **BaseAgent Abstract Class** — Forces every agent to implement `run()` and `render_ui()`. Guarantees consistency.
2. **Auto-Discovery Registry** — `pkgutil` scans `agents/` folder and automatically registers any new agent. No code changes needed in `app.py`.
3. **Separation of Concerns** — Each agent is split into 3 files:
   - `tools.py` — Python functions exposed to LLM via `@tool` decorator
   - `agent.py` — LangChain agent setup, system prompt, main class
   - `ui.py` — Streamlit UI rendering for that specific agent
4. **Per-Agent Database** — Each domain has its own SQLite file. No cross-domain coupling.
5. **Shared LLM** — All agents share one Groq instance (cached) for cost efficiency.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.10+ |
| **Agent Framework** | LangChain 1.x |
| **LLM** | Groq API (gpt-oss-20b) |
| **UI Framework** | Streamlit |
| **Database** | SQLite (per-agent) |
| **Search API** | Tavily Search |
| **PDF Processing** | PyMuPDF (fitz) |
| **Data Validation** | Pydantic |
| **Memory** | LangGraph InMemorySaver |

---

## 📁 Project Structure

```
multi-agent-ai-hub/
│
├── app.py                        # Main Streamlit entry point
├── .env                          # API keys (not in git)
├── requirements.txt
├── README.md
│
├── common/                       # Shared utilities
│   ├── __init__.py
│   ├── llm.py                    # Cached Groq LLM instance
│   └── ...
│
├── database/                     # SQLite files (auto-created)
│   ├── ecommerce.db
│   ├── food.db
│   ├── finance.db
│   ├── quiz.db
│   └── medical.db
│
└── agents/                       # All AI agents live here
    ├── __init__.py               # AUTO-DISCOVERY REGISTRY
    ├── base_agent.py             # Abstract base class
    │
    ├── business/                 # EmailCraft Agent
    │   ├── __init__.py
    │   ├── agent.py
    │   ├── tools.py
    │   └── ui.py
    │
    ├── researcher/               # News Researcher Agent
    │   ├── __init__.py
    │   ├── agent.py
    │   ├── tools.py
    │   └── ui.py
    │
    ├── food/                     # RecipeGenie Agent
    │   ├── __init__.py
    │   ├── agent.py
    │   ├── tools.py
    │   └── ui.py
    │
    ├── finance/                  # PropWealth Agent
    │   ├── __init__.py
    │   ├── agent.py
    │   ├── tools.py
    │   └── ui.py
    │
    ├── quiz/                     # QuizMaster Pro Agent
    │   ├── __init__.py
    │   ├── agent.py
    │   ├── tools.py
    │   └── ui.py
    │
    └── medical/                  # MediScan Agent
        ├── __init__.py
        ├── agent.py
        ├── tools.py
        └── ui.py
```

---

## ✨ Features

### 📧 EmailCraft (Business)
- Multi-agent system (Writer + Reviewer handoff)
- Iterative revision loop (up to 3 times until scores ≥7/10)
- 4-dimensional scoring: Tone, Persuasion, CTA, Grammar
- Spam trigger word detection
- 7 pre-seeded email templates
- Database persistence for all generated emails

### 🔍 News Researcher (Research)
- Real-time web search via Tavily API
- Stock price lookup (stub data for stability)
- Investment gain/loss calculator
- Conversation memory with thread IDs

### 🍲 RecipeGenie (Food)
- 6 diet transformations: Vegan, Vegetarian, Keto, Gluten-Free, Low-Carb, Diabetic-Friendly
- 10 base recipes + 35+ substitution rules
- Nutritional comparison (before vs after)
- Substitution reasoning (WHY each swap was chosen)
- Custom recipe input support

### 💰 PropWealth (Finance)
- 9 financial tools orchestrated in sequence
- Mortgage EMI calculation
- Cash flow analysis (with vacancy, expenses, tax)
- 3 ROI metrics (Cap Rate, Cash-on-Cash, Total ROI)
- 5-year projection with appreciation + rent growth
- Risk scoring (1-10) with factor breakdown
- Scenario analysis (Worst/Base/Best case)
- 10 Pakistan cities market data
- Database persistence for all analyses

### 📝 QuizMaster Pro (Education)
- PDF upload + text extraction (PyMuPDF)
- Topic-based content retrieval (RAG pattern)
- 3 question types: MCQ, True/False, Short Answer
- Adaptive difficulty based on performance
- Mastery tracking per topic (SQLite)
- Visual mastery dashboard with progress bars
- Detailed explanations for wrong answers

### 💊 MediScan (Medical)
- 40+ medicines database (OTC + Prescription)
- 35+ drug-drug interaction rules
- 20+ food-medicine interaction warnings
- Severity classification (🔴 Severe, 🟡 Moderate, 🟢 Safe)
- Alternative medicine finder
- Mandatory medical disclaimers (guardrails)
- Database persistence for consultations

---

## ⚙️ Installation

### Prerequisites

- Python 3.10 or higher
- Git
- Groq API Key (free) — get from [console.groq.com](https://console.groq.com)
- Tavily API Key (free tier) — get from [tavily.com](https://tavily.com)

### Step-by-Step Setup

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/multi-agent-ai-hub.git
cd multi-agent-ai-hub

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# macOS/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Set up environment variables
cp .env.example .env
# Edit .env and add your API keys

# 6. Run the application
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

---

## 🔑 Configuration

Create a `.env` file in the project root:

```env
# Required: Groq API Key (for LLM)
GROQ_API_KEY=gsk_your_groq_api_key_here

# Required: Tavily API Key (for News Researcher)
TAVILY_API_KEY=tvly_your_tavily_api_key_here

# Optional: LangSmith Tracing
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=
LANGCHAIN_PROJECT=multi-agent-hub
```

### Getting API Keys

1. **Groq API Key (Free):**
   - Visit [console.groq.com](https://console.groq.com)
   - Sign up with Google or GitHub
   - Navigate to API Keys → Create API Key
   - Copy the `gsk_...` key

2. **Tavily API Key (Free — 1000 searches/month):**
   - Visit [tavily.com](https://tavily.com)
   - Sign up
   - Dashboard → API Keys → Create
   - Copy the `tvly_...` key

---

## 🚀 Usage

### Selecting an Agent

1. Open the app in your browser (`http://localhost:8501`)
2. In the **sidebar**, select a **Domain** (Business, Research, Food, Finance, Education, Medical)
3. Select the specific **Agent** from that domain
4. The main area will display the agent's custom UI

### Running Your First Query

1. Choose **Medical** → **💊 MediScan**
2. Paste this into the input box:
   ```
   I am on Warfarin (blood thinner) for my heart. I have a headache, can I take Aspirin or Brufen? Check all interactions.
   ```
3. Click **"🔍 Check Interactions"**
4. View the detailed interaction report with severity warnings

### Adding a New Agent

The architecture supports auto-discovery. To add a new agent:

1. Create a new folder under `agents/` (e.g., `agents/legal/`)
2. Add 4 files:
   - `__init__.py` (empty)
   - `tools.py` (your custom tools)
   - `agent.py` (must extend `BaseAgent`)
   - `ui.py` (Streamlit UI function)
3. Restart Streamlit — the new agent automatically appears in the sidebar!

Example `agent.py` skeleton:

```python
from agents.base_agent import BaseAgent

class LegalAgent(BaseAgent):
    NAME = "LegalAdvisor"
    DESCRIPTION = "Legal document analyzer"
    ICON = "scales"
    DOMAIN = "Legal"

    def run(self, user_input, thread_id="default", **kwargs):
        # Your logic here
        return response

    def render_ui(self):
        from .ui import render_legal_ui
        render_legal_ui(self)
```

---

## 🧪 Test Cases

### MediScan (Medical)

| Test | Input | Expected |
|---|---|---|
| Safe Combo | `Check interactions between: Panadol, Brufen` | 🟢 SAFE |
| Severe Interaction | `I'm on Warfarin. Can I take Aspirin?` | 🔴 SEVERE bleeding risk |
| Antibiotic + Painkiller | `Taking Augmentin, want to add Brufen` | 🟡 MODERATE GI effects |
| Food Warning | `What food to avoid with Metronidazole?` | 🔴 AVOID alcohol completely |

### EmailCraft (Business)

| Test | Input | Expected |
|---|---|---|
| Welcome Email | Type: Welcome, Brief: "Welcome email for new SaaS signup, 14-day trial" | Subject < 50 chars, all scores ≥7 |
| Revision Loop | Type: Newsletter, Brief: "Use ALL CAPS and !!!!" | Reviewer flags grammar, Writer revises |
| Cold Sales | Type: Sales, Brief: "Cold email to CTO of fintech startup" | Persuasion score ≥7, soft CTA |

### PropWealth (Finance)

| Test | Input | Expected |
|---|---|---|
| Strong Investment | Karachi, PKR 15M, 30% down, 80K rent, 16%, 15yr | Positive cash flow, BUY recommendation |
| Bad Investment | Faisalabad, PKR 60M, 30% down, 130K rent, 17.5%, 20yr | Negative cash flow, AVOID recommendation |

### QuizMaster Pro (Education)

| Test | Input | Expected |
|---|---|---|
| Full Quiz Flow | Upload PDF, topic "cell structure", 5 MCQs, easy | Quiz generates, evaluation works |
| Adaptive Difficulty | Score ≥85% on easy → next quiz medium | Mastery score updates correctly |

---

## 🎓 Concepts Demonstrated

This project serves as a comprehensive demonstration of modern AI engineering concepts:

| Concept | Where Implemented |
|---|---|
| **LangChain Agents (ReAct)** | All 6 agents use `create_agent` with ReAct pattern |
| **Custom Tools (`@tool`)** | 34 custom Python tools exposed to LLM |
| **Multi-Agent System** | EmailCraft: Writer + Reviewer handoff with revision loop |
| **Auto-Discovery Pattern** | `agents/__init__.py` automatically registers new agents |
| **Abstract Base Class** | `BaseAgent` enforces contract on all agents |
| **SQLite Persistence** | 6 separate databases for permanent storage |
| **Pydantic Schemas** | Structured data validation throughout |
| **RAG (Retrieval-Augmented Generation)** | QuizMaster: PDF text extraction + topic retrieval |
| **Adaptive Logic** | QuizMaster: difficulty adjusts based on score |
| **Guardrails** | MediScan: mandatory disclaimers, never prescribes |
| **Memory (Short-term)** | InMemorySaver for conversation context |
| **Memory (Long-term)** | SQLite mastery tracking in QuizMaster |
| **Multimodal Input** | QuizMaster: PDF file upload |
| **Severity Classification** | MediScan: 🔴🟡🟢 interaction severity |
| **Scenario Analysis** | PropWealth: Worst/Base/Best case modeling |
| **Risk Assessment** | PropWealth: 1-10 risk score with factor breakdown |

---

## 🗺️ Roadmap

Future enhancements planned:

- [ ] **LangGraph Migration** — Migrate from LangChain agents to LangGraph for complex state machines
- [ ] **User Authentication** — Per-user data isolation
- [ ] **LangSmith Integration** — Full production tracing and evaluation
- [ ] **MCP (Model Context Protocol)** — Universal tool integration
- [ ] **Deployment** — Deploy on Render, Railway, or HuggingFace Spaces
- [ ] **Voice Input** — Whisper STT for accessibility
- [ ] **Vector Database** — Chroma/FAISS for better RAG in QuizMaster
- [ ] **Rate Limiting** — Per-user API quota management
- [ ] **Audit Logging** — Complete action trail for compliance

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **LangChain** — Agent framework
- **Groq** — Free, fast LLM inference
- **Streamlit** — Rapid UI development
- **Tavily** — AI-friendly search API
- **PyMuPDF** — PDF text extraction

---

## 📬 Contact

Built with ❤️ by **[AQSA RASHEED]**

- GitHub: [@yourusername](https://github.com/aqsarasheed-dev)
- LinkedIn: [Your Name](https://linkedin.com/in/aqsarasheed)


If you found this project helpful, please ⭐ the repository!

---

## 🏆 Project Stats

- **6** AI Agents
- **6** Different Domains
- **34** Custom Tools
- **6** SQLite Databases
- **~1500+** Lines of Code
- **100%** Python
