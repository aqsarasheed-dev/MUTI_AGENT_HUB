import streamlit as st
import uuid
import yfinance as yf
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Literal
from langchain_groq import ChatGroq
from langchain.agents import  create_agent
from langchain_core.tools import tool
from langchain_tavily import TavilySearch
from langgraph.checkpoint.memory import InMemorySaver


load_dotenv()
#llm setup
llm= ChatGroq(
    model= "openai/gpt-oss-20b",
    api_key=os.getenv("GROQ_API_KEY"),
    
    ) 
#custom tools
@tool
def get_stock_price(ticker: str) -> float:
   #docstring
    """ Get the current stock price for a given ticker symbol.
     use this when user ask for current price of a stock.      
     args:
      ticker symbol like AAPL, TSLA, NVDA etc


    """
    try:
        info = yf.Ticker(ticker).info
        price = info.get("regularMarketPrice")
        if price is None:
            return f"no price data found for {ticker}"
        return f"Current price of {ticker} is ${price:.2f}"
    except Exception as e:
        return f"could not fetch price for {ticker}: {e}"


@tool
   
def calculate_gain(buy_price: float, sell_price: float)-> str:
    """ 
    calculate the gain and loss between two prices
     use this when user ask for claulate profit , loos or returns
      arugs:
    buy_price = originol price 
     sell_price = current or selling price  """
    if buy_price <=0 :
        return "buy price should be greater than 0"
    gain =((sell_price - buy_price)/buy_price)*100
    return f"Gain/loss: {gain:+.2f}%"

     
search_tool = TavilySearch(max_results=1)

tools = [search_tool , get_stock_price, calculate_gain]


#agent with memory
@st.cache_resource
def get_agent():
    return create_agent(
        model=llm,
        tools=[search_tool , get_stock_price, calculate_gain],
        checkpointer=InMemorySaver(),
        system_prompt= """You are a analyst assistant.
     Rules:
     Remember user portfolio across turns.
     For news: use search tool, summarize in 3-4 lines.
     For prices: use get_stock_price.
     For gains: use calculate_gain.
     Give a concise summary. Do not include thinking steps."""

)
agent = get_agent()
#structred output 
class StockNewsSummary(BaseModel):
    ticker :str = Field(description="stock ticker ,e.g TSLA, NVDA")
    price: str = Field(description="current stock price")
    sentiment: Literal["positive","negative","neutral"]= Field(description= "sentiment of the recent news")
    headline: str = Field(description="Top headline , max 100 charcters")

class StockNewsreport(BaseModel):
    summaries: list[StockNewsSummary] = Field(description="List of stock news summaries")
    overall_sentiment: Literal["positive","negative","neutral"]= Field(description="Overall sentiment of the news report")

structured_llm=llm.with_structured_output(StockNewsreport)

#streamlitb webui


st.set_page_config(page_title="Stock News Summarizer", page_icon="📈")
st.title("Stock News Summarizer")


if "thread_id" not in st.session_state:
    st.session_state.thread_id= "user_001"

if "history" not in st.session_state:
    st.session_state.history = []

with st.sidebar:
    st.header("about")
    if st.button("new chat"):
        st.session_state.thread_id = str(uuid.uuid4())[:8]
        st.session_state.history = []
        st.rerun()



user_input = st.text_input("Enter stocks...", "Tesla , Nivdia ,Apple")

if st.button("send") and user_input:
    config = {"configurable": {"thread_id": st.session_state.thread_id}}

    with st.spinner("searching for News..."):
        try:
            result = get_agent().invoke(
                {"messages": [{"role": "user", "content": f"Latest news for: {user_input}"}]},
                config,
            )

            final_message = result["messages"][-1]
            if isinstance(final_message.content, list):
                summary = final_message.content[0].get("text", "")
            else:
                summary = final_message.content

            st.session_state.history.append(("user", user_input))
            st.session_state.history.append(("agent", summary))

        except Exception as e:
            st.error(f"Error: {e}")
            st.exception(e)

#conversation history
st.subheader("Conversation History")
for role, text in st.session_state.history:
    if role == "user":
        st.markdown(f"**User:** {text}")
    else:
        st.markdown(f"**agent:** {text}")
#structured summary table
if st.session_state.history:
    st.divider()
    st.subheader("Sturctured Summary")
    if st.button("Generate table"):
        with st.spinner(" extracted structured data ..."):
            latest = next((t for r, t in reversed(st.session_state.history) if r == "agent"), "")
            report = structured_llm.invoke(f"Extract stuructured data from text:\n\n{latest}")

        st.write(f"overall sentiment: {report.overall_sentiment}")

        st.dataframe([
            {
                "ticker": row.ticker,
                "price": row.price,
                "sentiment": row.sentiment,
                "headline": row.headline,
            }
            for row in report.summaries
        ])