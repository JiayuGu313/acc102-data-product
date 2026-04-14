import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 页面配置
st.set_page_config(page_title="专注植物园", page_icon="🌱")

st.title("🌱 专注植物园")
st.markdown("专注越久，植物长得越高！")

# 初始化用户数据文件
USER_DATA_FILE = "user_data.csv"

if not os.path.exists(USER_DATA_FILE):
    df_init = pd.DataFrame({
        "plant": [],
        "total_minutes": [],
        "last_update": []
    })
    df_init.to_csv(USER_DATA_FILE, index=False)

# 加载植物数据
@st.cache_data
def load_plants():
    return pd.read_csv("data/plant_data.csv")

plants_df = load_plants()

# 侧边栏：选择植物
st.sidebar.header("🌿 我的花园")
selected_plant = st.sidebar.selectbox("选择一颗种子", plants_df["plant_name"].tolist())

# 主区域：显示当前植物
st.subheader(f"你的 {selected_plant}")

# 读取用户当前植物的累计时间
user_df = pd.read_csv(USER_DATA_FILE)
if selected_plant in user_df["plant"].values:
    current_total = user_df[user_df["plant"] == selected_plant]["total_minutes"].values[0]
else:
    current_total = 0

# 获取当前植物的数据行
plant_row = plants_df[plants_df["plant_name"] == selected_plant].iloc[0]

# 四阶段阈值
thresholds = [
    plant_row["stage1_threshold"],
    plant_row["stage2_threshold"],
    plant_row["stage3_threshold"],
    plant_row["stage4_threshold"]
]

# 找到当前阶段
stage = 1
for i, threshold in enumerate(thresholds[1:], start=2):
    if current_total >= threshold:
        stage = i

# 获取对应阶段的图片
stage_image_col = f"stage{stage}_image"
stage_img = plant_row[stage_image_col]

# 显示植物图片和进度
col1, col2 = st.columns([1, 2])
with col1:
    st.image(f"images/{stage_img}", width=150)
with col2:
    st.metric("累计专注", f"{current_total} 分钟")
    # 计算进度（到阶段四的百分比）
    max_threshold = thresholds[-1]
    progress = min(current_total / max_threshold, 1.0)
    st.progress(progress)

    # 显示当前阶段名称
    stage_names = {1: "🌱 幼苗", 2: "🌿 成长中", 3: "🍃 茂盛期", 4: "🌸 完全绽放"}
    st.info(f"当前阶段：{stage_names[stage]}")

# 添加专注时间
st.subheader("📝 记录今天的专注")
today_minutes = st.number_input("今天专注了多少分钟？", min_value=0, max_value=480, step=10, value=0)

if st.button("💧 浇水长大"):
    if today_minutes > 0:
        new_total = current_total + today_minutes

        # 更新用户数据
        if selected_plant in user_df["plant"].values:
            user_df.loc[user_df["plant"] == selected_plant, "total_minutes"] = new_total
            user_df.loc[user_df["plant"] == selected_plant, "last_update"] = datetime.now().strftime("%Y-%m-%d")
        else:
            new_row = pd.DataFrame({
                "plant": [selected_plant],
                "total_minutes": [new_total],
                "last_update": [datetime.now().strftime("%Y-%m-%d")]
            })
            user_df = pd.concat([user_df, new_row], ignore_index=True)

        user_df.to_csv(USER_DATA_FILE, index=False)

        # 检查是否达到新阶段
        old_stage = stage
        new_stage = old_stage
        for i, thresh in enumerate(thresholds[1:], start=2):
            if new_total >= thresh:
                new_stage = i

        if new_stage > old_stage:
            st.balloons()
            st.success(f"🎉 恭喜！你的 {selected_plant} 进入了 {stage_names[new_stage]} 阶段！")
        else:
            st.success(f"✅ 已记录 {today_minutes} 分钟专注！继续加油！")

        st.rerun()
    else:
        st.warning("请输入专注分钟数")

# 显示花园收藏
st.sidebar.subheader("🌸 我的植物园")
for plant in plants_df["plant_name"].tolist():
    if plant in user_df["plant"].values:
        minutes = user_df[user_df["plant"] == plant]["total_minutes"].values[0]
        plant_info = plants_df[plants_df["plant_name"] == plant].iloc[0]
        max_needed = plant_info["stage4_threshold"]
        if minutes >= max_needed:
            st.sidebar.success(f"✅ {plant} (完全绽放)")
        elif minutes >= plant_info["stage3_threshold"]:
            st.sidebar.info(f"🍃 {plant} (茂盛期)")
        elif minutes >= plant_info["stage2_threshold"]:
            st.sidebar.info(f"🌿 {plant} (成长中)")
        else:
            st.sidebar.text(f"🌱 {plant} (幼苗)")
    else:
        st.sidebar.text(f"⚪ {plant} (未解锁)")

# 侧边栏底部显示提示
st.sidebar.markdown("---")
st.sidebar.caption("💡 提示：专注越久，植物长得越高！")
st.sidebar.caption("🌸 达到100分钟，植物完全绽放！")

# 可选：重置按钮
with st.sidebar.expander("⚙️ 设置"):
    if st.button("重置所有数据"):
        df_init = pd.DataFrame({
            "plant": [],
            "total_minutes": [],
            "last_update": []
        })
        df_init.to_csv(USER_DATA_FILE, index=False)
        st.success("数据已重置")
        st.rerun()
