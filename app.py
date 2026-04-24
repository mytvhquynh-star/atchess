import streamlit as st
import pandas as pd

# 1. Cấu hình tỉ lệ Roll chuẩn
roll_rates = {
    5: {1: 45, 2: 35, 3: 18, 4: 2},
    6: {1: 30, 2: 40, 3: 25, 4: 5},
    7: {1: 25, 2: 30, 3: 35, 4: 10},
    8: {1: 20, 2: 28, 3: 35, 4: 16},
    9: {1: 20, 2: 25, 3: 27, 4: 25},
    10: {1: 15, 2: 25, 3: 25, 4: 29},
    11: {1: 15, 2: 20, 3: 20, 4: 36}
}

st.set_page_config(page_title="Auto Chess Ban Tool", layout="centered")
st.title("🧙‍♂️ Tự Động Gợi Ý Ban Tướng")

# Đọc dữ liệu
try:
    df = pd.read_csv("data.csv")
    
    # Hàm lấy danh sách Tộc/Hệ duy nhất
    def get_unique_elements(dataframe, column_name):
        elements = set()
        for val in dataframe[column_name].dropna():
            parts = [p.strip() for p in str(val).split(',')]
            elements.update(parts)
        return sorted([e for e in elements if e and e != 'None'])

    all_races = get_unique_elements(df, 'Tộc (Race)')
    all_classes = get_unique_elements(df, 'Hệ (Class)')
    all_synergies = sorted(list(set(all_races + all_classes)))

    # --- PHẦN 1: THIẾT LẬP CHUNG ---
    st.subheader("1. Thiết lập trận đấu")
    col_l, col_p = st.columns(2)
    with col_l:
        level = st.selectbox("Cấp độ (Level):", list(roll_rates.keys()), index=3)
    with col_p:
        playing = st.multiselect("Hệ/Tộc bạn đang chơi (Không Ban):", all_synergies)

    st.divider()

    # --- PHẦN 2: LỌC VÀ CHỌN TƯỚNG MỤC TIÊU ---
    st.subheader("2. Chọn tướng cần tìm")
    st.caption("Mẹo: Dùng Tộc/Hệ để lọc nhanh danh sách tướng bên dưới")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filter_race = st.selectbox("Lọc theo Tộc:", ["Tất cả"] + all_races)
    with col_f2:
        filter_class = st.selectbox("Lọc theo Hệ:", ["Tất cả"] + all_class)

    # Logic lọc danh sách tướng
    filtered_df = df.copy()
    if filter_race != "Tất cả":
        filtered_df = filtered_df[filtered_df['Tộc (Race)'].str.contains(filter_race, na=False)]
    if filter_class != "Tất cả":
        filtered_df = filtered_df[filtered_df['Hệ (Class)'].str.contains(filter_class, na=False)]

    targets = st.multiselect("Chọn tướng mục tiêu (1-3):", filtered_df['Tên quân cờ'].unique())

    # --- PHẦN 3: LOGIC TÍNH TOÁN ---
    if targets:
        st.divider()
        
        # LỌC BỂ TƯỚNG (POOL) THỰC TẾ (Loại bỏ Egersis và Pandaren > 2$)
        mask_pool = (
            (~df['Tộc (Race)'].str.contains('Egersis', na=False)) & 
            (~df['Hệ (Class)'].str.contains('Egersis', na=False)) &
            ~((df['Tộc (Race)'].str.contains('Pandaren', na=False)) & (df['Giá (Gold)'] > 2))
        )
        df_active_pool = df[mask_pool].copy()
        pool_counts = df_active_pool['Giá (Gold)'].value_counts().to_dict()

        results = []
        for syn in all_synergies:
            if syn in playing or syn == "Egersis": continue
            
            mask_ban = df_active_pool['Tộc (Race)'].str.contains(syn, na=False) | df_active_pool['Hệ (Class)'].str.contains(syn, na=False)
            banned_units = df_active_pool[mask_ban]
            
            if any(u in banned_units['Tên quân cờ'].values for u in targets):
                continue
            
            ban_impact = {"name": syn, "details": [], "total_boost": 0}
            for t_name in targets:
                t_row = df_active_pool[df_active_pool['Tên quân cờ'] == t_name]
                if t_row.empty: continue
                t_cost = t_row['Giá (Gold)'].values[0]
                
                if t_cost >= 5: 
                    ban_impact["details"].append(f"**{t_name}**: (5$ ko tính)")
                    continue
                    
                num_removed = len(banned_units[banned_units['Giá (Gold)'] == t_cost])
                if num_removed > 0:
                    old_p = roll_rates[level][t_cost] / pool_counts[t_cost]
                    new_p = roll_rates[level][t_cost] / (pool_counts[t_cost] - num_removed)
                    boost = (new_p / old_p - 1) * 100
                    ban_impact["details"].append(f"**{t_name}**: +{boost:.1f}%")
                    ban_impact["total_boost"] += boost
            
            if ban_impact["total_boost"] > 0:
                results.append(ban_impact)

        top_3 = sorted(results, key=lambda x: x['total_boost'], reverse=True)[:3]
        
        if top_3:
            st.subheader("💡 3 Gợi ý Ban tốt nhất:")
            for i, res in enumerate(top_3):
                with st.expander(f"Gợi ý {i+1}: Ban **{res['name']}** (Tổng tăng: {res['total_boost']:.1f}%)", expanded=True):
                    for d in res['details']:
                        st.write(d)
        else:
            st.info("Không tìm thấy hệ nào phù hợp để Ban.")
    else:
        st.info("👆 Hãy dùng bộ lọc Tộc/Hệ và chọn tướng để xem kết quả.")

except Exception as e:
    st.error(f"Lỗi: {e}")
