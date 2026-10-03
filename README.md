# 📈 Stock News Summarizer

An AI agent that searches the web for latest stock news, analyzes sentiment, and returns a structured summary.

## 🎯 What It Does

- Takes stock tickers as input (e.g., `Tesla, Nvidia, Apple`)
- Uses an LLM agent (Groq + Llama/GPT-OSS) to search the web
- Returns a summarized news digest per stock
- Displays structured data (ticker, sentiment, headline) as a table
- Remembers your portfolio across turns

## 🛠️ Tech Stack

| Component | Purpose |
|---|---|
| **Streamlit** | Web UI |
| **LangChain v1.0** | Agent framework |
| **Groq** | LLM inference |
| **Tavily** | Web search tool |
| **yfinance** | Stock price data |
| **Pydantic** | Structured output schema |

## 🚀 Setup

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/stock-news-summarizer.git
cd stock-news-summarizer
```

### 2. Create virtual environment
```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
source .venv/bin/activate # macOS/Linux
```

### 3. Install dependencies
```bash
python -m pip install -r requirements.txt
```

### 4. Set up API keys
Create a `.env` file in the project root:
```
GROQ_API_KEY=your_groq_key_here
TAVILY_API_KEY=your_tavily_key_here
```

Get keys from:
- Groq: https://console.groq.com
- Tavily: https://tavily.com

### 5. Run the app
```bash
streamlit run app.py
```



## 🧠 How It Works

1. User enters stock tickers
2. Agent decides which tool to use (search, price, calculator)
3. Tools execute and return data
4. LLM synthesizes a summary
5. Structured output extracts table data
6. Streamlit renders everything

## 📝 License

MIT