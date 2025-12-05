# ===========================================================
# File: findash_app_VN.py
# Đề tài: Financial Dashboard cho dữ liệu VN-INDEX 30
# ===========================================================

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# ===========================================================
# 1️⃣ Tải dữ liệu VN30 tự động (chung cho toàn bộ ứng dụng)
# ===========================================================

@st.cache_data(ttl=3600)
def load_vn30_data():
    vn30_tickers = [
        "FPT.VN", "HPG.VN", "MWG.VN", "VNM.VN", "VCB.VN", "SSI.VN",
        "TCB.VN", "MBB.VN", "CTG.VN", "GAS.VN", "VHM.VN", "BVH.VN",
        "VIC.VN", "PLX.VN", "STB.VN", "SAB.VN", "NVL.VN", "VPB.VN"
    ]
    data_list = []
    for tk in vn30_tickers:
        try:
            df = yf.download(tk, period="1y", progress=False)

# Làm phẳng cột nếu là MultiIndex
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            if not df.empty:
                df = df.reset_index()
                df["Ticker"] = tk.replace(".VN", "")
                data_list.append(df)

        except Exception as e:
            print(f"Lỗi tải {tk}: {e}")
    if data_list:
        return pd.concat(data_list)
    else:
        return pd.DataFrame()

# ===========================================================
# 2️⃣ Cấu trúc giao diện sidebar
# ===========================================================

st.sidebar.title("VN30 Financial Dashboard")
st.sidebar.write("Ứng dụng phân tích dữ liệu tài chính nhóm VN30")
data = load_vn30_data()

# ===============================
# ✅ Kiểm tra dữ liệu VN30 đã tải
# ===============================
if data.empty:
    st.error("❌ Không tải được dữ liệu. Kiểm tra kết nối mạng hoặc mã cổ phiếu.")
    st.stop()
else:
    num_tickers = data["Ticker"].nunique()
    num_rows = len(data)

tickers = sorted(data["Ticker"].unique())
ticker = st.sidebar.selectbox("Chọn mã cổ phiếu", tickers)

# ===========================================================
# 3️⃣ Khai báo các tab của ứng dụng
# ===========================================================

tab = st.sidebar.radio(
    "Chọn phần hiển thị:",
    ["Summary", "Chart", "Statistics", "Monte Carlo Simulation", "Portfolio Trend"]
)

# ===========================================================
# 4️⃣ TAB 1 - SUMMARY (Nguyễn Thị Hồng Thắm)
# ===========================================================

