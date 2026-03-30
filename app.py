import streamlit as st
import pandas as pd
import os
import glob
import plotly.express as px

# ================= 网页基础设置 =================
st.set_page_config(page_title="龙虾选股雷达 | 极简版", page_icon="🦞", layout="wide", initial_sidebar_state="expanded")

# CSS: 指标卡片美化 & 强制表格居中
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
    st.title("⚙️ 龙虾控制台")
    data_dir = "stock_data"
    if not os.path.exists(data_dir): os.makedirs(data_dir)
    csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
    
    if not csv_files:
        st.warning("📭 暂无数据，请等待龙虾上传。")
        st.stop()
        
    available_dates = sorted([os.path.basename(f).replace("picks_", "").replace(".csv", "") for f in csv_files], reverse=True)
    selected_date = st.selectbox("📅 选择复盘日期", available_dates)
    st.divider()
    show_only_breakout = st.checkbox("🔥 仅看 9:45 价格突破 9:30 的强势股", value=False)

# ================= 右侧主展区 =================
st.title("🦞 龙虾每日初筛雷达")
st.markdown(f"**当前日期：** `{selected_date}` ｜ **初始过滤：** 9:30-9:45 换手率 > 10%")

file_path = os.path.join(data_dir, f"picks_{selected_date}.csv")

try:
    df = pd.read_csv(file_path)
    
    # 智能匹配列名 (移除了对"收盘"的模糊匹配，防止与"收盘涨幅"冲突)
    col_930 = [c for c in df.columns if '9:30' in c or '开盘' in c][0]
    col_945 = [c for c in df.columns if '9:45' in c or '现价' in c][0]
    col_turnover = [c for c in df.columns if '换手' in c or 'turnover' in c][0]
    
    # 智能寻找龙虾新增的“收盘涨幅”列
    col_daily_change = [c for c in df.columns if '收盘涨幅' in c or '全天涨幅' in c or '今日涨幅' in c or '涨跌幅' in c]
    has_daily_change = len(col_daily_change) > 0
    if has_daily_change:
        col_daily_change = col_daily_change[0]
    
    # 计算15分钟涨幅
    df['15分钟涨幅(%)'] = ((df[col_945] - df[col_930]) / df[col_930]) * 100
    
    # 侧边栏筛选逻辑
    display_df = df[df[col_945] > df[col_930]] if show_only_breakout else df.copy()

    # ======== 顶部核心数据 ========
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1: st.metric("基础达标总数", f"{len(df)} 只")
    with m_col2: st.metric("当前展示数量", f"{len(display_df)} 只")
    with m_col3:
        if len(df) > 0:
            win_rate = len(df[df[col_945] > df[col_930]]) / len(df) * 100
            st.metric("早盘突破率", f"{win_rate:.1f}%")

    # ======== 数据清单 (强制居中 & 格式化) ========
    st.divider()
    st.subheader("📋 详细个股数据清单")
    
    if not display_df.empty:
        # 优化列的展示顺序
        cols = display_df.columns.tolist()
        
        # 1. 把 15分钟涨幅 放到 9:45价格 的后面
        if '15分钟涨幅(%)' in cols:
            cols.insert(cols.index(col_945) + 1, cols.pop(cols.index('15分钟涨幅(%)')))
            
        # 2. 如果存在 收盘涨幅，把它放到 15分钟涨幅 的后面，方便对比
        if has_daily_change and col_daily_change in cols:
            cols.insert(cols.index('15分钟涨幅(%)') + 1, cols.pop(cols.index(col_daily_change)))
            
        display_df = display_df[cols]
        
        # 将数字强制转为带符号的字符串，锁定格式
        format_df = display_df.copy()
        format_df[col_turnover] = pd.to_numeric(format_df[col_turnover], errors='coerce').apply(lambda x: f"{x:.2f} %")
        format_df[col_930] = pd.to_numeric(format_df[col_930], errors='coerce').apply(lambda x: f"¥ {x:.2f}")
        format_df[col_945] = pd.to_numeric(format_df[col_945], errors='coerce').apply(lambda x: f"¥ {x:.2f}")
        format_df['15分钟涨幅(%)'] = pd.to_numeric(format_df['15分钟涨幅(%)'], errors='coerce').apply(lambda x: f"{x:.2f} %")
        
        # 如果有收盘涨幅，也对它进行美化格式化
        if has_daily_change:
            format_df[col_daily_change] = pd.to_numeric(format_df[col_daily_change], errors='coerce').apply(lambda x: f"{x:.2f} %")
        
        # 使用 Styler 彻底居中并展示
        styled_df = format_df.style.set_properties(**{'text-align': 'center'})
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
