# Fundamental Analyst Agent (Track A) 

## 1. Project Overview
This project implements an AI-powered Fundamental Analyst Agent designed to automate bottom-up security selection. The agent integrates **yfinance** for real-time market data ingestion and **OpenAI GPT-4o** for investment reasoning.

**Key Features:**
- Automated Data Ingestion (5-year historical financials).
- Deterministic Analytics (P/E, EV/EBITDA, ROE calculation).
- Peer Group Auto-Discovery.
- Professional Investment Memo Generation (Markdown).

## 2. File Structure
```text
Group_05_Final_Submission/
├── main.py                 # Entry point for the Fundamental Agent
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
└── src/
    ├── config.py           # Configuration (API Key setup)
    ├── data_ingestion.py   # Yahoo Finance data fetching pipeline
    ├── analytics.py        # Valuation & ratio calculation engine
    └── report_generator.py # LLM prompt engineering & report synthesis
    
3. Installation & Setup
Step 1: Install Dependencies
Ensure you have Python 3.10+ installed. Run the following command to install required libraries:3. Installation & Setup
pip install -r requirements.txt

Step 2: Configure API Key
1.Open src/config.py.
2.Insert your OpenAI API Key into the API_KEY variable:
API_KEY = "sk-proj-..."

4. How to Run
To start the agent, simply run the main script from the root directory:

python main.py

Interaction Flow:

1.The terminal will ask for a company name (e.g., enter Starbucks or SBUX).

2.The agent will identify the ticker, find peers (e.g., MCD, DNUT), and fetch data.

3.A Markdown report will be generated in the root folder: SBUX_Investment_Memo.md.

5. Output Example
The agent generates:

Investment Memo: A qualitative analysis of valuation and risks.

Audit Trail: Raw quantitative data tables appended to the end of the memo for verification.