import streamlit as st
import pandas as pd

# 1. Cấu hình tỉ lệ Roll chuẩn theo cơ chế Auto Chess
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
st.title("🧙‍♂️ Auto Chess Ban Strategy")
st.caption("Bản cập nhật: Tự động tính xác suất thực tế theo Level")

# Đọc dữ liệu
try:
    df = pd.read_csv("data.csv")
    
    def get_unique_elements(dataframe, column_name):
        elements = set()
        for val in dataframe[column_name].dropna():
            parts = [p.strip() for p in str(val).split(',')]
            elements.update(parts)
        return sorted([e for e in elements if e and e != 'None'])

    all_races = get_unique_elements(df, 'Tộc (Race)')
    all_classes = get_unique_elements(df, 'Hệ (Class)')
    all_synergies = sorted(list(set(all_races + all_classes)))

    # --- PHẦN 1: THIẾT LẬP TRẬN ĐẤU ---
    with st.expander("⚙️ Cấu hình trận đấu", expanded=True):
        col_l, col_p = st.columns(2)
        with col_l:
            level = st.selectbox("Cấp độ (Level):", list(roll_rates.keys()), index=3)
        with col_p:
            playing = st.multiselect("Hệ/Tộc bạn đang chơi:", all_synergies)

    # --- PHẦN 2: LỌC VÀ CHỌN TƯỚNG ---
    st.subheader("🎯 Tìm tướng mục tiêu")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filter_race = st.selectbox("Lọc Tộc:", ["Tất cả"] + all_races)
    with col_f2:
        filter_class = st.selectbox("Lọc Hệ:", ["Tất cả"] + all_classes)

    filtered_df = df.copy()
    if filter_race != "Tất cả":
        filtered_df = filtered_df[filtered_df['Tộc (Race)'].str.contains(filter_race, na=False)]
    if filter_class != "Tất cả":
        filtered_df = filtered_df[filtered_df['Hệ (Class)'].str.contains(filter_class, na=False)]

    targets = st.multiselect("Chọn tướng cần tìm (tối đa 3):", filtered_df['Tên quân cờ'].unique(), max_selections=3)

    # --- PHẦN 3: LOGIC TÍNH TOÁN & HIỂN THỊ ---
    if targets:
        st.divider()
        
        # LỌC BỂ TƯỚNG (POOL) THỰC TẾ
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
                
                # Tướng 5$ có cơ chế roll khác (không phụ thuộc pool size 113) nên ta tạm bỏ qua boost %
                if t_cost >= 5: 
                    ban_impact["details"].append(f"• **{t_name}**: (5$ không tính)")
                    continue
                    
                num_removed = len(banned_units[banned_units['Giá (Gold)'] == t_cost])
                
                if num_removed > 0:
                    # Tỉ lệ rơi theo Level
                    rate_by_level = roll_rates[level][t_cost] / 100
                    
                    # Xác suất trong 1 ô cửa hàng
                    p_old = rate_by_level / pool_counts[t_cost]
                    p_new = rate_by_level / (pool_counts[t_cost] - num_removed)
                    
                    boost = (p_new / p_old - 1) * 100
                    ban_impact["details"].append(
                        f"• **{t_name}**: +{boost:.1f}% (XS: {p_old:.2%} → {p_new:.2%})"
                    )
                    ban_impact["total_boost"] += boost
            
            if ban_impact["total_boost"] > 0:
                results.append(ban_impact)

        # Xuất kết quả Top 3
        top_3 = sorted(results, key=lambda x: x['total_boost'], reverse=True)[:3]
        
        if top_3:
            st.subheader("💡 3 Gợi ý Ban tối ưu nhất:")
            for i, res in enumerate(top_3):
                with st.expander(f"Gợi ý {i+1}: Ban **{res['name']}** (Lợi ích: +{res['total_boost']:.1f}%)", expanded=True):
                    for d in res['details']:
                        st.write(d)
        else:
            st.info("Hệ bạn định Ban không chứa quân cờ nào cùng bậc tiền với tướng mục tiêu.")
    else:
        st.info("👆 Vui lòng chọn tướng mục tiêu để xem phân tích xác suất.")

except Exception as e:
    st.error(f"Lỗi vận hành: {e}")
