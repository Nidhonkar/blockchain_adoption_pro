import streamlit as st
import pandas as pd
import altair as alt
import pydeck as pdk
import requests
from datetime import datetime, timedelta
from pathlib import Path

st.set_page_config(page_title="Blockchain adoption", page_icon="₿", layout="wide")

# ---------- Styles (neon/glass) ----------
st.markdown("""
<style>
.big-title { font-size: 42px; font-weight: 800; letter-spacing: .5px; }
.hero { padding: 18px 22px; border-radius: 18px;
  background: linear-gradient(135deg, rgba(247,147,26,.18), rgba(37,99,235,.14));
  border: 1px solid rgba(255,255,255,.08); }
.card { padding: 14px 16px; border-radius: 16px;
  background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); }
.kpi { font-size: 36px; font-weight: 800; }
.caption { color: #cbd5e1; font-size: 14px; }
</style>
""", unsafe_allow_html=True)

DATA_DIR = Path("data")

def load_csv(name):
    df = pd.read_csv(DATA_DIR / name)
    if "date" in df.columns:
        try:
            df["date"] = pd.to_datetime(df["date"])
        except: pass
    return df

# ---------- Live data helpers ----------
@st.cache_data(ttl=3600)
def fetch_tx_counts_coinmetrics(assets=("btc","eth")) -> pd.DataFrame:
    # Coin Metrics Community API — Metric: TxCnt
    base = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
    params = {"assets": ",".join(assets), "metrics": "TxCnt", "frequency": "1d", "page_size": 10000}
    r = requests.get(base, params=params, timeout=30)
    r.raise_for_status()
    js = r.json()
    rows = []
    for item in js.get("data", []):
        rows.append({
            "time": item["time"][:10],
            "asset": item["asset"],
            "tx": float(item["TxCnt"]) if item.get("TxCnt") is not None else None
        })
    df = pd.DataFrame(rows)
    df["time"] = pd.to_datetime(df["time"])
    pivot = df.pivot(index="time", columns="asset", values="tx").rename(columns=str.upper).sort_index()
    return pivot

@st.cache_data(ttl=1800)
def fetch_stablecoin_caps(ids=("tether","usd-coin","dai","true-usd")) -> pd.DataFrame:
    # CoinGecko public API
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency":"usd", "ids": ",".join(ids), "per_page": len(ids)}
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    return pd.DataFrame([{"name": d["name"], "symbol": d["symbol"].upper(), "market_cap": d["market_cap"]} for d in data])

# ---------- Load static/fallback data ----------
df_internet = load_csv("adoption_internet.csv")
df_blockchain = load_csv("adoption_blockchain.csv")
df_tx = load_csv("transactions_comparison.csv")
df_btc_eth_fb = load_csv("btc_eth_volumes.csv")
df_fees = load_csv("remittance_fees.csv")
df_token = load_csv("tokenization_assets.csv")
df_risk  = load_csv("risks_opportunities.csv")
df_cbdc  = load_csv("cbdc_projects.csv")
df_cbdc_map = load_csv("cbdc_map.csv")
df_defi = load_csv("defi_tvl.csv")
df_vol = load_csv("volatility_series.csv")
df_liq = load_csv("liquidity_series.csv")
df_energy = load_csv("energy_comparison.csv")
df_emix = load_csv("energy_mix.csv")
df_reg = load_csv("regulation_timeline.csv")
df_nfts = load_csv("nfts_market.csv")

# ---------- Stablecoin caps fallback CSV ----------
df_stables_fb = pd.read_csv(DATA_DIR / "stablecoin_caps_fallback.csv")

# ---------- Sidebar ----------
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["🏠 Home","📈 Adoption","💸 Transactions & Costs","₿ Supply","💱 Stablecoins & DeFi","📊 Markets","🌿 Energy","🎨 NFTs","🌍 Adoption Map","📜 Regulation"])
presentation = st.sidebar.checkbox("Presentation Mode (simplify visuals)", value=True)
if presentation: alt.themes.enable("none")

# ---------- Home ----------
if page == "🏠 Home":
    st.markdown('<div class="hero"><div class="big-title">₿ Blockchain adoption</div><div class="caption">Crypto‑styled dashboard with neon glass cards, curated metrics, and LIVE charts.</div></div>', unsafe_allow_html=True)
    st.write("")
    c1,c2,c3 = st.columns(3)
    with c1:
        st.markdown('<div class="card"><div>⛓️ Years since Bitcoin genesis</div><div class="kpi">%s+</div><div class="caption">Bitcoin launched in 2009 — the “email” moment for blockchain.</div></div>' % (datetime.now().year-2009), unsafe_allow_html=True)
    with c2:
        last30 = int(df_tx.tail(30)["btc_daily_tx"].mean())
        st.markdown(f'<div class="card"><div>₿ Avg daily BTC tx (30d)</div><div class="kpi">{last30:,}</div><div class="caption">Rolling activity snapshot (illustrative fallback).</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="card"><div>🏦 CBDC projects in table</div><div class="kpi">{len(df_cbdc)}</div><div class="caption">Sample list; swap with BIS/IMF tracker.</div></div>', unsafe_allow_html=True)

