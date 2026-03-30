import streamlit as st
import pandas as pd
import os
import glob

# 1. 网页基础设置
st.set_page_config(page_title="龙虾选股雷达", page_icon="🦞", layout="wide")
st.title("🦞 龙虾 (OpenClaw) 每日强势股初筛雷达")
st.markdown("筛选策略：9:30-9:45 实际流通盘换手率 > 10% ｜ 9:45 价格突破 9:30 开盘价")

# 2. 自动获取云端仓库里的数据文件
data_dir = "stock_data"
# 如果云端还没有这个文件夹，先自动建一个防止网页报错
if not os.path.exists(data_dir):
    os.makedirs(data_dir) 

csv_files = glob.glob(os.path.join(data_dir, "*.csv"))

if not csv_files:
    st.info("🦞 龙虾今天似乎还没交作业，或者云端 stock_data 文件夹里还没有 CSV 数据文件哦。")
else:
    # 按文件修改时间排序，拿到最新生成的文件
    latest_file = max(csv_files, key=os.path.getmtime)
    
    # 提取日期显示 
    date_str = os.path.basename(latest_file).replace("picks_", "").replace(".csv", "")
    st.subheader(f"📅 最新交易日: {date_str}")
    
    # 3. 读取并展示数据
    try:
        df = pd.read_csv(latest_file)
        
        # 顶部数据概览
        st.metric(label="今日达标股票数量", value=f"{len(df)} 只")
        
        # 使用交互式表格展示，你可以直接在网页上点击表头排序
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )
        
        # 附加功能：如果龙虾抓取了板块或行业数据，自动生成图表
        if '板块' in df.columns:
            st.divider()
            st.subheader("📊 今日达标股票板块分布")
            sector_counts = df['板块'].value_counts()
            st.bar_chart(sector_counts)
        elif '行业' in df.columns:
            st.divider()
            st.subheader("📊 今日达标股票行业分布")
            industry_counts = df['行业'].value_counts()
            st.bar_chart(industry_counts)
            
    except Exception as e:
        st.error(f"读取数据时出错，请检查文件格式: {e}")
