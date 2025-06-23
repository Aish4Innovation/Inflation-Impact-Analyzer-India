import streamlit as st
import pandas as pd

# ---------- PAGE SETUP ----------
st.set_page_config(page_title="Inflation Impact Analyzer", layout="centered")
st.title("📈 Inflation Impact Analyzer – India (CPI)")
st.markdown("Analyze how ₹1000 in 2014 compares to today across groceries, fuel, housing, and more!")

# ---------- LOAD DATA ----------
df = pd.read_csv("cpi.csv")

# Drop rows where Year or Month is missing
df = df.dropna(subset=['Year', 'Month'])

# Fix common month typos and formats
month_map = {
    'Jan': 'January', 'Feb': 'February', 'Mar': 'March', 'Marcrh': 'March', 'Apr': 'April',
    'May': 'May', 'Jun': 'June', 'Jul': 'July', 'Aug': 'August', 'Sep': 'September',
    'Sept': 'September', 'Oct': 'October', 'Nov': 'November', 'Dec': 'December'
}
df['Month'] = df['Month'].astype(str).str.strip().str.capitalize().map(month_map).fillna(df['Month'])

# Convert Year and Date
df['Year'] = df['Year'].astype(int)
df['Date'] = pd.to_datetime(df['Month'] + ' ' + df['Year'].astype(str), format='%B %Y', errors='coerce')
df = df.dropna(subset=['Date'])  # Remove rows where date couldn't be parsed

# ---------- USER INTERFACE ----------
# Select CPI category
categories = df.columns[3:-1]  # Skip 'Sector', 'Year', 'Month'; exclude last column if it's "General index"
selected_category = st.selectbox("🧾 Choose a CPI Category", categories)

# Select year range
years = sorted(df['Year'].unique())
col1, col2 = st.columns(2)
with col1:
    start_year = st.selectbox("Start Year", years)
with col2:
    end_year = st.selectbox("End Year", years[::-1])

# Validate year selection
if start_year >= end_year:
    st.warning("⚠️ End year must be greater than start year.")
else:
    # Filter average CPI values for start and end year
    start_val = df[df['Year'] == start_year][selected_category].mean()
    end_val = df[df['Year'] == end_year][selected_category].mean()

    # Input amount
    amount = st.number_input(f"💰 Enter amount in ₹ (in {start_year})", min_value=1, value=1000)

    # Inflation adjustment
    adjusted = (end_val / start_val) * amount
    st.success(f"₹{amount} in {start_year} is worth approx. **₹{int(adjusted)}** in {end_year} for *{selected_category}*.")

    # ---------- PLOT CPI TREND ----------
    st.subheader(f"📊 CPI Trend for {selected_category}")
    chart_df = df[['Date', selected_category]].set_index('Date').sort_index()
    st.line_chart(chart_df)

# ---------- FOOTER ----------
st.caption("📊 Data Source: Government of India (via Kaggle). Built with ❤️ using Streamlit.")


# Graph explanation logic
inflation_percent = ((end_val - start_val) / start_val) * 100
direction = "increased" if inflation_percent > 0 else "decreased"

st.subheader("🧠 Inflation Insight")
st.markdown(f"""
Between **{start_year}** and **{end_year}**, the average price index for **{selected_category}** has {direction} by **{abs(inflation_percent):.2f}%**.

This means an item that cost ₹{amount} in {start_year} would now cost approximately ₹{int(adjusted)} in {end_year}.
""")




# ------------------ 🤖 Build Prompt for Gemini ------------------
# Smart summary for AI explanation
prompt = f"""
Between {start_year} and {end_year}, in India, the Consumer Price Index (CPI) for the category '{selected_category}' changed as follows:

- CPI in {start_year}: {start_val:.2f}
- CPI in {end_year}: {end_val:.2f}
- Inflation-adjusted value: ₹{amount} in {start_year} is worth ₹{int(adjusted)} in {end_year}.

This means that the prices for {selected_category.lower()} increased by approximately {((end_val - start_val) / start_val) * 100:.2f}%.

Please explain in simple terms:
1. What this means for the user.
2. Likely reasons why {selected_category.lower()} became more expensive.
3. What factors might have affected this trend in India between {start_year} and {end_year}.

Be brief, informative, and user-friendly.
"""

# Add CPI trend line
cpi_history = df[df['Year'].between(start_year, end_year)][['Year', selected_category]].groupby('Year').mean().reset_index()
trend_lines = "\n".join([f"{int(row.Year)}: {row[selected_category]:.2f}" for _, row in cpi_history.iterrows()])
prompt += f"\n\nCPI trend by year:\n{trend_lines}"

# ------------------ 🤖 Gemini Flash Integration ------------------
import google.generativeai as genai  # pip install google-generativeai

# ✅ Configure with your API key
genai.configure(api_key="YOUR API KEY")  # Replace this with your real key securely

# ✅ Use Gemini Flash 1.5 (latest)
model = genai.GenerativeModel(model_name="models/gemini-1.5-flash-latest")

# ✅ Generate content
response = model.generate_content(prompt)

# ✅ Show in Streamlit
st.subheader("🤖 AI Insight")
st.info(response.text)