# ---------- Adoption ----------
elif page == "📈 Adoption":
    st.header("📈 Adoption — Internet vs Blockchain")

    col1,col2 = st.columns(2)
    with col1:
        chart_inet = alt.Chart(df_internet).mark_area(opacity=0.7, color="#3b82f6").encode(
            x=alt.X("year:O", title="Year"), y=alt.Y("users_millions_est:Q", title="Users (M)"),
            tooltip=["year","users_millions_est"]
        ).properties(title="Internet adoption (est.)", height=320)
        st.altair_chart(chart_inet, use_container_width=True)
        st.caption("Internet users scaled on open standards (TCP/IP/HTTP), unlocking a layered innovation stack.")

    with col2:
        chart_bc = alt.Chart(df_blockchain).mark_area(opacity=0.8, color="#F7931A").encode(
            x=alt.X("year:O", title="Year"), y=alt.Y("users_millions_est:Q", title="Users (M)"),
            tooltip=["year","users_millions_est"]
        ).properties(title="Blockchain/Crypto adoption (est.)", height=320)
        st.altair_chart(chart_bc, use_container_width=True)
        st.caption("Blockchain growth shows early S‑curve traits as wallets, exchanges and L2s mature.")

    st.markdown("### Indexed adoption (start year = 100)")
    di = df_internet.copy(); db = df_blockchain.copy()
    di["index"] = 100*di["users_millions_est"]/di["users_millions_est"].iloc[0]
    db["index"] = 100*db["users_millions_est"]/db["users_millions_est"].iloc[0]
    di["series"]="Internet"; db["series"]="Blockchain"
    d = pd.concat([di[["year","index","series"]], db[["year","index","series"]]])
    chart_idx = alt.Chart(d).mark_line(point=True).encode(
        x="year:O", y=alt.Y("index:Q", title="Index (start=100)"),
        color=alt.Color("series:N", legend=alt.Legend(title="")),
        tooltip=["series","year","index"]
    ).properties(height=320)
    st.altair_chart(chart_idx, use_container_width=True)
    st.caption("Indexing normalizes scale and highlights **shape** similarities between eras.")

# ---------- Transactions & Costs ----------
elif page == "💸 Transactions & Costs":
    st.header("💸 Transactions & Costs")

    tabs = st.tabs(["BTC vs SWIFT", "BTC vs ETH (LIVE)", "Remittance: Cost & Speed"])

    with tabs[0]:
        t = df_tx.copy().sort_values("date")
        t["btc_ma7"] = t["btc_daily_tx"].rolling(7).mean()
        t["swift_ma7"] = t["swift_daily_msgs"].rolling(7).mean()

        st.markdown("#### ₿ BTC transactions — daily vs 7‑day average")
        st.line_chart(t.set_index("date")[["btc_daily_tx","btc_ma7"]])
        st.caption("Daily BTC transactions are choppy; the MA7 smooths the line for trend spotting.")

        st.markdown("#### 📨 SWIFT messages — daily vs 7‑day average")
        st.line_chart(t.set_index("date")[["swift_daily_msgs","swift_ma7"]])
        st.caption("SWIFT runs at global banking scale. The chart frames **architecture differences** rather than absolute parity.")

    with tabs[1]:
        st.markdown("#### BTC vs ETH transaction volume — LIVE (Coin Metrics, 7‑day MA)")
        try:
            live = fetch_tx_counts_coinmetrics()
            live_ma7 = live.rolling(7).mean()
            st.line_chart(live_ma7, height=260)
            st.caption("Source: Coin Metrics Community API — Metric ‘TxCnt’, 7‑day MA.")
        except Exception as e:
            st.warning("Live fetch failed or rate limited. Showing fallback series.")
            b = df_btc_eth_fb.copy().sort_values("date").set_index("date")[["btc_daily_tx","eth_daily_tx"]]
            b = b.rename(columns={"btc_daily_tx":"BTC","eth_daily_tx":"ETH"}).rolling(7).mean()
            st.line_chart(b, height=260)
            st.caption("Fallback: local CSV (illustrative).")

    with tabs[2]:
        st.markdown("#### Remittance fee & speed — SWIFT vs crypto rails")
        amt = st.number_input("Transfer amount (USD)", min_value=100, step=100, value=1000, key="amt_remit")
        pick = st.selectbox("Corridor", df_fees["corridor"], key="corr_remit")
        row = df_fees[df_fees["corridor"] == pick].iloc[0]
        trad_cost = amt*(row["traditional_fee_pct"]/100); chain_cost = amt*(row["blockchain_fee_pct"]/100)
        trad_speed = row["traditional_speed_hours"]; chain_speed = row["crypto_speed_hours"]
        st.success(f"Traditional ≈ **${trad_cost:,.2f}** (~{trad_speed}h) | Crypto rail ≈ **${chain_cost:,.2f}** (~{chain_speed}h) → **Save ${trad_cost-chain_cost:,.2f}**")
        st.bar_chart(df_fees.set_index("corridor")[["traditional_fee_pct","blockchain_fee_pct"]])
        st.caption("Blockchain rails can compress end‑to‑end **cost** and **time**, notably on popular corridors.")

