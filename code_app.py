import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import time

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="Hệ thống Cảnh báo Rủi ro Tài chính", layout="wide")

# --- GIAO DIỆN HIỆN ĐẠI (CSS) ---
st.markdown("""
    <style>
    .stMetric {
        background: linear-gradient(135deg, #ffffff 0%, #f0f2f6 100%);
        border-radius: 15px;
        padding: 20px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .insight-box {
        background-color: #f8f9fa;
        border-left: 5px solid #2e7d32;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0px;
    }
    .ticker-wrap {
        width: 100%; overflow: hidden; background-color: #1a1a1a; 
        padding: 8px 0; border-radius: 5px; margin-bottom: 20px;
    }
    .ticker {
        display: inline-block; white-space: nowrap; animation: ticker 50s linear infinite;
        font-weight: bold; color: #00ff00; font-family: 'Courier New', monospace;
    }
    @keyframes ticker { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }

    /* CSS cho Chatbot đẹp hơn */
    .chat-metric-box {
        padding: 10px; border-radius: 8px; border: 1px solid #eee; background: white; margin-bottom: 10px;
    }

    /* Tùy chỉnh tiêu đề chính cho đẹp hơn */
    .main-title {
        font-size: 2.2em;
        font-weight: 700;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 20px;
        text-transform: uppercase;
    }
    </style>
    """, unsafe_allow_html=True)


# 2. HÀM LOAD DATA
@st.cache_data
def load_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # LƯU Ý: Đảm bảo tên file CSV khớp với file bạn đã xuất ra
    file_name = "ket_qua_du_bao.csv"
    file_path = os.path.join(current_dir, file_name)
    try:
        if os.path.exists(file_path):
            df = pd.read_csv(file_path, encoding='utf-8-sig')
            df.columns = df.columns.str.strip()
            if 'ten_cong_ty' in df.columns:
                df.loc[df['ma_ck'] == 'VNM', 'ten_cong_ty'] = 'CTCP Sữa Việt Nam (Vinamilk)'
            mapping = {
                'ma_ck': 'Mã doanh nghiệp', 'ten_cong_ty': 'Tên công ty',
                'nganh': 'Ngành nghề', 'ngay': 'Ngày báo cáo',
                'diem_tin_dung': 'Điểm rủi ro', 'trang_thai': 'Trạng thái'
            }
            df = df.rename(columns=mapping)
            if 'Ngày báo cáo' in df.columns:
                df['Ngày báo cáo'] = pd.to_datetime(df['Ngày báo cáo'], errors='coerce')
                df['Năm'] = df['Ngày báo cáo'].dt.year
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Lỗi: {e}")
        return pd.DataFrame()


df = load_data()

