{\rtf1\ansi\ansicpg1252\cocoartf2822
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import streamlit as st\
import requests\
import datetime\
\
# ---- USER CONFIG ---- #\
API_KEY = st.text_input("Enter your TD Ameritrade API Key (Consumer Key)", type="password")\
BASE_URL = "https://api.tdameritrade.com/v1"\
\
symbol = "SPY"\
\
# ---- FUNCTIONS ---- #\
def get_option_chain(symbol, from_date, to_date):\
    url = f"\{BASE_URL\}/marketdata/chains"\
    params = \{\
        "apikey": API_KEY,\
        "symbol": symbol,\
        "contractType": "CALL",\
        "strikeCount": 30,\
        "includeQuotes": "FALSE",\
        "strategy": "SINGLE",\
        "fromDate": from_date,\
        "toDate": to_date\
    \}\
    response = requests.get(url, params=params)\
    return response.json() if response.status_code == 200 else None\
\
def extract_spreads(option_chain, today_expiry, tomorrow_expiry):\
    spreads = []\
    if not option_chain or "callExpDateMap" not in option_chain:\
        return spreads\
\
    call_map = option_chain["callExpDateMap"]\
\
    if today_expiry not in call_map or tomorrow_expiry not in call_map:\
        return spreads\
\
    today_strikes = list(call_map[today_expiry].keys())\
    tomorrow_strikes = list(call_map[tomorrow_expiry].keys())\
\
    for t_strike in today_strikes:\
        for tm_strike in tomorrow_strikes:\
            strike_gap = float(tm_strike) - float(t_strike)\
            if 2 <= strike_gap <= 3:\
                short_option = call_map[today_expiry][t_strike][0]\
                long_option = call_map[tomorrow_expiry][tm_strike][0]\
\
                debit = float(long_option["ask"] or 0) - float(short_option["bid"] or 0)\
                max_value = strike_gap\
                if debit > 0 and debit < max_value:\
                    roi = (max_value - debit) / debit * 100\
                    spreads.append(\{\
                        "Buy Strike (T+1)": tm_strike,\
                        "Sell Strike (Today)": t_strike,\
                        "Net Debit ($)": round(debit, 2),\
                        "Max Value ($)": round(max_value, 2),\
                        "ROI (%)": round(roi, 1),\
                        "Buy Expiry": tomorrow_expiry.split(':')[0],\
                        "Sell Expiry": today_expiry.split(':')[0]\
                    \})\
    return sorted(spreads, key=lambda x: -x["ROI (%)"])\
\
# ---- MAIN APP ---- #\
st.title("SPY Diagonal Spread Scanner")\
st.markdown("Finds optimal SPY diagonal call spreads for today vs tomorrow with $2\'96$3 gap.")\
\
if API_KEY:\
    today = datetime.date.today()\
    tomorrow = today + datetime.timedelta(days=1)\
\
    from_date = today.strftime('%Y-%m-%d')\
    to_date = tomorrow.strftime('%Y-%m-%d')\
\
    with st.spinner("Fetching SPY options..."):\
        option_chain = get_option_chain(symbol, from_date, to_date)\
\
    # Find expiration keys\
    exp_map = option_chain.get("callExpDateMap", \{\})\
    exp_keys = list(exp_map.keys())\
    if len(exp_keys) < 2:\
        st.error("Could not find enough expiries. Market might be closed or data missing.")\
    else:\
        today_expiry = exp_keys[0]\
        tomorrow_expiry = exp_keys[1]\
        spreads = extract_spreads(option_chain, today_expiry, tomorrow_expiry)\
\
        if spreads:\
            st.success(f"Found \{len(spreads)\} diagonal spreads:")\
            st.dataframe(spreads)\
        else:\
            st.warning("No valid diagonal spreads found with $2\'96$3 gap.")\
else:\
    st.info("Enter your TD Ameritrade API key above to begin.")}