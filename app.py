import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# 데이터 로드
@st.cache_data
def load_data():
    df = pd.read_csv("pharmacy.csv", dtype=str)
    df['좌표정보x'] = pd.to_numeric(df['좌표정보x'], errors='coerce')
    df['좌표정보y'] = pd.to_numeric(df['좌표정보y'], errors='coerce')
    df = df.dropna(subset=['좌표정보x', '좌표정보y'])
    return df

df = load_data()

st.title("전국 약국 정보 지도")
st.markdown("지역을 선택하고, 영업 상태에 따라 약국을 필터링해보세요.")

# 지역 선택
all_regions = df['개방자치단체코드'].dropna().unique()
selected_regions = st.multiselect("지역 선택 (시/도 코드)", sorted(all_regions), default=all_regions[:1])

# 영업상태 선택
status_options = df['영업상태명'].unique()
selected_status = st.multiselect("영업상태 선택", status_options, default=['영업중'])

# 필터링
filtered_df = df[df['개방자치단체코드'].isin(selected_regions)]
filtered_df = filtered_df[filtered_df['영업상태명'].isin(selected_status)]

st.write(f"선택된 약국 수: {len(filtered_df)}")

# 지도 생성
map_center = [filtered_df['좌표정보y'].mean(), filtered_df['좌표정보x'].mean()]
m = folium.Map(location=map_center, zoom_start=12)

for _, row in filtered_df.iterrows():
    folium.Marker(
        [row['좌표정보y'], row['좌표정보x']],
        popup=f"""
        <b>{row['사업장명']}</b><br>
        전화: {row['소재지전화']}<br>
        주소: {row['도로명전체주소']}
        """
    ).add_to(m)

st_data = st_folium(m, width=800, height=600)
