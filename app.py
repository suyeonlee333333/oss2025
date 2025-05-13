import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# CSV 파일 불러오기 (인코딩 오류가 나면 encoding을 "cp949"로 바꿔보세요)
df = pd.read_csv("night_pharmacy.csv", encoding="utf-8-sig")

# 관리지역에서 '구' 이름만 추출해서 새로운 컬럼으로 저장
df['구'] = df['관리지역'].str.extract(r'([가-힣]+구)')

# 구 목록 만들기
구_목록 = df['구'].dropna().unique()
구_선택 = st.selectbox("부산시 내 구를 선택하세요", sorted(구_목록))

# 선택된 구의 약국 데이터 필터링
df_filtered = df[df['구'] == 구_선택]

# ✅ 지도 중심 좌표 설정 (기본은 부산 중심)
location = [35.1796, 129.0756]  # ← 여기를 원하는 좌표로 바꿔도 됩니다!

# 지도 생성
map = folium.Map(location=location, zoom_start=13)

# 선택된 구의 약국 위치를 지도에 마커로 추가
for idx, row in df_filtered.iterrows():
    if pd.notna(row['위도']) and pd.notna(row['경도']):
        folium.Marker(
            [row['위도'], row['경도']],
            popup=f"{row['약국명']}<br>{row['소재지(도로명)']}<br>{row['전화번호']}"
        ).add_to(map)

# Streamlit에 지도 출력
st_folium(map, width=700, height=500)
