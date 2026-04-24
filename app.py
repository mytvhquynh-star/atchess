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
st.caption("Lưu ý: Hệ Egersis và Pandaren (3,4,5$) đã được loại bỏ khỏi bể tướng roll.")

# Đọc dữ liệu
try:
    df = pd.read_csv("data.csv")
    
    def get_all_synergies(dataframe):
        syns = set()
        for col in ['Tộc (Race)', 'Hệ (Class)']:
            for val in dataframe[col].dropna():
                parts = [p.strip() for p in str(val).split(',')]
                syns.update(parts)
        return sorted([s for s in syns if s and s != 'None'])

    all_synergies = get_all_synergies(df)

    # --- NHẬP LIỆU ---
    col1, col2 = st.columns(2)
    with col1:
        level = st.selectbox("Cấp độ (Level):", list(roll_rates.keys()), index=3)
    with col2:
        playing = st.multiselect("Hệ/Tộc bạn đang chơi:", all_synergies)

    targets = st.multiselect("Chọn tướng bạn cần tìm (1-3):", df['Tên quân cờ'].unique())

    # --- LOGIC TÍNH TOÁN TỰ ĐỘNG ---
    if targets:
        st.divider()
        
        # LỌC BỂ TƯỚNG (POOL) THỰC TẾ
        # 1. Loại bỏ toàn bộ Egersis
        # 2. Loại bỏ Pandaren giá > 2 gold
        mask_pool = (
            (~df['Tộc (Race)'].str.contains('Egersis', na=False)) & 
            (~df['Hệ (Class)'].str.contains('Egersis', na=False)) &
            ~((df['Tộc (Race)'].str.contains('Pandaren', na=False)) & (df['Giá (Gold)'] > 2))
        )
        
        df_active_pool = df[mask_pool].copy()
        pool_counts = df_active_pool['Giá (Gold)'].value_counts().to_dict()

        results = []
        for syn in all_synergies:
            # Không gợi ý Ban những hệ không có trong bể roll (Egersis) hoặc hệ đang chơi
            if syn in playing or syn == "Egersis": 
                continue
            
            # Tìm tướng bị loại khi BAN hệ này trong bể roll thực tế
            mask_ban = df_active_pool['Tộc (Race)'].str.contains(syn, na=False) | df_active_pool['Hệ (Class)'].str.contains(syn, na=False)
            banned_units = df_active_pool[mask_ban]
            
            # Nếu hệ định BAN chứa tướng cần tìm -> Bỏ qua
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

        # Xuất kết quả
        top_3 = sorted(results, key=lambda x: x['total_boost'], reverse=True)[:3]
        
        if top_3:
            st.subheader("💡 3 Gợi ý Ban tốt nhất:")
            for i, res in enumerate(top_3):
                with st.expander(f"Gợi ý {i+1}: Ban **{res['name']}** (Tổng tăng: {res['total_boost']:.1f}%)", expanded=True):
                    for d in res['details']:
                        st.write(d)
        else:
            st.info("Không tìm thấy hệ nào để Ban giúp tăng tỉ lệ (có thể do các hệ còn lại không có tướng cùng bậc tiền với tướng mục tiêu).")
    else:
        st.write("👆 *Chọn tướng để xem kết quả.*")

except Exception as e:
    st.error(f"Lỗi: {e}")
