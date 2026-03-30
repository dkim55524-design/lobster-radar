import streamlit as st
import pandas as pd
import os
import glob

# 1. 网页基础设置 (Pro版)
st.set_page_config(page_title="龙虾选股雷达 Pro", page_icon="🦞", layout="wide")

# ================= 左侧控制面板 (Sidebar) =================
with st.sidebar:
    st.image("https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.x/svgs/solid/otter.svg", width=50) # 放个小图标占位
    st.header("⚙️ 龙虾控制台")
    
    # 获取所有历史数据文件
    data_dir = "stock_data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
    
    if not csv_files:
        st.warning("暂无数据，请等待龙虾上传。")
        st.stop() # 停止运行后面的代码
        
    # 提取所有可用日期并倒序排列 (最新的在最上面)
    available_dates = sorted([os.path.basename(f).replace("picks_", "").replace(".csv", "") for f in csv_files], reverse=True)
    
    # 功能 1：历史日期选择器
    selected_date = st.selectbox("📅 选择复盘日期", available_dates)
    
    st.divider()
    
    # 功能 2：强弱筛选开关
    st.subheader("🎯 走势筛选")
    show_only_breakout = st.checkbox("🔥 仅显示 9:45 突破 9:30 开盘价", value=False, help="勾选后，仅显示走势强劲、价格突破的标的")

# ================= 右侧主展区 (Main Content) =================
st.title("🦞 龙虾 (OpenClaw) 每日初筛雷达 Pro")
st.markdown(f"**当前查看日期：** `{selected_date}` ｜ **基础池：** 9:30-9:45 实际流通换手率 > 10%")

# 读取用户选定日期的数据
file_path = os.path.join(data_dir, f"picks_{selected_date}.csv")

try:
    df = pd.read_csv(file_path)
    
    # 动态筛选逻辑
    # 注意：这里假设你的列名包含 "9:30" 和 "9:45" 的字眼。如果龙虾用的名字不一样，比如叫 "开盘价" 和 "现价"，你可能需要修改这里。
    col_930 = [c for c in df.columns if '9:30' in c or '开盘' in c][0]
    col_945 = [c for c in df.columns if '9:45' in c or '现价' in c or '收盘' in c][0]
    
    # 如果用户勾选了“仅显示突破”
    if show_only_breakout:
        display_df = df[df[col_945] > df[col_930]]
    else:
        display_df = df

    # 顶部数据概览 (分成三列，看起来更高级)
    col1, col2, col3 = st.columns(3)
    col1.metric(label="基础达标总数 (>10%换手)", value=f"{len(df)} 只")
    col2.metric(label="当前筛选展示数量", value=f"{len(display_df)} 只")
    
    if len(df) > 0:
        win_rate = len(df[df[col_945] > df[col_930]]) / len(df) * 100
        col3.metric(label="今日早盘突破率", value=f"{win_rate:.1f}%")

    # 漂亮的交互式表格
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
    
    # 图表区：只统计当前筛选下的数据
    if not display_df.empty:
        col_chart1, col_chart2 = st.columns(2)
        with col_chart1:
            if '板块' in display_df.columns:
                st.write("📊 **板块分布**")
                st.bar_chart(display_df['板块'].value_counts())
        with col_chart2:
            if '行业' in display_df.columns:
                st.write("📊 **行业分布**")
                st.bar_chart(display_df['行业'].value_counts())

except Exception as e:
    st.error(f"读取或处理数据时出错，请确认龙虾生成的 CSV 列名是否正确。详细报错: {e}")
