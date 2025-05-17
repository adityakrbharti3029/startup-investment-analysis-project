import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import plotly.express as px

# --- Page Config ---
st.set_page_config(page_title="🚀 Startup Investments Analysis", layout="wide")

# --- Introduction ---
st.markdown("""
### 🗺️ **Startup Investment Analysis Dashboard**
Welcome to a data-driven journey through the world of startup investments.  
Discover which countries lead, where investors are betting big, and what sectors are booming. Ready to explore? 🚀
""")

# --- Data Loading with Caching for Speed ---
@st.cache_data
def load_data():
    df = pd.read_csv('investments_VC.csv', encoding='ISO-8859-1')
    df.columns = df.columns.str.strip()
    df['funding_total_usd'] = df['funding_total_usd'].replace('[\$,]', '', regex=True)
    df['funding_total_usd'] = pd.to_numeric(df['funding_total_usd'], errors='coerce')
    df['region_clean'] = df['region'].fillna(df['city']).str.strip().str.replace(r"\s+", " ", regex=True)
    df['founded_year'] = pd.to_datetime(df['founded_at'], errors='coerce').dt.year
    return df

df = load_data()

# --- Sidebar Filters ---
st.sidebar.header("🔍 Filter Data")

# Year Range Filter
min_year, max_year = int(df['founded_year'].min()), int(df['founded_year'].max())
year_range = st.sidebar.slider("Select Year Range", min_year, max_year, (2005, 2020))

# Country Filter
countries = df['country_code'].dropna().unique().tolist()
selected_countries = st.sidebar.multiselect("Filter by Country", sorted(countries), default=countries)

# Market Filter
markets = df['market'].dropna().unique().tolist()
selected_markets = st.sidebar.multiselect("Filter by Market", sorted(markets), default=markets)

# Apply filters to dataset
filtered_df = df[
    (df['founded_year'].between(*year_range)) &
    (df['country_code'].isin(selected_countries)) &
    (df['market'].isin(selected_markets))
]

# --- Helper: Human readable number formatting ---
def human_format(num):
    if num >= 1e9:
        return f"${num/1e9:.2f}B"
    elif num >= 1e6:
        return f"${num/1e6:.2f}M"
    elif num >= 1e3:
        return f"${num/1e3:.2f}K"
    else:
        return f"${num:.2f}"

# --- Key Metrics Calculation ---
total_startups = filtered_df['name'].nunique()
total_funding = filtered_df['funding_total_usd'].sum()
countries_covered = filtered_df['country_code'].nunique()
avg_funding = filtered_df.groupby('name')['funding_total_usd'].sum().mean()
total_rounds = filtered_df['funding_rounds'].sum()

# --- Display Key Metrics ---
st.markdown("### 🌟 **Key Metrics Overview**")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("🏢 Total Startups", f"{total_startups:,}")
col2.metric("💰 Total Funding", human_format(total_funding))
col3.metric("🌍 Countries Covered", countries_covered)
col4.metric("📈 Avg Funding/Startup", human_format(avg_funding))
col5.metric("🔄 Total Funding Rounds", human_format(total_rounds))

# --- Top 10 Companies Funding Progress ---
st.markdown("### 📶 **Top 10 Companies Funding Progress**")
top10 = filtered_df[['name', 'funding_total_usd']].dropna().sort_values(by='funding_total_usd', ascending=False).head(10)
max_fund = top10['funding_total_usd'].max()

for _, row in top10.iterrows():
    pct = (row['funding_total_usd'] / max_fund) * 100
    st.text(f"{row['name']} - {human_format(row['funding_total_usd'])}")
    st.progress(min(int(pct), 100))

# --- Top 5 Countries Funding Contribution ---
st.markdown("### 🌍 **Top 5 Countries Funding Contribution**")

country_symbols = {
    'USA': '🇺🇸 $', 'IND': '🇮🇳 ₹', 'GBR': '🇬🇧 £', 'CHN': '🇨🇳 ¥', 'CAN': '🇨🇦 $',
    'DEU': '🇩🇪 €', 'FRA': '🇫🇷 €', 'ISR': '🇮🇱 ₪', 'SGP': '🇸🇬 S$', 'AUS': '🇦🇺 A$'
}

top_countries = filtered_df.groupby('country_code')['funding_total_usd'].sum().sort_values(ascending=False).head(5)
total_global = filtered_df['funding_total_usd'].sum()

for country, fund in top_countries.items():
    symbol = country_symbols.get(country, '🌐 $')
    pct = (fund / total_global) * 100
    st.markdown(f"**{symbol} {country}** — {human_format(fund)}")
    st.progress(min(int(pct), 100))

# --- Funding Trend of Selected Market ---
st.markdown("### 📈 Funding Trend of a Selected Market")
selected_market = st.selectbox("🔍 Choose a Market", sorted(filtered_df['market'].dropna().unique()))

market_df = filtered_df[filtered_df['market'] == selected_market]
trend = market_df.groupby('founded_year')['funding_total_usd'].sum().dropna()

fig_market_trend = px.line(
    x=trend.index,
    y=trend.values,
    labels={'x': 'Year', 'y': 'Total Funding (USD)'},
    title=f"💸 Funding Trend in {selected_market} Market",
    markers=True,
    color_discrete_sequence=['#00BFC4']
)
fig_market_trend.update_traces(line=dict(width=3), marker=dict(size=6))
st.plotly_chart(fig_market_trend, use_container_width=True)