# 3. GIAO DIỆN VÀ BỘ LỌC
if not df.empty:
    st.sidebar.title("🛡️ RISK MGMT PRO")
    menu = st.sidebar.radio("Chọn chức năng:", [
        "📊 Tổng quan & Xu hướng",
        "🎯 Phân tích Chiến lược",
        "🧭 Cẩm nang Nhà đầu tư",
        "🔮 Trình mô phỏng Dự báo",
        "🤖 AI Assistant (Chatbot)"
    ])

    st.sidebar.markdown("---")
    col_nganh = 'Ngành nghề';
    col_ma = 'Mã doanh nghiệp';
    col_diem = 'Điểm rủi ro'

    # --- BỘ LỌC NGÀNH ---
    list_nganh = sorted(df[col_nganh].unique().astype(str))
    sel_ind = st.sidebar.multiselect("Ngành nghề:", list_nganh, default=list_nganh)
    df_f = df[df[col_nganh].isin(sel_ind)]

    # --- BỘ LỌC MÃ CHỨNG KHOÁN ---
    full_list_ma = sorted(df[col_ma].unique().astype(str))
    list_ma_f = sorted(df_f[col_ma].unique().astype(str))

    # Mặc định chọn 5 mã đầu tiên để hiển thị cho đỡ rối
    default_ma = list_ma_f[:5] if len(list_ma_f) >= 5 else list_ma_f
    sel_ma = st.sidebar.multiselect("Mã chứng khoán:", list_ma_f, default=default_ma)
    df_f = df_f[df_f[col_ma].isin(sel_ma)]

    # === [MỚI] BỘ LỌC THỜI GIAN (NĂM) ===
    if 'Năm' in df.columns and not df['Năm'].isnull().all():
        min_year = int(df['Năm'].min())
        max_year = int(df['Năm'].max())

        st.sidebar.markdown("---")
        selected_years = st.sidebar.slider(
            "⏳ Chọn giai đoạn (Năm):",
            min_value=min_year,
            max_value=max_year,
            value=(min_year, max_year)  # Mặc định chọn từ đầu đến cuối
        )

        # Áp dụng lọc thời gian vào df_f
        df_f = df_f[
            (df_f['Năm'] >= selected_years[0]) &
            (df_f['Năm'] <= selected_years[1])
            ]
    # ====================================

    # --- TICKER (Dựa trên dữ liệu sau khi lọc) ---
    danger_list = df_f[df_f[col_diem] > 70][col_ma].unique()
    ticker_text = "  |  ".join([f"🔴 CẢNH BÁO: {m}" for m in danger_list]) if len(
        danger_list) > 0 else "🟢 DANH MỤC ĐANG THEO DÕI ỔN ĐỊNH"
    st.markdown(f'<div class="ticker-wrap"><div class="ticker">{ticker_text}</div></div>', unsafe_allow_html=True)

    # --- TRANG 1: TỔNG QUAN ---
    if menu == "📊 Tổng quan & Xu hướng":
        st.markdown(
            '<div class="main-title">PHÂN TÍCH VÀ ỨNG DỤNG HỌC MÁY TRONG CẢNH BÁO SỚM RỦI RO TÀI CHÍNH<br><span style="font-size:0.6em; color:#555;">CÁC DOANH NGHIỆP PHI TÀI CHÍNH NIÊM YẾT TẠI VIỆT NAM</span></div>',
            unsafe_allow_html=True)

        if df_f.empty:
            st.warning("⚠️ Không có dữ liệu trong khoảng thời gian hoặc mã chứng khoán bạn chọn.")
        else:
            # Biểu đồ Line
            st.plotly_chart(px.line(df_f, x="Năm", y=col_diem, color=col_ma, markers=True,
                                    title="Biến động điểm rủi ro qua các kỳ báo cáo", template="plotly_white"),
                            use_container_width=True)

            # Heatmap
            st.markdown("### 🌡️ Heatmap Rủi ro Doanh nghiệp (Đỏ: Cao - Xanh: Thấp)")
            heatmap_data = df_f.pivot_table(index=col_ma, columns='Năm', values=col_diem, aggfunc='mean')
            if not heatmap_data.empty:
                st.plotly_chart(px.imshow(heatmap_data, text_auto=".1f", color_continuous_scale='RdYlGn_r'),
                                use_container_width=True)

    # --- TRANG 2: CHIẾN LƯỢC ---
    elif menu == "🎯 Phân tích Chiến lược":
        st.title("🎯 Phân Tích Chiến Lược & Ngành")

        if df_f.empty:
            st.warning("⚠️ Vui lòng mở rộng khoảng thời gian hoặc chọn thêm mã chứng khoán.")
        else:
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Số DN", len(df_f[col_ma].unique()))
            with c2:
                st.metric("Rủi ro TB", f"{df_f[col_diem].mean():.2f}")
            with c3:
                st.metric("Báo động", len(df_f[df_f[col_diem] > 50][col_ma].unique()), delta="⚠️")
            with c4:
                st.metric("Độ ổn định", f"{df_f[col_diem].std():.2f}")

            col_l, col_r = st.columns([2, 1])
            with col_l:
                st.plotly_chart(px.bar(df_f.groupby(col_nganh)[col_diem].mean().reset_index().sort_values(col_diem),
                                       x=col_diem, y=col_nganh, orientation='h', color=col_diem,
                                       color_continuous_scale='Reds'), use_container_width=True)
            with col_r:
                fig_pie = px.pie(df_f, names='Trạng thái', hole=0.6,
                                 color='Trạng thái',
                                 color_discrete_map={
                                     'AN TOÀN XANH': '#008000',
                                     'CẢNH BÁO VÀNG': '#FFFF00',
                                     'BÁO ĐỘNG ĐỎ': '#FF0000'
                                 })
                st.plotly_chart(fig_pie, use_container_width=True)

            st.markdown("### 🏆 Bảng xếp hạng Rủi ro (Trong giai đoạn đã chọn)")
            rk1, rk2 = st.columns(2)
            # Lấy trung bình điểm rủi ro của từng mã trong giai đoạn được chọn để xếp hạng
            ranking_df = df_f.groupby([col_ma, 'Trạng thái'])[col_diem].mean().reset_index()

            with rk1:
                st.write("🔴 **Top 5 Rủi ro cao nhất:**")
                st.dataframe(ranking_df.sort_values(by=col_diem, ascending=False).head(5),
                             hide_index=True)
            with rk2:
                st.write("🟢 **Top 5 An toàn nhất:**")
                st.dataframe(ranking_df.sort_values(by=col_diem, ascending=True).head(5),
                             hide_index=True)

    # --- TRANG 3: CẨM NANG ---
    elif menu == "🧭 Cẩm nang Nhà đầu tư":
        st.title("🧭 Phân Tích Chuyên Sâu & Radar")

        if df_f.empty:
            st.warning("⚠️ Không đủ dữ liệu để vẽ biểu đồ.")
        else:
            st.plotly_chart(px.sunburst(df_f, path=[col_nganh, col_ma], values=col_diem, color=col_diem,
                                        color_continuous_scale='RdYlGn_r'), use_container_width=True)

            st.markdown("---")
            # Chọn mã từ danh sách ĐÃ LỌC
            available_tickers = df_f[col_ma].unique()
            if len(available_tickers) > 0:
                ticker_radar = st.selectbox("Chọn mã doanh nghiệp:", available_tickers)

                # Lấy dữ liệu mới nhất TRONG KHOẢNG THỜI GIAN ĐÃ CHỌN
                latest = df_f[df_f[col_ma] == ticker_radar].sort_values('Năm').iloc[-1]

                color_map = {'AN TOÀN XANH': 'rgba(46, 204, 113, 0.5)', 'CẢNH BÁO VÀNG': 'rgba(241, 196, 15, 0.5)',
                             'BÁO ĐỘNG ĐỎ': 'rgba(231, 76, 60, 0.5)'}
                line_map = {'AN TOÀN XANH': '#27ae60', 'CẢNH BÁO VÀNG': '#f39c12', 'BÁO ĐỘNG ĐỎ': '#c0392b'}
                current_color = color_map.get(latest['Trạng thái'], 'rgba(100, 100, 100, 0.5)')
                current_line = line_map.get(latest['Trạng thái'], '#7f8c8d')

                # === PHẦN RADAR ===
                score_safe = 100 - latest[col_diem]
                val_liq = latest.get('tt_hien_han_tre1', 0)
                score_liq = min(100, val_liq * 50)
                val_lev = latest.get('no_tong_tai_san_tre1', 0.5)
                score_lev = max(0, min(100, (1 - val_lev) * 100))
                val_prof = latest.get('roa_tre1', 0)
                score_prof = max(0, min(100, val_prof * 500))
                val_cash = latest.get('dong_tien_tren_no_tre1', 0)
                if val_cash > 0.5:
                    score_cash = 100
                elif val_cash > 0:
                    score_cash = 70
                elif val_cash == 0:
                    score_cash = 50
                else:
                    score_cash = 20

                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(
                    r=[score_safe, score_liq, score_lev, score_prof, score_cash],
                    theta=['Độ An toàn (100-Risk)', 'Thanh khoản', 'Cấu trúc Vốn (Ít nợ)', 'Sinh lời (ROA)',
                           'Dòng tiền'],
                    fill='toself', fillcolor=current_color, line=dict(color=current_line), name=ticker_radar
                ))
                fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                                        title=f"Sức khỏe tài chính đa chiều: {ticker_radar} (Năm {latest['Năm']})")
                st.plotly_chart(fig_radar, use_container_width=True)

                st.markdown(
                    f"""<div class='insight-box'><b>🤖 AI Review chuyên sâu:</b> Mã {ticker_radar} ({latest['Tên công ty']}) hiện có mức rủi ro đạt <b>{latest[col_diem]:.2f}</b> điểm (Năm {latest['Năm']}). 
                Mức điểm này phản ánh trạng thái <b>{latest['Trạng thái']}</b> của doanh nghiệp trong kỳ báo cáo được chọn. 
                {'⚠️ Khuyến nghị: Doanh nghiệp đang gặp áp lực lớn về tài chính, nhà đầu tư cần rà soát lại cơ cấu nợ và dòng tiền hoạt động.' if latest[col_diem] > 60 else '✅ Phân tích: Các chỉ số vận hành đang nằm trong tầm kiểm soát tốt, đây là vùng an toàn để nắm giữ lâu dài.'}</div>""",
                    unsafe_allow_html=True)
            else:
                st.info("Vui lòng chọn mã chứng khoán bên thanh menu.")

    # --- TRANG 4: MÔ PHỎNG ---
    elif menu == "🔮 Trình mô phỏng Dự báo":
        st.title("🔮 Stress-Test Kịch Bản")

        # Chỉ lấy các mã có trong danh sách đã lọc
        available_tickers = df_f[col_ma].unique()

        if len(available_tickers) > 0:
            col_in, col_ch = st.columns([1, 2])
            with col_in:
                target_ma = st.selectbox("Chọn mã giả lập:", available_tickers)
                s_roa = st.slider("Lợi nhuận thay đổi (%)", -10.0, 10.0, 0.0)
                s_debt = st.slider("Nợ thay đổi (%)", -20.0, 20.0, 0.0)

                # Lấy base là năm GẦN NHẤT trong khoảng thời gian đã chọn
                base = df_f[df_f[col_ma] == target_ma].sort_values('Năm').iloc[-1][col_diem]
                sim_score = max(0, min(100, base - (s_roa * 2) + (s_debt * 0.8)))

            with col_ch:
                st.plotly_chart(
                    go.Figure(go.Indicator(mode="gauge+number+delta", value=sim_score, delta={'reference': base},
                                           gauge={'axis': {'range': [0, 100]},
                                                  'steps': [{'range': [0, 30], 'color': "green"},
                                                            {'range': [70, 100], 'color': "red"}]})),
                    use_container_width=True)

            st.write(
                f"**So sánh Điểm Gốc (Năm {df_f[df_f[col_ma] == target_ma].sort_values('Năm').iloc[-1]['Năm']}) và Dự báo:**")
            fig_bullet = go.Figure(
                go.Bar(name='Hiện tại', y=[target_ma], x=[base], orientation='h', marker_color='#95a5a6'))
            fig_bullet.add_trace(
                go.Bar(name='Dự báo', y=[target_ma], x=[sim_score], orientation='h', marker_color='#e74c3c'))
            fig_bullet.update_layout(barmode='group', height=200)
            st.plotly_chart(fig_bullet, use_container_width=True)
        else:
            st.warning("Không có mã chứng khoán nào để mô phỏng. Vui lòng kiểm tra bộ lọc.")

    # --- TRANG 5: CHATBOT (AI ASSISTANT) ---
    elif menu == "🤖 AI Assistant (Chatbot)":
        st.title("🤖 Trợ lý Tài chính Thông minh (AI Analyst)")

        # Khởi tạo lịch sử chat
        if "messages" not in st.session_state:
            st.session_state.messages = [
                {"role": "assistant",
                 "content": "Chào bạn! Tôi có thể **phân tích chuyên sâu** và **vẽ biểu đồ** cho bất kỳ mã cổ phiếu nào. Hãy thử nhập: *'Phân tích VNM'* hoặc *'Tình hình VIC thế nào'*."}
            ]

        # Hiển thị lịch sử chat cũ
        for m in st.session_state.messages:
            with st.chat_message(m["role"]):
                st.markdown(m["content"])

        # Xử lý khi có input mới
        if prompt := st.chat_input("Nhập mã cổ phiếu hoặc câu hỏi..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                # Placeholder để tạo hiệu ứng suy nghĩ
                status_placeholder = st.empty()
                status_placeholder.markdown("⏳ *AI đang phân tích dữ liệu thị trường...*")
                time.sleep(0.8)  # Giả lập độ trễ xử lý
                status_placeholder.empty()

                p_up = prompt.upper()
                # Tìm trong FULL list (Chatbot nên biết hết, không bị ảnh hưởng bởi bộ lọc bên trái)
                found = [m for m in full_list_ma if m in p_up]

                # --- TRƯỜNG HỢP 1: TÌM THẤY MÃ CỔ PHIẾU ---
                if found:
                    m_code = found[0]

                    # Lấy dữ liệu mới nhất (Từ DF gốc, không phải DF_F đã lọc)
                    d_latest = df[df[col_ma] == m_code].sort_values('Năm').iloc[-1]
                    score = d_latest[col_diem]
                    status = d_latest['Trạng thái']

                    # Lấy dữ liệu lịch sử để vẽ biểu đồ mini
                    d_history = df[df[col_ma] == m_code].sort_values('Năm')

                    # 1. Tạo nội dung Text
                    response_text = f"### 🔍 Kết quả phân tích {m_code} ({d_latest['Tên công ty']})\n"
                    if score < 30:
                        response_text += f"**Đánh giá:** ✅ Doanh nghiệp đang rất **AN TOÀN**. Cấu trúc tài chính vững mạnh."
                    elif score < 60:
                        response_text += f"**Đánh giá:** ⚠️ Doanh nghiệp ở mức **CẢNH BÁO**. Cần theo dõi sát các khoản nợ ngắn hạn."
                    else:
                        response_text += f"**Đánh giá:** 🚨 **BÁO ĐỘNG ĐỎ**. Rủi ro tài chính rất cao, nguy cơ mất thanh khoản."

                    # 2. Hiển thị Metrics đẹp mắt ngay trong Chat
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.metric("Điểm rủi ro", f"{score:.1f}/100",
                                  delta=f"{score - d_history.iloc[0][col_diem]:.1f} vs QK", delta_color="inverse")
                    with c2:
                        color_stt = "green" if "XANH" in status else "red" if "ĐỎ" in status else "orange"
                        st.markdown(f"**Trạng thái:**\n\n:{color_stt}[{status}]")
                    with c3:
                        st.metric("Năm báo cáo", d_latest['Năm'])

                    # 3. Vẽ biểu đồ Sparkline (Biểu đồ xu hướng nhỏ) ngay trong chat
                    st.markdown("**📉 Xu hướng Sức khỏe Tài chính (Toàn bộ lịch sử):**")
                    fig_mini = px.area(d_history, x='Năm', y=col_diem, markers=True,
                                       title=None, height=200)
                    fig_mini.update_layout(margin=dict(l=0, r=0, t=0, b=0),
                                           xaxis_title=None, yaxis_title="Điểm Rủi ro",
                                           showlegend=False)

                    if score > 50:
                        fig_mini.update_traces(line_color='#e74c3c', fillcolor='rgba(231, 76, 60, 0.3)')
                    else:
                        fig_mini.update_traces(line_color='#2ecc71', fillcolor='rgba(46, 204, 113, 0.3)')

                    st.plotly_chart(fig_mini, use_container_width=True)

                    # 4. Hiệu ứng gõ chữ cho phần lời khuyên
                    msg_box = st.empty()
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                    msg_box.markdown(response_text)

                # --- TRƯỜNG HỢP 2: HỎI VỀ RỦI RO CHUNG / NGÀNH ---
                elif "RỦI RO" in p_up or "NGÀNH" in p_up:
                    # Lấy Top 5 từ dữ liệu GỐC để luôn có cái nhìn tổng quan nhất
                    top_risk = df[df['Năm'] == df['Năm'].max()].sort_values(by=col_diem, ascending=False).head(5)
                    response_text = "📊 **Tổng quan thị trường (Năm mới nhất):**\n\nTôi đã quét toàn bộ dữ liệu. Dưới đây là Top 5 doanh nghiệp có chỉ số rủi ro cao nhất hiện tại:"
                    st.markdown(response_text)
                    st.table(top_risk[[col_ma, 'Tên công ty', col_diem, 'Trạng thái']])
                    st.session_state.messages.append({"role": "assistant", "content": response_text})

                # --- TRƯỜNG HỢP 3: KHÔNG HIỂU ---
                else:
                    response_text = "Tôi chưa hiểu ý bạn. Hãy thử nhập một mã chứng khoán cụ thể (Ví dụ: **NVL**, **VIC**, **VNM**) để tôi phân tích biểu đồ cho bạn xem nhé!"
                    st.markdown(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
else:
    st.error("💡 Thiếu file 'ket_qua_du_bao.csv'.")