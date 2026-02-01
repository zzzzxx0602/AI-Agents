# File: src/report_generator.py

from openai import OpenAI
from src.config import API_KEY, MODEL_NAME

# Initialize OpenAI Client
if API_KEY:
    client = OpenAI(api_key=API_KEY)
else:
    client = None


def generate_agent_prompt(target_ticker, valuation_summary, historical_df, peers_df):
    """
    Synthesizes the Agent's Prompt using computed quantitative data.
    """
    latest_hist = historical_df.iloc[0]
    avg_roe = historical_df['ROE (%)'].mean()

    prompt = f"Act as a Buy-Side Fundamental Analyst Agent. Write a detailed 1-page Investment Memo for {target_ticker}.\n\n"

    prompt += "SECTION 1: RELATIVE VALUATION (MARKET DATA)\n"
    for metric, data in valuation_summary.items():
        if isinstance(data, dict):
            prompt += f"- {metric}: {target_ticker} ({data['Target']}x) vs Peer Avg ({data['Peer_Avg']}x). "
            prompt += f"Verdict: Trading at a {data['Difference']}% {data['Status']}.\n"

    prompt += "\nSECTION 2: FUNDAMENTAL HEALTH (5-YEAR ANALYSIS)\n"
    prompt += f"- Profitability (ROE): Latest is {latest_hist['ROE (%)']}%. 5-Year Average is {avg_roe:.2f}%.\n"
    prompt += f"- Growth: Latest Revenue Growth is {latest_hist['Revenue Growth (%)']}%.\n"
    prompt += f"- Leverage: Current Debt-to-Equity ratio is {latest_hist['Debt/Equity']}.\n"
    prompt += f"- Efficiency: Asset Turnover is {latest_hist['Asset Turnover']}.\n"

    prompt += "\nSECTION 3: PEER DATA REFERENCE\n"
    prompt += peers_df[['Ticker', 'P/E', 'P/S', 'EV/EBITDA']].to_string(index=False)

    prompt += "\n\nTASK:\n"
    prompt += "Based on the above data, write a professional investment memo.\n"
    prompt += "1. Synthesize the valuation: Is the stock cheap or expensive?\n"
    prompt += "2. Assess quality: Does the high ROE or Growth justify the premium?\n"
    prompt += "3. Provide a final recommendation: Buy, Hold, or Sell.\n"

    # --- MARKDOWN INSTRUCTION ---
    prompt += "4. Format the output using **Markdown syntax** (use # for headers, ** for bolding, - for lists).\n"
    prompt += "IMPORTANT: Do NOT include any top metadata headers like 'Date', 'Prepared By', 'To', or 'From'. Start directly with the Investment Thesis."

    return prompt


def generate_memo_with_llm(prompt_text):
    """
    Sends the prompt to OpenAI API to generate the narrative.
    """
    if not client:
        return "Error: API Key is missing. Please check src/config.py"

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a senior financial analyst."},
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error calling LLM API: {e}"