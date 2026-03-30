import streamlit as st
import pandas as pd
import os
import glob
import plotly.express as px

# ================= 网页基础设置 =================
# 👉 这里可以修改网页标签页的名字和图标
st.set_page_config(page_title="强势突破监控雷达", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 2.2rem; font-weight: 700; color: #ff4b4b; }
    [data-testid="stMetricLabel"] { font-size: 1.1rem; font-weight: 500; color: #555; }
    [data-testid="stDataFrame"] div[data-testid="stTable"] td, 
    [data-testid="stDataFrame"] div[data-testid="stTable"] th { text-align: center !important; }
    </style>
    """, unsafe_allow_html=True) 

# ================= 左侧控制面板 =================
with st.sidebar:
    # 👉 这里可以修改左侧边栏的控制台标题
    st.title("⚙️ 策略控制台")
    data_dir = "stock_data"
    if not os.path.exists(data_dir): os.makedirs(data_dir)
    csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
    
    if not csv_files:
        # 👉 这里修改没有数据时的提示语
        st.warning("📭 暂无数据，请等待今日复盘数据上传。")
        st.stop()
        
    available_dates = sorted([os.path.basename(f).replace("picks_", "").replace(".csv", "") for f in csv_files], reverse=True)
    selected_date = st.selectbox("📅 选择复盘日期", available_dates)
    st.divider()
    show_only_breakout = st.checkbox("🔥 仅看 9:45 价格突破 9:30 的强势股", value=False)

# ================= 右侧主展区 =================
# 👉 这里修改网页主标题
st.title("⚡ 每日强势股初筛看板")
st.markdown(f"**当前日期：** `{selected_date}` ｜ **初始过滤：** 9:30-9:45 换手率 > 10%")

file_path = os.path.join(data_dir, f"picks_{selected_date}.csv")

try:
    df = pd.read_csv(file_path)
    
    col_930 = [c for c in df.columns if '9:30' in c or '开盘' in c][0]
    col_945 = [c for c in df.columns if '9:45' in c or '现价' in c][0]
    
    df['15分钟涨幅(%)'] = ((df[col_945] - df[col_930]) / df[col_930]) * 100
    display_df = df[df[col_945] > df[col_930]] if show_only_breakout else df.copy()

    # ======== 顶部核心数据 ========
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1: st.metric("基础达标总数", f"{len(df)} 只")
    with m_col2: st.metric("当前展示数量", f"{len(display_df)} 只")
    with m_col3:
        if len(df) > 0:
            win_rate = len(df[df[col_945] > df[col_930]]) / len(df) * 100
            st.metric("早盘突破率", f"{win_rate:.1f}%")

    # ======== 数据清单 ========
    st.divider()
    st.subheader("📋 详细个股数据清单")
    
    if not display_df.empty:
        cols = display_df.columns.tolist()
        
        if '15分钟涨幅(%)' in cols:
            cols.insert(cols.index(col_945) + 1, cols.pop(cols.index('15分钟涨幅(%)')))
        col_daily_change = [c for c in cols if '收盘涨幅' in c or '全天涨幅' in c or '涨跌幅' in c]
        if col_daily_change:
            cols.insert(cols.index('15分钟涨幅(%)') + 1, cols.pop(cols.index(col_daily_change[0])))
            
        display_df = display_df[cols]
        format_df = display_df.copy()
        
        def fmt_pct(x): return f"{x:.2f} %" if pd.notna(x) else "-"
        def fmt_price(x): return f"¥ {x:.2f}" if pd.notna(x) else "-"

        for col in format_df.columns:
            if format_df[col].dtype == object and format_df[col].astype(str).str.contains('%').any():
                format_df[col] = format_df[col].astype(str).str.replace('%', '', regex=False)
                
            if '价' in col:
                format_df[col] = pd.to_numeric(format_df[col], errors='coerce').apply(fmt_price)
            elif '换手' in col or '涨幅' in col or '跌幅' in col or '率' in col:
                format_df[col] = pd.to_numeric(format_df[col], errors='coerce').apply(fmt_pct)
        
        def color_red_green(val):
            if isinstance(val, str) and '%' in val:
                try:
                    num = float(val.replace('%', '').strip())
                    if num > 0:
                        return 'color: #ff4b4b;' 
                    elif num < 0:
                        return 'color: #00c04b;' 
                except:
                    pass
            return ''
        
        styled_df = format_df.style.set_properties(**{'text-align': 'center'})
        
        change_cols = [c for c in format_df.columns if '涨幅' in c or '跌幅' in c]
        if change_cols:
            try:
                styled_df = styled_df.map(color_red_green, subset=change_cols)
            except AttributeError:
                styled_df = styled_df.applymap(color_red_green, subset=change_cols)

        st.dataframe(styled_df, use_container_width=True, hide_index=True)

    # ======== 极简可视化分析 ========
    if not display_df.empty and '行业' in display_df.columns:
        st.divider()
        st.subheader("📊 热门行业分布")
        
        industry_counts = display_df['行业'].value_counts().reset_index()
        industry_counts.columns = ['行业', '股票数量']
        top_industry = industry_counts.head(15).sort_values(by='股票数量', ascending=True)
        
        fig_industry = px.bar(top_industry, x='股票数量', y='行业', orientation='h', text='股票数量')
        fig_industry.update_traces(marker_color='#3b71ca', textposition='outside', textfont_size=13)
        fig_industry.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False), 
            yaxis=dict(title=None, tickfont_size=14), margin=dict(l=0, r=40, t=10, b=0), 
            height=400 + len(top_industry) * 15 
        )
        st.plotly_chart(fig_industry, use_container_width=True)

except Exception as e:
    st.error(f"读取数据时出错，请检查 CSV 格式。详细报错: {e}")
