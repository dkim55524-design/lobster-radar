import streamlit as st
import pandas as pd
import os
import glob
import plotly.express as px

# ================= 网页基础设置 (Pro v3.0) =================
st.set_page_config(
    page_title="龙虾选股雷达 | Pro",
    page_icon="🦞",
    layout="wide", # 启用宽屏，让图表有更多空间展示
    initial_sidebar_state="expanded" 
)

# 注入 CSS 美化顶部数据卡片
st.markdown("""
    <style>
    [data-testid="stMetricValue"] {
        font-size: 2.2rem;
        font-weight: 700;
        color: #ff4b4b;
    }
    [data-testid="stMetricLabel"] {
        font-size: 1.1rem;
        font-weight: 500;
        color: #555;
    }
    </style>
    """, unsafe_allow_stdio=True)

# ================= 左侧控制面板 =================
with st.sidebar:
    st.title("⚙️ 龙虾控制台 Pro")
    
    data_dir = "stock_data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
    
    if not csv_files:
        st.warning("📭 暂无数据，请等待龙虾上传。")
        st.stop()
        
    available_dates = sorted([os.path.basename(f).replace("picks_", "").replace(".csv", "") for f in csv_files], reverse=True)
    selected_date = st.selectbox("📅 选择复盘日期", available_dates)
    
    st.divider()
    st.subheader("🎯 走势二次筛选")
    show_only_breakout = st.checkbox("🔥 仅看 9:45 价格突破 9:30 开盘价", value=False)
    
    st.divider()
    st.caption("📊 数据源: Openclaw 自动抓取")

# ================= 右侧主展区 =================
st.title("🦞 龙虾每日初筛雷达")
st.markdown(f"**当前复盘日期：** `{selected_date}` ｜ **初始过滤条件：** 9:30-9:45 实际换手率 > 10%")

file_path = os.path.join(data_dir, f"picks_{selected_date}.csv")

try:
    df = pd.read_csv(file_path)
    
    # 智能匹配列名
    col_930 = [c for c in df.columns if '9:30' in c or '开盘' in c][0]
    col_945 = [c for c in df.columns if '9:45' in c or '现价' in c or '收盘' in c][0]
    col_turnover = [c for c in df.columns if '换手' in c or 'turnover' in c][0]
    
    # ======== 计算涨幅 ========
    df['15分钟涨幅(%)'] = ((df[col_945] - df[col_930]) / df[col_930]) * 100
    
    # 根据侧边栏开关进行动态筛选
    if show_only_breakout:
        display_df = df[df[col_945] > df[col_930]]
    else:
        display_df = df

    # ======== 美化区 1：顶部核心数据卡片 ========
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.metric("初筛达标总数 (>10%换手)", f"{len(df)} 只")
    with m_col2:
        st.metric("当前筛选展示数量", f"{len(display_df)} 只")
    with m_col3:
        if len(df) > 0:
            win_rate = len(df[df[col_945] > df[col_930]]) / len(df) * 100
            st.metric("早盘价格突破率", f"{win_rate:.1f}%")

    # ======== 美化区 2：精修数据表格 ========
    st.divider()
    st.subheader("📋 详细个股数据清单")
    
    # 自动将展示的列按逻辑排序
    cols = display_df.columns.tolist()
    if '15分钟涨幅(%)' in cols:
        cols.insert(cols.index(col_945) + 1, cols.pop(cols.index('15分钟涨幅(%)')))
        display_df = display_df[cols]

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            col_turnover: st.column_config.NumberColumn("换手率(%)", format="%.2f %%"),
            col_930: st.column_config.NumberColumn("9:30开盘价", format="¥ %.2f"),
            col_945: st.column_config.NumberColumn("9:45价格", format="¥ %.2f"),
            "15分钟涨幅(%)": st.column_config.NumberColumn("15分钟涨幅", format="%.2f %%"),
        }
    )
    
    # ======== 美化区 3：高级交互图表 ========
    if not display_df.empty:
        st.divider()
        st.subheader("📊 热点分布可视化分析")
        
        c_col1, c_col2 = st.columns([1, 1.5]) # 左边饼图略小，右边条形图略宽
        
        with c_col1:
            if '板块' in display_df.columns:
                st.write("**板块占比 (环形图)**")
                sector_counts = display_df['板块'].value_counts().reset_index()
                sector_counts.columns = ['板块', '股票数量']
                
                fig_sector = px.pie(
                    sector_counts, 
                    values='股票数量', 
                    names='板块',
                    hole=0.4, 
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_sector.update_traces(textposition='inside', textinfo='percent+label')
                fig_sector.update_layout(showlegend=False, margin=dict(l=0, r=0, t=10, b=0))
                st.plotly_chart(fig_sector, use_container_width=True)
                
        with c_col2:
            if '行业' in display_df.columns:
                st.write("**热门行业排行 (横向条形图)**")
                industry_counts = display_df['行业'].value_counts().reset_index()
                industry_counts.columns = ['行业', '股票数量']
                # 只取前15个热门行业，并升序排列以便画图时最多的在最上面
                top_industry = industry_counts.head(15).sort_values(by='股票数量', ascending=True)
                
                fig_industry = px.bar(
                    top_industry,
                    x='股票数量',
                    y='行业',
                    orientation='h', 
                    color='股票数量', 
                    color_continuous_scale='Blues'
                )
                fig_industry.update_layout(
                    xaxis=dict(tickmode='linear', dtick=1), 
                    coloraxis_showscale=False, 
                    margin=dict(l=0, r=0, t=10, b=0)
                )
                st.plotly_chart(fig_industry, use_container_width=True)

except Exception as e:
    st.error(f"读取数据时出错，请检查 CSV 格式。详细报错: {e}")
