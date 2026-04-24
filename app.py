import streamlit as st
import pandas as pd

# Cấu hình tỉ lệ Roll chuẩn
roll_rates = {
    5: {1: 45, 2: 35, 3: 18, 4: 2},
    6: {1: 30, 2: 40, 3: 25, 4: 5},
    7: {1: 25, 2: 30, 3: 35, 4: 10},
    8: {1: 20, 2: 28, 3: 35, 4: 16},
    9: {1: 20, 2: 25, 3: 27, 4: 25},
    10: {1: 15, 2: 25, 3: 25, 4: 29},
    11: {1: 15, 2: 20, 3: 20, 4: 36}
}

st.set_page_config(page_title="Auto Chess Ban Picker", layout="centered")
st.title("🧙‍♂️ Chiến Thuật Ban Tướng Auto Chess")

# Đọc dữ liệu
try:
    df = pd.read_csv("data.csv")
    
    # Xử lý Tộc/Hệ đa dạng (tách dấu phẩy trong ngoặc kép)
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
        level = st.selectbox("Cấp độ của bạn (Level):", list(roll_rates.keys()), index=3)
    with col2:
        playing = st.multiselect("Hệ/Tộc bạn đang chơi:", all_synergies)

    targets = st.multiselect("Chọn 1-3 tướng bạn cần tìm:", df['Tên quân cờ'].unique(), max_selections=3)

    if st.button("TÍNH TOÁN GỢI Ý BAN", use_container_width=True):
        if not targets:
            st.error("Chọn ít nhất một tướng mục tiêu!")
        else:
            results = []
            pool_counts = df['Giá (Gold)'].value_counts().to_dict()

            # Duyệt qua từng Tộc/Hệ để thử BAN
            for syn in all_synergies:
                if syn in playing: continue
                
                # Tìm các tướng bị loại nếu BAN hệ này
                mask = df['Tộc (Race)'].str.contains(syn, na=False) | df['Hệ (Class)'].str.contains(syn, na=False)
                banned_units = df[mask]
                
                # Nếu hệ định BAN chứa tướng cần tìm -> Bỏ qua
                if any(u in banned_units['Tên quân cờ'].values for u in targets):
                    continue
                
                ban_impact = {"name": syn, "details": [], "total_boost": 0}
                
                for t_name in targets:
                    t_cost = df[df['Tên quân cờ'] == t_name]['Giá (Gold)'].values[0]
                    if t_cost >= 5: 
                        ban_impact["details"].append(f"{t_name}: (5$ không tính)")
                        continue
                        
                    num_removed = len(banned_units[banned_units['Giá (Gold)'] == t_cost])
                    
                    if num_removed > 0:
                        old_p = roll_rates[level][t_cost] / pool_counts[t_cost]
                        new_p = roll_rates[level][t_cost] / (pool_counts[t_cost] - num_removed)
                        boost = (new_p / old_p - 1) * 100
                    else:
                        boost = 0
                    
                    ban_impact["details"].append(f"**{t_name}**: +{boost:.1f}%")
                    ban_impact["total_boost"] += boost
                
                if ban_impact["total_boost"] > 0:
                    results.append(ban_impact)

            # Xuất kết quả
            top_3 = sorted(results, key=lambda x: x['total_boost'], reverse=True)[:3]
            
            if not top_3:
                st.info("Không tìm thấy phương án Ban nào tối ưu hơn.")
            for i, res in enumerate(top_3):
                with st.expander(f"Top {i+1}: BAN {res['name']} (Tổng tăng: {res['total_boost']:.1f}%)"):
                    for d in res['details']:
                        st.write(d)
except Exception as e:
    st.error(f"Lỗi đọc file data.csv: {e}")