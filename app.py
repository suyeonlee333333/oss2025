import streamlit as st
import pandas as pd
import folium
from folium import plugins
import geopandas as gpd
from geopy.geocoders import Nominatim

# CSV 파일을 읽을 때 인코딩을 지정하여 문제 해결
df = pd.read_csv("night_pharmacy.csv", encoding="utf-8-sig")  # 혹은 "ISO-8859-1" 또는 "latin1"을 시도할 수 있음

# CSV 파일 불러오기
df = pd.read_csv("night_pharmacy.csv")

# Streamlit 앱 설정
st.title("부산시 심야 약국 지도")
st.markdown("### 구 선택")

# 구 리스트 가져오기
districts = df['소재지(도로명)'].apply(lambda x: x.split()[0]).unique()
selected_district = st.selectbox("구를 선택하세요", districts)

# 구에 해당하는 데이터 필터링
district_data = df[df['소재지(도로명)'].str.contains(selected_district)]

# 지도 생성
m = folium.Map(location=[district_data['위도'].mean(), district_data['경도'].mean()], zoom_start=12)

# 약국 마커 추가
for idx, row in district_data.iterrows():
    folium.Marker([row['위도'], row['경도']], 
                  popup=f"약국명: {row['약국명']}<br>전화번호: {row['전화번호']}<br>관리지역: {row['관리지역']}",
                  icon=folium.Icon(color="blue")).add_to(m)

# 지도를 HTML로 렌더링
st.markdown("### 심야 약국 위치")
st.components.v1.html(m._repr_html_(), height=500)

# 필터링된 데이터 테이블 보여주기
st.markdown("### 선택한 구의 약국 리스트")
st.write(district_data[['약국명', '소재지(도로명)', '전화번호', '관리지역']])
