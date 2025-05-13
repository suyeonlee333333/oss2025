import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

def load_data():
    try:
        # 'utf-8' 대신 다른 인코딩 사용
        df = pd.read_csv("pharmacy.csv", encoding="latin1", dtype=str)
    except UnicodeDecodeError:
        # 추가적인 인코딩 시도
        df = pd.read_csv("pharmacy.csv", encoding="ISO-8859-1", dtype=str)
    
    df.columns = df.columns.str.strip()  # 열 이름 공백 제거
    df['시도'] = df['도로명전체주소'].str.extract(r'^(\S+?[시도])')
    df['좌표정보x'] = pd.to_numeric(df['좌표정보x'], errors='coerce')
    df['좌표정보y'] = pd.to_numeric(df['좌표정보y'], errors='coerce')
    df = df.dropna(subset=['좌표정보x', '좌표정보y'])
    return df


df = load_data()

# 🎯 타이틀
st.title("💊 전국 약국 정보 지도")
st.markdown("지역과 영업상태를 선택해 약국을 지도에서 확인하세요.")

# 🗺️ 지역(시도) 필터
regions = df['시도'].dropna().unique()
selected_regions = st.multiselect("📍 지역 선택 (시/도)", sorted(regions), default=regions[:1])

# 🔄 영업 상태 필터
status_options = df['영업상태명'].dropna().unique()
selected_status = st.multiselect("🏪 영업 상태 선택", status_options, default=["영업중"])

# 🔎 필터링
filtered_df = df[df['시도'].isin(selected_regions) & df['영업상태명'].isin(selected_status)]

# 📊 필터 결과 요약
st.write(f"🔎 선택된 약국 수: {len(filtered_df)}")

# ❌ 필터 결과가 없을 때
if filtered_df.empty:
    st.warning("해당 조건에 맞는 약국이 없습니다.")
else:
    # 📍 지도 중심 좌표
    map_center = [filtered_df['좌표정보y'].mean(), filtered_df['좌표정보x'].mean()]
    m = folium.Map(location=map_center, zoom_start=12)

    # 📌 약국 마커 추가
    for _, row in filtered_df.iterrows():
        popup_text = f"""
        <b>{row['사업장명']}</b><br>
        전화: {row['소재지전화'] or '정보 없음'}<br>
        주소: {row['도로명전체주소']}
        """
        folium.Marker(
            [row['좌표정보y'], row['좌표정보x']],
            popup=popup_text,
            icon=folium.Icon(color="blue", icon="plus-sign")
        ).add_to(m)

    # 지도 출력
    st_folium(m, width=800, height=600)
