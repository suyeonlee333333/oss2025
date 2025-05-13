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

# 전체 부산시 심야약국 지도를 먼저 표시
st.title("💊 부산 심야약국 위치 지도")

# 전체 지도의 중심 위치 설정 (기본은 부산 중심 좌표)
center_lat, center_lon = 35.1796, 129.0756  # 부산 중심

# Folium 지도 생성 (전체 부산시)
m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

# 전체 심야약국 마커 추가
for _, row in df.iterrows():
    name = row["약국명"]
    address = row["소재지(도로명)"]
    phone = row["전화번호"]
    lat = row["위도"]
    lon = row["경도"]

    popup_text = f"{name}<br>{address}<br>{phone}"
    folium.Marker([lat, lon], popup=popup_text).add_to(m)

# Streamlit에 전체 부산시 지도 표시
st_folium(m, width=700, height=500)

# 약국 검색 기능
search_term = st.text_input("검색할 약국명을 입력하세요:")

# 약국 검색 결과 필터링
if search_term:
    filtered_search = df[df["약국명"].str.contains(search_term, case=False, na=False)]  # 대소문자 구분 없이 검색
    if not filtered_search.empty:
        st.write(f"**검색 결과**: {len(filtered_search)}개 약국이 검색되었습니다.")
        # 검색된 약국의 지도 표시
        m_search = folium.Map(location=[center_lat, center_lon], zoom_start=12)

        for _, row in filtered_search.iterrows():
            name = row["약국명"]
            address = row["소재지(도로명)"]
            phone = row["전화번호"]
            lat = row["위도"]
            lon = row["경도"]

            popup_text = f"{name}<br>{address}<br>{phone}"
            folium.Marker([lat, lon], popup=popup_text).add_to(m_search)

        # Streamlit에 검색된 약국 지도 표시
        st_folium(m_search, width=700, height=500)
        
        # 검색된 약국 목록 표시
        st.write("### 📋 검색된 약국 목록")
        st.dataframe(filtered_search[["약국명", "소재지(도로명)", "전화번호"]].reset_index(drop=True))
    else:
        st.write("**검색 결과가 없습니다.**")

# 선택한 구의 약국 필터링
filtered_df = df[df["관리지역"] == selected_district]

# 선택한 구의 지도
if not filtered_df.empty:
    # 선택된 구의 중심 좌표로 지도 업데이트
    center_lat = filtered_df["위도"].mean()
    center_lon = filtered_df["경도"].mean()
else:
    center_lat, center_lon = 35.1796, 129.0756  # 기본 부산 중심

# 선택된 구의 지도 생성
m_filtered = folium.Map(location=[center_lat, center_lon], zoom_start=13)

# 선택된 구의 약국 마커 추가
for _, row in filtered_df.iterrows():
    name = row["약국명"]
    address = row["소재지(도로명)"]
    phone = row["전화번호"]
    lat = row["위도"]
    lon = row["경도"]

    popup_text = f"{name}<br>{address}<br>{phone}"
    folium.Marker([lat, lon], popup=popup_text).add_to(m_filtered)

# Streamlit에 선택한 구의 지도 표시
st.write(f"선택한 지역: **{selected_district}**")
st_folium(m_filtered, width=700, height=500)

# 선택한 구의 약국 목록 표시
st.write("### 📋 약국 목록")
st.dataframe(filtered_df[["약국명", "소재지(도로명)", "전화번호"]].reset_index(drop=True))
