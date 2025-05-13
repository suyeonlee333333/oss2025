import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# CSV 파일 불러오기
df = pd.read_csv("night_pharmacy1.csv", encoding="utf-8-sig")

# 위도/경도 값이 없는 행 제거
df = df.dropna(subset=["위도", "경도"])

# 사이드바 - 구 선택
districts = sorted(df["관리지역"].unique())
selected_district = st.sidebar.selectbox("구를 선택하세요", districts)

# 선택한 구의 약국 필터링
filtered_df = df[df["관리지역"] == selected_district]

# 지도 중심 위치 설정 (기본은 부산 중심 좌표)
if not filtered_df.empty:
    center_lat = filtered_df["위도"].mean()
    center_lon = filtered_df["경도"].mean()
else:
    center_lat, center_lon = 35.1796, 129.0756  # 부산 중심

# Folium 지도 생성
m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

# 약국 마커 추가
for _, row in filtered_df.iterrows():
    name = row["약국명"]
    address = row["소재지(도로명)"]
    phone = row["전화번호"]
    lat = row["위도"]
    lon = row["경도"]
    
    popup_text = f"{name}<br>{address}<br>{phone}"
    folium.Marker([lat, lon], popup=popup_text).add_to(m)

# Streamlit에 지도 표시
st.title("💊 부산 심야약국 위치 지도")
st.write(f"선택한 지역: **{selected_district}**")
st_folium(m, width=700, height=500)
for index, row in filtered_df.iterrows():
    popup_text = f"{row['약국명']}<br>{row['소재지(도로명)']}<br>{row['전화번호']}"
    folium.Marker(
        [row['위도'], row['경도']],
        popup=folium.Popup(popup_text, max_width=300)  # 여기 max_width 설정이 핵심!
    ).add_to(m)

# 선택한 약국 표 표시
st.write("### 📋 약국 목록")
st.dataframe(filtered_df[["약국명", "소재지(도로명)", "전화번호"]].reset_index(drop=True))