def tab_summary():
   # --- Tiêu đề chính căn giữa ---
    st.markdown(
        """
        <h1 style='text-align: center; color: #1a73e8;'>
            📊 Tab “Summary” – Tổng quan từng mã cổ phiếu VN30
        </h1>
        """,
        unsafe_allow_html=True
    )

    # --- 1️⃣ Lọc dữ liệu theo mã được chọn ---
    df_ticker = data[data["Ticker"] == ticker].copy()
    df_ticker = df_ticker.sort_values("Date")

    if df_ticker.empty:
        st.warning("⚠️ Không có dữ liệu cho mã cổ phiếu này.")
        return

    # --- Tiêu đề phụ thông báo mã đang hiển thị ---
    st.markdown(
        f"""
        <h3 style='text-align: center; color: #34a853;'>
            🔍 Đang hiển thị dữ liệu cổ phiếu: <b>{ticker}</b>
        </h3>
        """,
        unsafe_allow_html=True
    )

    # --- 2️⃣ Tính toán các chỉ số tổng quan ---
    df_ticker["Return"] = df_ticker["Close"].pct_change()
    latest_close = df_ticker["Close"].iloc[-1]                     # Giá đóng cửa gần nhất
    mean_30d = df_ticker["Close"].tail(30).mean()                  # Trung bình 30 ngày gần nhất
    std_return = df_ticker["Return"].std()                         # Độ lệch chuẩn lợi nhuận

    # --- 3️⃣ Hiển thị các chỉ tiêu cơ bản ---
    st.subheader("📈 Các chỉ tiêu cơ bản")
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Giá đóng cửa mới nhất", f"{latest_close:,.2f} VND")
    col2.metric("📆 Trung bình 30 ngày gần nhất", f"{mean_30d:,.2f} VND")
    col3.metric("📉 Độ lệch chuẩn lợi nhuận (σ)", f"{std_return:.2%}")

    st.markdown("""
    <div style="text-align: justify;">
    Các chỉ tiêu trên là <b>thước đo định lượng</b> quan trọng:
    <ul>
        <li>💰 <b>Giá đóng cửa mới nhất</b>: phản ánh giá trị hiện hành trên thị trường.</li>
        <li>📆 <b>Giá trung bình 30 ngày</b>: thể hiện xu hướng ngắn hạn.</li>
        <li>📉 <b>Độ lệch chuẩn lợi nhuận (σ)</b>: biểu thị mức độ biến động và rủi ro của cổ phiếu.</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

    # --- 4️⃣ Biểu đồ giá cổ phiếu ---
    st.subheader(f"📊 Diễn biến giá cổ phiếu {ticker} trong 1 năm gần đây")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_ticker["Date"],
        y=df_ticker["Close"],
        mode="lines",
        name="Giá đóng cửa",
        line=dict(color="#0077b6", width=2),
        fill="tozeroy",
        fillcolor="rgba(0, 119, 182, 0.25)"
    ))

    # Bộ chọn thời gian
    fig.update_xaxes(
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1M", step="month", stepmode="backward"),
                dict(count=3, label="3M", step="month", stepmode="backward"),
                dict(count=6, label="6M", step="month", stepmode="backward"),
                dict(count=1, label="1Y", step="year", stepmode="backward"),
                dict(step="all", label="MAX")
            ])
        ),
        rangeslider=dict(visible=False),
        type="date"
    )

    # Tùy chỉnh giao diện
    fig.update_layout(
        title=f"Biểu đồ biến động giá cổ phiếu {ticker}",
        xaxis_title="Thời gian",
        yaxis_title="Giá đóng cửa (VND)",
        template="plotly_white",
        hovermode="x unified",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=60, b=30)
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})

    # --- 5️⃣ Bảng dữ liệu 100 ngày gần nhất ---
    st.subheader("📋 Bảng dữ liệu 100 ngày gần nhất")
    df_recent = df_ticker.tail(100)[["Date", "Open", "High", "Low", "Close", "Volume"]]
    st.dataframe(
        df_recent.style.format({
            "Open": "{:,.2f}",
            "High": "{:,.2f}",
            "Low": "{:,.2f}",
            "Close": "{:,.2f}",
            "Volume": "{:,.0f}"
        }),
        use_container_width=True,
        height=350
    )
# ===========================================================
# 5️⃣ TAB 2 - CHART (Phan Văn Thảo)
# ===========================================================
def tab_chart():
    st.title("📈 Phân tích biểu đồ kỹ thuật nâng cao")

    df_ticker = data[data["Ticker"] == ticker].copy()
    df_ticker["Date"] = pd.to_datetime(df_ticker["Date"])
    df_ticker.sort_values("Date", inplace=True)

    # Tính SMA 50 và SMA 200 trên toàn bộ dữ liệu
    df_ticker["SMA_50"] = df_ticker["Close"].rolling(window=50).mean()
    df_ticker["SMA_200"] = df_ticker["Close"].rolling(window=200).mean()

    # Bộ lọc thời gian
    min_date = df_ticker["Date"].min().date()
    max_date = df_ticker["Date"].max().date()

    col1, col2 = st.columns(2)
    from_date = col1.date_input("📅 Ngày bắt đầu", min_value=min_date, max_value=max_date, value=min_date)
    to_date = col2.date_input("📅 Ngày kết thúc", min_value=min_date, max_value=max_date, value=max_date)

    duration = st.selectbox("⏱️ Chọn thời hạn", ["Tùy chọn", "YTD", "6M", "1Y"])
    today = datetime.now().date()

    if duration == "YTD":
        from_date = datetime(today.year, 1, 1).date()
    elif duration == "6M":
        from_date = today - timedelta(days=180)
    elif duration == "1Y":
        from_date = today - timedelta(days=365)

    from_date = pd.to_datetime(from_date)
    to_date = pd.to_datetime(to_date)

    if from_date > to_date:
        st.error("❌ Ngày bắt đầu phải nhỏ hơn hoặc bằng ngày kết thúc.")
        st.stop()

    interval = st.selectbox("📊 Khoảng thời gian", ["Hằng ngày", "Hằng tuần", "Hằng tháng"])
    plot_type = st.selectbox("📈 Loại biểu đồ", ["Đường", "Nến", "Vùng"])

    # Lọc dữ liệu theo thời gian
    df_filtered = df_ticker[(df_ticker["Date"] >= from_date) & (df_ticker["Date"] <= to_date)].copy()

    # Resample nếu cần
    if interval == "Hằng tuần":
        df_plot = df_filtered.set_index("Date").resample("W").agg({
            "Open": "first", "High": "max", "Low": "min", "Close": "last",
            "Volume": "sum"
        }).dropna().reset_index()
        df_sma = df_ticker.set_index("Date").resample("W").agg({"SMA_50": "last"}).dropna().reset_index()
    elif interval == "Hằng tháng":
        df_plot = df_filtered.set_index("Date").resample("M").agg({
            "Open": "first", "High": "max", "Low": "min", "Close": "last",
            "Volume": "sum"
        }).dropna().reset_index()
        df_sma = df_ticker.set_index("Date").resample("M").agg({"SMA_50": "last"}).dropna().reset_index()
    else:
        df_plot = df_filtered.copy()
        df_sma = df_ticker[["Date", "SMA_50"]].copy()

    # Biểu đồ chính
    fig = go.Figure()
    hover_text = df_plot.apply(lambda row: f"Ngày: {row['Date'].date()}<br>Open: {row['Open']}<br>High: {row['High']}<br>Low: {row['Low']}<br>Close: {row['Close']}<br>Volume: {row['Volume']}", axis=1)

    if plot_type == "Nến":
        fig.add_trace(go.Candlestick(
            x=df_plot["Date"],
            open=df_plot["Open"],
            high=df_plot["High"],
            low=df_plot["Low"],
            close=df_plot["Close"],
            name="Giá nến",
            hovertext=hover_text,
            hoverinfo="text"
        ))
    elif plot_type == "Vùng":
        fig.add_trace(go.Scatter(
            x=df_plot["Date"], y=df_plot["Close"], fill="tozeroy", mode="lines", name="Close",
            hovertext=hover_text,
            hoverinfo="text"
        ))
    else:
        fig.add_trace(go.Scatter(
            x=df_plot["Date"], y=df_plot["Close"], mode="lines", name="Close",
            hovertext=hover_text,
            hoverinfo="text"
        ))

    # SMA 50 toàn biểu đồ
    fig.add_trace(go.Scatter(
        x=df_sma["Date"], y=df_sma["SMA_50"], mode="lines", name="SMA 50", line=dict(color="red"),
        hovertemplate="SMA 50: %{y}<br>Ngày: %{x}"
    ))

    # Volume
    fig.add_trace(go.Bar(
        x=df_plot["Date"],
        y=df_plot["Volume"],
        name="Khối lượng",
        yaxis="y2",
        marker_color="green",
        hovertemplate="Volume: %{y}<br>Ngày: %{x}"
    ))

    fig.update_layout(
        title=f"Biểu đồ kỹ thuật của {ticker}",
        xaxis_title="Ngày",
        yaxis_title="Giá",
        yaxis2=dict(title="Khối lượng", overlaying="y", side="right", showgrid=False),
        xaxis_rangeslider_visible=False,
        height=600,
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)

    # Biểu đồ thứ hai: toàn bộ dữ liệu với SMA 200
    st.subheader("📉 Biểu đồ nến & SMA 200 ngày")

    df_candle = df_ticker.copy()

    fig2 = go.Figure()

    fig2.add_trace(go.Candlestick(
        x=df_candle["Date"],
        open=df_candle["Open"],
        high=df_candle["High"],
        low=df_candle["Low"],
        close=df_candle["Close"],
        name="Giá nến",
        increasing_line_color="green",
        decreasing_line_color="red"
    ))

    fig2.add_trace(go.Scatter(
        x=df_candle["Date"],
        y=df_candle["SMA_200"],
        mode="lines",
        line=dict(color="orange", width=2),
        name="SMA 200 ngày"
    ))

    fig2.add_trace(go.Bar(
        x=df_candle["Date"],
        y=df_candle["Volume"],
        name="Khối lượng",
        marker_color="rgb(119,220,197)",
        yaxis="y2"
    ))

    fig2.update_layout(
        xaxis_title="Ngày",
        yaxis=dict(title="Giá", side="left"),
        yaxis2=dict(title="Khối lượng", overlaying="y", side="right", showgrid=False),
        xaxis_rangeslider_visible=False,
        height=600,
        hovermode="x unified"
    )

    st.plotly_chart(fig2, use_container_width=True)

# ===========================================================
# 6️⃣ TAB 3 - STATISTICS (Nguyễn Hoàng Thiên Bảo)
# ===========================================================

def tab_statistics():
    # --- Tiêu đề tab ---
    st.markdown("""
        <h1 style='text-align: center; color: #1a73e8;'>
        Phân tích thống kê & rủi ro cổ phiếu
        </h1>
    """, unsafe_allow_html=True)

    # --- Lọc dữ liệu theo mã cổ phiếu được chọn ---
    df_ticker = data[data["Ticker"] == ticker].copy()
    if df_ticker.empty:
        st.warning("⚠️ Không có dữ liệu cho mã cổ phiếu này.")
        return

    # --- Tính tỷ suất lợi nhuận hàng ngày ---
    df_ticker["Lợi_nhuận"] = df_ticker["Close"].pct_change()
    df_ticker.dropna(inplace=True)

    # --- Thêm cột Tháng & Quý (1 lần duy nhất) ---
    df_ticker["Tháng"] = df_ticker["Date"].dt.to_period("M")
    df_ticker["Quý"] = df_ticker["Date"].dt.to_period("Q")

    # --- Bảng mô tả thống kê cơ bản ---
    st.subheader("📋 Bảng mô tả thống kê cơ bản")
    stats_df = df_ticker["Lợi_nhuận"].describe().to_frame()
    stats_df.loc["Độ lệch (Skew)"] = df_ticker["Lợi_nhuận"].skew()
    stats_df.loc["Độ nhọn (Kurtosis)"] = df_ticker["Lợi_nhuận"].kurt()
    sharpe_ratio = df_ticker["Lợi_nhuận"].mean() / df_ticker["Lợi_nhuận"].std()
    stats_df.loc["Chỉ số Sharpe (Lợi nhuận theo rủi ro)"] = sharpe_ratio

    # Hiển thị bảng
    st.dataframe(
        stats_df.style.format("{:.4f}").set_table_styles(
            [{'selector': 'th', 'props': [('text-align', 'left')]}]
        ),
        use_container_width=True,
        height=400
    )

    # --- Boxplot lợi nhuận ---
    fig_box = px.box(
        df_ticker, y="Lợi_nhuận",
        color_discrete_sequence=["#ff6361"],
        title=f"Boxplot lợi nhuận cổ phiếu {ticker}",
        labels={"Lợi_nhuận": "Tỷ suất lợi nhuận hàng ngày"}
    )
    fig_box.update_layout(template="plotly_white")
    st.plotly_chart(fig_box, use_container_width=True)

    # --- Giải thích ý nghĩa ---
    st.markdown("""
    <div style="text-align: justify;">
    <b>💡 Nhận xét:</b>
    <ul>
        <li><b>Mean</b>: Lợi nhuận trung bình mỗi ngày (cao là tốt).</li>
        <li><b>Std</b>: Độ biến động lợi nhuận (cao là rủi ro cao).</li>
        <li><b>Min / Max</b>: Biên độ dao động cực trị.</li>
        <li><b>Skew</b>: Độ lệch phân phối (âm = dễ giảm mạnh, dương = dễ tăng mạnh).</li>
        <li><b>Kurtosis</b>: Độ nhọn, thể hiện mức độ xuất hiện của biến động cực đoan.</li>
        <li><b>Sharpe Ratio</b>: Đo hiệu quả lợi nhuận so với rủi ro (càng lớn càng tốt).</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

    # --- Histogram lợi nhuận ---
    st.subheader("📊 Phân phối tỷ suất lợi nhuận (Rủi ro biến động)")
    fig_hist = px.histogram(
        df_ticker, x="Lợi_nhuận", nbins=40,
        color_discrete_sequence=["#1a73e8"],
        title=f"Phân phối lợi nhuận cổ phiếu {ticker}",
        labels={"Lợi_nhuận": "Tỷ suất lợi nhuận hàng ngày", "count": "Số ngày"}
    )
    fig_hist.update_layout(template="plotly_white")
    st.plotly_chart(fig_hist, use_container_width=True)


    # --- Lợi nhuận trung bình theo Tháng & Quý ---
    st.subheader("📊 Lợi nhuận trung bình theo Tháng và Quý")

    # Theo Tháng
    monthly_ret = df_ticker.groupby("Tháng")["Lợi_nhuận"].mean().reset_index()
    monthly_ret["Tháng"] = monthly_ret["Tháng"].astype(str)
    fig_month = px.bar(
        monthly_ret, x="Tháng", y="Lợi_nhuận",
        title="Lợi nhuận trung bình theo Tháng",
        text_auto=".2%", color_discrete_sequence=["#003f5c"],
        labels={"Tháng": "Tháng (YYYY-MM)", "Lợi_nhuận": "Tỷ suất lợi nhuận trung bình"}
    )
    fig_month.update_layout(xaxis=dict(tickangle=-45, automargin=True), yaxis=dict(automargin=True), template="plotly_white")
    fig_month.update_traces(textposition='outside', cliponaxis=False)
    st.plotly_chart(fig_month, use_container_width=True)

    # Theo Quý
    quarterly_ret = df_ticker.groupby("Quý")["Lợi_nhuận"].mean().reset_index()
    quarterly_ret["Quý"] = quarterly_ret["Quý"].astype(str)
    fig_quarter = px.bar(
        quarterly_ret, x="Quý", y="Lợi_nhuận",
        title="Lợi nhuận trung bình theo Quý",
        text_auto=".2%", color_discrete_sequence=["#58508d"],
        labels={"Quý": "Quý (YYYYQ)", "Lợi_nhuận": "Tỷ suất lợi nhuận trung bình"}
    )
    fig_quarter.update_layout(xaxis_tickangle=0, template="plotly_white")
    st.plotly_chart(fig_quarter, use_container_width=True)


    # --- Sharpe Ratio theo Tháng và Quý (dạng %) ---
    st.subheader("📊 Sharpe Ratio theo Tháng và Quý")

    # Theo Tháng
    monthly_stats = df_ticker.groupby("Tháng")["Lợi_nhuận"].agg(['mean', 'std']).reset_index()
    monthly_stats["Sharpe"] = (monthly_stats["mean"] / monthly_stats["std"]) * 100
    monthly_stats["Tháng"] = monthly_stats["Tháng"].astype(str)
    fig_sharpe_month = px.bar(
        monthly_stats,
        x="Tháng",
        y="Sharpe",
        text=monthly_stats["Sharpe"].map("{:.2f}%".format),
        color_discrete_sequence=["#ff7f0e"],
        title=f"Sharpe Ratio theo Tháng của {ticker}",
        labels={"Sharpe": "Sharpe Ratio (%)", "Tháng": "Tháng (YYYY-MM)"}
    )
    fig_sharpe_month.update_layout(xaxis=dict(tickangle=-45, automargin=True), yaxis=dict(automargin=True), template="plotly_white")
    fig_sharpe_month.update_traces(textposition='outside', cliponaxis=False)
    st.plotly_chart(fig_sharpe_month, use_container_width=True)

    # Theo Quý
    quarterly_stats = df_ticker.groupby("Quý")["Lợi_nhuận"].agg(['mean', 'std']).reset_index()
    quarterly_stats["Sharpe"] = (quarterly_stats["mean"] / quarterly_stats["std"]) * 100
    quarterly_stats["Quý"] = quarterly_stats["Quý"].astype(str)
    fig_sharpe_quarter = px.bar(
        quarterly_stats,
        x="Quý",
        y="Sharpe",
        text=quarterly_stats["Sharpe"].map("{:.2f}%".format),
        color_discrete_sequence=["#ffa600"],
        title=f"Sharpe Ratio theo Quý của {ticker}",
        labels={"Sharpe": "Sharpe Ratio (%)", "Quý": "Quý (YYYYQ)"}
    )
    fig_sharpe_quarter.update_layout(xaxis=dict(tickangle=0, automargin=True), yaxis=dict(automargin=True), template="plotly_white")
    fig_sharpe_quarter.update_traces(textposition='outside', cliponaxis=False)
    st.plotly_chart(fig_sharpe_quarter, use_container_width=True)

# ===========================================================
# 7️⃣ TAB 4 - MONTE CARLO SIMULATION (Phan Văn Thảo)
# ===========================================================

def tab_montecarlo():
    import matplotlib.pyplot as plt

    st.title("🎲 Mô phỏng Monte Carlo")

    # Lấy dữ liệu và tính toán
    df_ticker = data[data["Ticker"] == ticker].copy()
    df_ticker["Return"] = df_ticker["Close"].pct_change()
    df_ticker.dropna(inplace=True)

    daily_vol = df_ticker["Return"].std()
    last_price = df_ticker["Close"].iloc[-1]

    # Giao diện người dùng
    col1, col2 = st.columns(2)
    n_sim = col1.slider("🔁 Số lần mô phỏng", 200, 2000, 500)
    t_horizon = col2.slider("⏳ Số ngày dự báo", 30, 365, 180)

    # Cho phép chọn số đường hiển thị
    n_display = st.slider("👁️ Số đường mô phỏng hiển thị", 50, n_sim, min(300, n_sim))

    # Mô phỏng Monte Carlo
    np.random.seed(42)
    simulations = []
    for _ in range(n_sim):
        price_series = [last_price]
        for _ in range(t_horizon):
            price_series.append(price_series[-1] * (1 + np.random.normal(0, daily_vol)))
        simulations.append(price_series)

    simulation_df = pd.DataFrame(simulations).T
    x_values = list(range(t_horizon + 1))

    # Biểu đồ quạt (Fan Chart)
    fig = go.Figure()
    cmap = plt.cm.get_cmap("tab20", n_display)

    for idx in range(n_display):
        r, g, b = [int(c * 255) for c in cmap(idx)[:3]]
        fig.add_trace(go.Scatter(
            x=x_values,
            y=simulation_df[idx],
            mode="lines",
            line=dict(width=2.5, color=f"rgba({r},{g},{b},0.5)"),
            showlegend=False
        ))

    # Đường kỳ vọng trung bình
    mean_path = simulation_df.mean(axis=1)
    fig.add_trace(go.Scatter(
        x=x_values,
        y=mean_path,
        mode="lines",
        line=dict(color="red", width=2),
        name="Kỳ vọng trung bình"
    ))

    fig.update_layout(
        title=f"📉 Mô phỏng Monte Carlo cho {ticker}",
        xaxis_title="Ngày mô phỏng",
        yaxis_title="Giá dự báo",
        height=600,
        width=1400  # 👈 biểu đồ dài hơn
    )
    st.plotly_chart(fig)

    # Thống kê xác suất
    final_prices = simulation_df.iloc[-1]
    prob_up = (final_prices > last_price).mean() * 100

    st.subheader("📊 Kết quả thống kê")
    st.write(f"💰 **Giá hiện tại:** {last_price:.2f}")
    st.write(f"📈 **Xác suất giá tăng sau {t_horizon} ngày:** `{prob_up:.2f}%`")
    st.write(f"📉 **Xác suất giá giảm:** `{100 - prob_up:.2f}%`")

    # Phân phối giá cuối kỳ
    fig2 = px.histogram(final_prices, nbins=50, title="📦 Phân phối giá cuối kỳ")
    fig2.update_layout(xaxis_title="Giá kết thúc", yaxis_title="Tần suất", height=500, width=1000)
    st.plotly_chart(fig2)

# ===========================================================
# 8️⃣ TAB 5 - PORTFOLIO TREND (Nguyễn Hoàng Thiên Bảo)
# ===========================================================
def tab_portfolio():
    st.markdown("""
        <h1 style='text-align: center; color: #1a73e8;'>
            📊 So sánh xu hướng
        </h1>
    """, unsafe_allow_html=True)

    # --- Chọn cổ phiếu để so sánh ---
    selected = st.multiselect(
        "📌 Chọn cổ phiếu để so sánh xu hướng", 
        tickers, 
        default=["FPT", "VNM", "VCB", "HPG", "SSI", "MWG"]
    )

    if not selected:
        st.warning("⚠️ Vui lòng chọn ít nhất một mã cổ phiếu.")
        return

    df_port = data[data["Ticker"].isin(selected)].copy()
    df_port = df_port.sort_values(["Ticker", "Date"])

    # --- Biểu đồ 1: Biến động giá chuẩn hóa (%) ---
    df_port["Norm_Close"] = df_port.groupby("Ticker")["Close"].transform(lambda x: x / x.iloc[0] * 100)
    df_port["Tooltip_Norm"] = df_port.apply(
        lambda row: f"{row['Ticker']}<br>Ngày: {row['Date'].strftime('%Y-%m-%d')}<br>Giá: {row['Close']:,.0f} VND<br>Tỷ lệ: {row['Norm_Close']:.2f}%", axis=1
    )

    st.subheader("📈 Biểu đồ Biến động giá chuẩn hóa (%)")
    fig1 = px.line(
        df_port,
        x="Date",
        y="Norm_Close",
        color="Ticker",
        labels={"Date": "Thời gian", "Norm_Close": "Biến động giá (%)", "Close": "Giá (VND)"},
        hover_data={
            "Ticker": True,
            "Date": True,
            "Close": ":,.0f",
            "Norm_Close": ":.2f"
        }
    )
    fig1.update_layout(template="plotly_white", hovermode="x unified")
    st.plotly_chart(fig1, use_container_width=True)


    # --- Biểu đồ 2: Giá thực tế (VND) ---
    df_port["Tooltip_Value"] = df_port.apply(
        lambda row: f"{row['Ticker']}<br>Ngày: {row['Date'].strftime('%Y-%m-%d')}<br>Giá: {row['Close']:,.0f} VND", axis=1
    )

    st.subheader("📈 Biểu đồ Giá thực tế (VND)")
    fig2 = px.line(
        df_port,
        x="Date",
        y="Close",
        color="Ticker",
        labels={"Date": "Thời gian", "Close": "Giá (VND)"},
        hover_data={
            "Ticker": True,
            "Date": True,
            "Close": ":,.0f"
        }
    )
    fig2.update_layout(template="plotly_white", hovermode="x unified")
    st.plotly_chart(fig2, use_container_width=True)

# ===========================================================
# 9️⃣ Chạy ứng dụng chính
# ===========================================================

if tab == "Summary":
    tab_summary()
elif tab == "Chart":
    tab_chart()
elif tab == "Statistics":
    tab_statistics()
elif tab == "Monte Carlo Simulation":
    tab_montecarlo()
elif tab == "Portfolio Trend":
    tab_portfolio()
