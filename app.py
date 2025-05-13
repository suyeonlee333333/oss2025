import folium
import pandas as pd
import streamlit as st

# 데이터 불러오기
df = pd.read_csv("night_pharmacy1.csv", encoding="utf-8-sig")

# 구 이름 추출
df['구'] = df['관리지역'].str.extract(r'([가-힣]+구)')
구_목록 = df['구'].dropna().unique()

# Streamlit에서 구 선택
구_선택 = st.selectbox('구 선택', 구_목록)

# 선택한 구에 해당하는 데이터 필터링
df_선택_구 = df[df['구'] == 구_선택]

# 지도 생성
map = folium.Map(location=[35.1796, 129.0756], zoom_start=12)  # 부산 중심 좌표

# 선택한 구에 대한 마커 추가
for idx, row in df_선택_구.iterrows():
    lat = row['위도'] if pd.notna(row['위도']) else 0
    lon = row['경도'] if pd.notna(row['경도']) else 0
    folium.Marker([lat, lon], popup=row['약국명']).add_to(map)

# 지도 표시
st.write(map)