st.info(f"""
📌 **Insight:** The funding trend of **{selected_market}** market shows how investment interest has evolved over time.  
Peaks 🔺 indicate booming years, dips 🔻 show cooling phases. Use this to spot promising or declining sectors. ⚖️
""")

# --- Word Cloud of Top Market Segments ---
st.markdown("### ☁️ Word Cloud of Top Market Segments")
text = ' '.join(filtered_df['market'].dropna().astype(str).tolist())
wordcloud = WordCloud(width=800, height=400, background_color='white', colormap='viridis').generate(text)

fig_wc, ax_wc = plt.subplots(figsize=(10, 5))
ax_wc.imshow(wordcloud, interpolation='bilinear')
ax_wc.axis('off')
st.pyplot(fig_wc)

st.info("📌 **Insight:** Word cloud shows the most common startup markets. Bigger words = more startups.")

# --- Top 10 Markets by Total Funding ---
st.markdown("### 🌐 Top 10 Markets by Total Funding")
top_markets = filtered_df.groupby('market')['funding_total_usd'].sum().sort_values(ascending=False).head(10).reset_index()
fig2 = px.bar(top_markets, x='market', y='funding_total_usd',
              labels={'funding_total_usd': 'Total Funding (USD)'},
              title='Top Funded Markets')
st.plotly_chart(fig2, use_container_width=True)

st.info("📌 **Insight:** These sectors have attracted the most investor funding. 📈")

# --- Funding Trend Over the Years ---
st.markdown("### 📆 Funding Trend Over the Years")
yearly_funding = filtered_df.groupby('founded_year')['funding_total_usd'].sum().dropna()
fig3 = px.line(x=yearly_funding.index, y=yearly_funding.values, title="Funding Trend Over Years")
st.plotly_chart(fig3)
st.info("📌 **Insight:** Shows how total funding has changed year-by-year. 📅")

# --- Top 10 Funded Companies ---
st.markdown("### 🏆 Top 10 Funded Companies")
top_companies = filtered_df[['name', 'market', 'country_code', 'funding_total_usd']] \
    .sort_values(by='funding_total_usd', ascending=False).dropna().head(10)
fig4 = px.bar(top_companies, x='funding_total_usd', y='name', color='country_code',
              orientation='h',
              labels={'funding_total_usd': 'Funding (USD)', 'name': 'Company'},
              title='Top Funded Companies')
st.plotly_chart(fig4, use_container_width=True)
st.info("📌 **Insight:** Most heavily funded startups showing investor confidence. 🚀")

# --- Detailed Startup Profiles for Top 10 ---
st.markdown("### 🧬 Startup Profiles")
for i, row in top10.iterrows():
    with st.expander(f"{row['name']}"):
        market = filtered_df[filtered_df['name'] == row['name']]['market'].values[0]
        country = filtered_df[filtered_df['name'] == row['name']]['country_code'].values[0]
        st.markdown(f"**Market:** {market}")
        st.markdown(f"**Country:** {country}")
        st.markdown(f"**Total Funding:** {human_format(row['funding_total_usd'])}")

# --- Market Segment Distribution Pie Chart ---
st.markdown("### 🎈 Market Segment Distribution (Top 10)")
market_dist = filtered_df['market'].value_counts(normalize=True).head(10) * 100
fig5 = px.pie(names=market_dist.index, values=market_dist.values,
              title='Top 10 Market Segments')
st.plotly_chart(fig5, use_container_width=True)
st.info("📌 **Insight:** Shows dominant industries in the startup ecosystem. 🧭")

# --- Suggested Emerging Markets for Investment ---
st.markdown("### 🧠 Suggested Markets for Investment")
emerging_markets = filtered_df[filtered_df['founded_year'] > 2015].groupby('market')['funding_total_usd'].sum()
top_emerging = emerging_markets.sort_values(ascending=False).head(5)

for market, fund in top_emerging.items():
    st.success(f"📌 **{market}** — {human_format(fund)}")

# --- Startup Status Overview ---
st.markdown("### 📊 Startup Survival Overview")
status_data = {
    'Status': ['Operating', 'Closed', 'Unknown'],
    'Count': [41845, 2608, 4986]  # Adjust if you want to calculate dynamically
}
df_status = pd.DataFrame(status_data)
df_status['Percentage'] = (df_status['Count'] / df_status['Count'].sum()) * 100
df_status['All'] = 'Startup Status'

fig_status = px.bar(
    df_status,
    x='All',
    y='Percentage',
    color='Status',
    text=df_status['Percentage'].round(1).astype(str) + '%',
    title="📊 Startup Survival Overview (Pictorial Stacked Style)",
    color_discrete_sequence=px.colors.qualitative.Set2
)
fig_status.update_layout(
    xaxis_title=None,
    yaxis_title='Percentage',
    yaxis=dict(showgrid=False, showticklabels=False),
    bargap=0.2,
    showlegend=True,
    height=400
)
fig_status.update_traces(textposition='inside')

st.plotly_chart(fig_status, use_container_width=True)
st.info("📌 **Insight:** Proportion of startups by status — Operating, Closed, or Unknown. 👁️")

# --- Footer ---
st.markdown("---")
st.markdown("<center>👨‍💻 Made with ❤️ by Aditya Kumar Bharti — 🏆 Startup Investment Dashboard 2025 — IIT ROPAR</center>", unsafe_allow_html=True)