# ---------- Supply ----------
elif page == "₿ Supply":
    st.header("₿ Bitcoin supply — editable snapshot")
    max_supply = 21_000_000
    circ = st.number_input("Circulating supply (est., editable for demos)", min_value=0, max_value=max_supply, value=19_700_000, step=1000)
    remaining = max_supply - circ
    pct = (circ / max_supply) * 100 if max_supply else 0
    c1,c2,c3 = st.columns(3)
    c1.metric("Max supply", f"{max_supply:,} BTC")
    c2.metric("Circulating", f"{circ:,} BTC")
    c3.metric("% mined", f"{pct:.2f}%")
    st.caption("Hard cap of 21M BTC; halvings reduce issuance over time. Circulating value is editable for presentations.")

# ---------- Stablecoins & DeFi (LIVE caps) ----------
elif page == "💱 Stablecoins & DeFi":
    st.header("💱 Stablecoins & DeFi")
    st.image("assets/stablecoins.png", use_column_width=True)

    c1,c2 = st.columns(2)
    with c1:
        st.subheader("Stablecoin market caps (LIVE)")
        try:
            caps = fetch_stablecoin_caps().sort_values("market_cap", ascending=False)
        except Exception as e:
            st.warning("Live fetch failed or rate limited. Showing fallback snapshot.")
            caps = pd.read_csv(DATA_DIR / "stablecoin_caps_fallback.csv")
        st.bar_chart(caps.set_index(caps["symbol"])["market_cap"])
        st.caption("Source: CoinGecko API (fallback if unavailable).")

    with c2:
        st.subheader("DeFi TVL breakdown (USD bn, illustrative)")
        df_defi = load_csv("defi_tvl.csv")
        st.bar_chart(df_defi.set_index("category"))
        st.caption("DeFi replicates financial primitives (DEX, lending, staking) without traditional intermediaries.")

    st.markdown("### Discussion")
    st.markdown("- Stablecoin growth correlates with on-chain transfer volume and exchange liquidity.\n- DeFi TVL indicates capital parked in smart contracts across verticals.")

# ---------- Markets ----------
elif page == "📊 Markets":
    st.header("📊 Markets — Liquidity & Volatility")
    st.image("assets/markets.png", use_column_width=True)

    st.subheader("Rolling volatility (illustrative)")
    st.line_chart(df_vol.set_index("date"))
    st.caption("BTC shows higher realized volatility vs Gold/S&P500 — a key adoption constraint for payments, but less so for tokenized assets or stablecoins.")

    st.subheader("Market liquidity comparison (USD bn, illustrative)")
    st.line_chart(df_liq.set_index("date"))
    st.caption("Crypto liquidity is smaller than FX today; the takeaway is trajectory and use-case fit, not parity.")

# ---------- Energy ----------
elif page == "🌿 Energy":
    st.header("🌿 Energy & Sustainability")
    st.image("assets/energy.png", use_column_width=True)

    st.subheader("Annual electricity comparison (TWh/yr, illustrative)")
    st.bar_chart(df_energy.set_index("metric"))
    st.caption("Energy footprint is a regulatory focus area; estimates vary — pair this with latest research when publishing.")

    st.subheader("Mining energy mix (%, illustrative)")
    st.bar_chart(df_emix.set_index("source"))
    st.caption("Renewables share is increasing in certain regions; disclosure improves with public miners.")

# ---------- NFTs ----------
elif page == "🎨 NFTs":
    st.header("🎨 NFTs & New Assets")
    st.image("assets/nfts.png", use_column_width=True)

    st.subheader("NFT market by category (USD bn, illustrative)")
    st.bar_chart(df_nfts.set_index("category"))
    st.caption("NFTs demonstrate new forms of digital property rights, royalties, and programmable media.")

# ---------- Adoption Map ----------
elif page == "🌍 Adoption Map":
    st.header("🌍 Global blockchain adoption — CBDC pilots (sample)")
    st.image("assets/map.png", use_column_width=True)

    status_to_color = {
        "Live": [0, 200, 120],
        "Pilot": [255, 153, 0],
        "Preparation": [0, 122, 255],
        "Experimentation": [180, 180, 200]
    }
    df = df_cbdc_map.copy()
    df["color"] = df["status"].map(status_to_color)

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position='[lon, lat]',
        get_radius=1200000,
        get_fill_color="color",
        pickable=True
    )
    view_state = pdk.ViewState(latitude=20, longitude=10, zoom=1.2)
    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={"text":"{country}\nStatus: {status}"}))
    st.caption("Green=Live, Orange=Pilot, Blue=Preparation, Gray=Experimentation — illustrative only.")

# ---------- Regulation ----------
elif page == "📜 Regulation":
    st.header("📜 CBDCs & Regulation timeline")
    st.image("assets/regulation.png", use_column_width=True)

    st.subheader("Key milestones (illustrative)")
    st.dataframe(df_reg, use_container_width=True)
    st.caption("Combine with central bank sources for detailed policy tracking (e.g., scope of pilots, wholesale vs retail).")
