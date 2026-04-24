import streamlit as st
import pandas as pd

# 1. Tỉ lệ Roll
roll_rates = {
    5: {1: 45, 2: 35, 3: 18, 4: 2},
    6: {1: 30, 2: 40, 3: 25, 4: 5},
    7: {1: 25, 2: 30, 3: 35, 4: 10},
    8: {1: 20, 2: 28, 3: 35, 4: 16},
    9: {1: 20, 2: 25, 3: 27, 4: 25},
    10: {1: 15, 2: 25, 3: 25, 4: 29},
    11: {1: 15, 2: 20, 3: 20, 4: 36}
}

# Cấu hình giao diện cực gọn
st.set_page_config(page_title="AC Ban Tool", layout="centered")

# CSS để thu nhỏ font và khoảng cách trên Mobile
st.markdown("""
    <style>
    .block-container {padding-top: 1rem; padding-bottom: 0rem;}
    h1 {font-size: 1.5rem !important; text-align: center;}
    .stSelectbox label, .stMultiSelect label {display: none;} /* Ẩn nhãn để tiết kiệm chỗ */
    div[data-testid="stExpander"] {margin-top: -10px;}
    </style>
    """, unsafe_allow_html=True)

st.title("🧙‍♂️ AC BAN TOOL")

try:
    df = pd.read_csv("data.csv")
    
    def get_unique(dataframe, col):
        elements = set()
        for val in dataframe[col].dropna():
            parts = [p.strip() for p in str(val).split(',')]
            elements.update(parts)
        return sorted([e for e in elements if e and e != 'None'])

    all_races = get_unique(df, 'Tộc (Race)')
    all_classes = get_unique(df, 'Hệ (Class)')
    all_syns = sorted(list(set(all_races + all_classes)))

    # --- HÀNG 1: LEVEL & PLAYING ---
    col_l, col_p = st.columns([1, 2])
    level = col_l.selectbox("L", list(roll_rates.keys()), index=3, help="Level")
    playing = col_p.multiselect("P", all_syns, placeholder="Hệ đang chơi")

    # --- HÀNG 2: BỘ LỌC TƯỚNG ---
    col_f1, col_f2 = st.columns(2)
    f_race = col_f1.selectbox("R", ["Tộc: Tất cả"] + all_races)
    f_class = col_f2.selectbox("C", ["Hệ: Tất cả"] + all_classes)

    # Logic lọc
    f_df = df.copy()
    if f_race != "Tộc: Tất cả": f_df = f_df[f_df['Tộc (Race)'].str.contains(f_race, na=False)]
    if f_class != "Hệ: Tất cả": f_df = f_df[f_df['Hệ (Class)'].str.contains(f_class, na=False)]

    # --- CHỌN TƯỚNG ---
    targets = st.multiselect("T", f_df['Tên quân cờ'].unique(), placeholder="Chọn tướng mục tiêu")

    if targets:
        # Lọc Pool
        mask = (~df['Tộc (Race)'].str.contains('Egersis', na=False)) & \
               (~df['Hệ (Class)'].str.contains('Egersis', na=False)) & \
               ~((df['Tộc (Race)'].str.contains('Pandaren', na=False)) & (df['Giá (Gold)'] > 2))
        df_active = df[mask].copy()
        pool_counts = df_active['Giá (Gold)'].value_counts().to_dict()

        results = []
        for syn in all_syns:
            if syn in playing or syn == "Egersis": continue
            
            mask_ban = df_active['Tộc (Race)'].str.contains(syn, na=False) | df_active['Hệ (Class)'].str.contains(syn, na=False)
            banned_units = df_active[mask_ban]
            
            if any(u in banned_units['Tên quân cờ'].values for u in targets): continue
            
            impact = {"name": syn, "txt": [], "val": 0}
            for t_name in targets:
                t_row = df_active[df_active['Tên quân cờ'] == t_name]
                if t_row.empty: continue
                cost = t_row['Giá (Gold)'].values[0]
                if cost >= 5: continue
                    
                removed = len(banned_units[banned_units['Giá (Gold)'] == cost])
                if removed > 0:
                    rate = roll_rates[level][cost] / 100
                    p_old = rate / pool_counts[cost]
                    p_new = rate / (pool_counts[cost] - removed)
                    
                    # XS 1 lượt (5 ô)
                    r_old, r_new = 1-(1-p_old)**5, 1-(1-p_new)**5
                    boost = (p_new/p_old - 1) * 100
                    impact["txt"].append(f"**{t_name}**: {r_old:.1%} → **{r_new:.1%}**")
                    impact["val"] += boost
            
            if impact["val"] > 0: results.append(impact)

        # Hiển thị Top 3 gọn nhất
        top = sorted(results, key=lambda x: x['val'], reverse=True)[:3]
        for i, res in enumerate(top):
            with st.expander(f"Top {i+1}: Ban **{res['name']}** (+{res['val']:.1f}%)", expanded=True):
                for t in res["txt"]: st.write(t)
    else:
        st.info("Chọn tướng để thấy kết quả")

except Exception as e:
    st.error(f"Lỗi: {e}")
