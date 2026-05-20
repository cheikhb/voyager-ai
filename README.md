# ✈️ Voyager AI – Travel Agency Agent

> A production-ready AI travel concierge built with **LangChain 1.x** + **LangGraph** + **Streamlit**.  
> Plan trips, search flights & hotels, build itineraries, and simulate bookings — all through natural conversation.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-1.x-green.svg)](https://www.langchain.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 👨‍💻 Author

| | |
|---|---|
| **Name** | Cheikh Badiane |
| **Email** | [cheikhbadiane99@gmail.com](mailto:cheikhbadiane99@gmail.com) |
| **GitHub** | [@cheikhb](https://github.com/cheikhb) |
| **Repository** | [github.com/cheikhb/voyager-ai](https://github.com/cheikhb/voyager-ai) |

---

## 📋 Overview

Voyager AI is an intelligent travel concierge agent that helps customers plan their vacations end-to-end:

- 🗺️ **Gather preferences** — budget, destination interests, travel dates, group type
- ✈️ **Search flights & hotels** — via SerpAPI (live) or realistic simulated data
- 🎭 **Find activities** — curated experiences based on travel style
- 📅 **Build itineraries** — detailed day-by-day plans with tips and cost estimates
- 🏨 **Handle bookings** — flight, hotel, and activity confirmations with reference numbers
- 🌤️ **Ongoing support** — weather forecasts, currency conversion, travel advisories
- 📊 **Evaluation dashboard** — 4-layer metrics (Retrieval, Generation, Agentic, LLM Judge)

---

## 🗂️ Project Structure

```
voyager-ai/
├── app.py              # Streamlit UI (chat interface + metrics dashboard)
├── agent.py            # LangGraph React Agent (LangChain 1.x)
├── tools.py            # 8 custom LangChain tools
├── metrics.py          # Evaluation layer (RAG + Agentic metrics)
├── utils.py            # Helpers (session state, export)
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables template
├── .gitignore          # Git ignored files
└── README.md           # This file
```

---

## ⚙️ Architecture

```
User (Streamlit Chat)
        │
        ▼
  TravelAgent (agent.py)
  ├── LLM: GPT-4o (via langchain-openai)
  ├── Agent: create_react_agent (LangGraph)
  ├── Memory: MemorySaver (thread-based)
  └── Tools (tools.py):
      ├── search_flights          ← SerpAPI (live) or simulated
      ├── search_hotels           ← SerpAPI (live) or simulated
      ├── search_activities       ← Simulated (curated data)
      ├── build_itinerary         ← Generates day-by-day plan
      ├── make_booking            ← Returns confirmation ref
      ├── get_weather_forecast    ← Simulated forecast
      ├── convert_currency        ← Static exchange rates
      └── get_travel_advisory     ← Visa & safety info
        │
        ▼
  TravelEvaluator (metrics.py)   ← Fully decoupled evaluation layer
  ├── RetrievalMetrics            ← Document quality (RAG)
  ├── GenerationMetrics           ← Answer quality + hallucination detection
  ├── AgenticMetrics              ← Pipeline completeness + latency
  └── LLMJudgeMetrics             ← Semantic scoring via GPT-4o-mini
```

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/cheikhb/voyager-ai.git
cd voyager-ai
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API keys

Copy the example environment file and fill in your keys:

```bash
cp .env.example .env
```

Edit `.env`:

```env
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxx
SERPAPI_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx   # optional
```

| Key | Required | Where to get |
|-----|----------|--------------| 
| `OPENAI_API_KEY` | ✅ Yes | https://platform.openai.com/api-keys |
| `SERPAPI_API_KEY` | ⬜ Optional | https://serpapi.com |

### 5. Run the app

```bash
streamlit run app.py
```

Open **http://localhost:8501** in your browser. The agent starts automatically — no API key input required in the UI.

---

## 💬 Example Conversations

**Full trip planning:**
```
I want to spend 7 days in Japan in April. Budget $3,000.
I love food and temples. Travelling as a couple.

→ Agent calls: search_flights → search_hotels → search_activities → build_itinerary
→ Returns: complete 7-day itinerary with options, costs, and tips
```

**Booking:**
```
Book the second hotel for Cheikh Badiane, cheikhbadiane99@gmail.com

→ Agent calls: make_booking
→ Returns: Confirmation VOY-20240315-84721
```

**Support queries:**
```
What's the weather like in Tokyo in April?
How much is €500 in Japanese Yen?
Do I need a visa for Japan as a French citizen?
```

---

## 📊 Evaluation Metrics

The app includes a built-in **evaluation dashboard** aligned with the RAG & Agentic AI evaluation guideline:

| Layer | Metrics |
|-------|---------|
| 🔎 **Retrieval** | raw_count, selected_count, top_1_score, avg_score, compression_ratio |
| ✍️ **Generation** | grounded, has_answer, answer_length, hallucination_risk |
| 🤖 **Agentic** | pipeline_complete, execution_steps, agents_used, latency_ms |
| ⚖️ **LLM Judge** | pertinence, fidélité, complétude, clarté, score_global (0–5) |

---

## 🛠️ Customisation

### Add a real booking API

```python
# In tools.py – BookingTool._run()
def _run(self, item_type, item_id, passenger_name, email, special_requests=None):
    response = requests.post("https://your-booking-api.com/book", json={...})
    return json.dumps(response.json())
```

### Switch LLM model

```python
# In agent.py – cheaper option
self.llm = ChatOpenAI(model="gpt-4o-mini", api_key=openai_api_key)
```

---

## 🔒 Security

- API keys are loaded from `.env` — **never hardcoded**
- `.env` is listed in `.gitignore` — **never committed to Git**
- Use `.env.example` to share the required variable names without values

---

## 📦 Deployment

### Streamlit Cloud

1. Push to GitHub: `git push origin main`
2. Go to https://share.streamlit.io
3. Connect your repo `cheikhb/voyager-ai`, set `app.py` as entry point
4. Add secrets: `OPENAI_API_KEY` and `SERPAPI_API_KEY` in the dashboard

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501"]
```

```bash
docker build -t voyager-ai .
docker run -p 8501:8501 --env-file .env voyager-ai
```

---

## 📝 Requirements

- Python 3.10+
- OpenAI API key (GPT-4o access recommended)
- SerpAPI key (optional, for live flight/hotel data)
- Internet connection

---

## 📄 License

MIT License — feel free to use, modify, and distribute.

---

*Built with ❤️ by **Cheikh Badiane** · [cheikhbadiane99@gmail.com](mailto:cheikhbadiane99@gmail.com)*  
*Powered by LangChain 1.x · LangGraph · Streamlit · OpenAI GPT-4o*
