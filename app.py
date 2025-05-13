import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# CSV 파일 불러오기
df = pd.read_csv("night_pharmacy1.csv", encoding="utf-8-sig")
df = df.dropna(subset=["위도", "경도"])  # 위도/경도 값 없는 행 제거

# 앱 제목
st.title("💊 부산 심야약국 위치 지도")

# ---------------------------
# 🔍 약국 검색 기능 (지도보다 위에 위치)
# ---------------------------
st.subheader("🔍 약국명으로 검색")

search_term = st.text_input("약국명을 입력하세요:")

if search_term:
    filtered_search = df[df["약국명"].str.contains(search_term, case=False, na=False)]
    if not filtered_search.empty:
        st.success(f"{len(filtered_search)}개 약국이 검색되었습니다.")
        
        # 검색된 약국 지도
        center_lat = filtered_search["위도"].mean()
        center_lon = filtered_search["경도"].mean()
        m_search = folium.Map(location=[center_lat, center_lon], zoom_start=13)

        for _, row in filtered_search.iterrows():
            popup_text = f"{row['약국명']}<br>{row['소재지(도로명)']}<br>{row['전화번호']}"
            folium.Marker([row["위도"], row["경도"]], popup=popup_text).add_to(m_search)

        st_folium(m_search, width=700, height=500)
        st.write("### 📋 검색된 약국 목록")
        st.dataframe(filtered_search[["약국명", "소재지(도로명)", "전화번호"]].reset_index(drop=True))
    else:
        st.warning("검색 결과가 없습니다.")

# ---------------------------
# 📍 구 선택 버튼 (지도 아래)
# ---------------------------
st.subheader("📍 지역별 약국 보기")

districts = sorted(df["관리지역"].unique())

# 버튼 누르면 해당 구 필터링
selected_district = None
cols = st.columns(4)  # 4열로 버튼 나열

for i, district in enumerate(districts):
    if cols[i % 4].button(district):
        selected_district = district

# ---------------------------
# 🗺️ 지도 표시 (구 선택 시)
# ---------------------------
if selected_district:
    st.markdown(f"### 🏙️ 선택한 지역: **{selected_district}**")

    filtered_df = df[df["관리지역"] == selected_district]
    center_lat = filtered_df["위도"].mean()
    center_lon = filtered_df["경도"].mean()

    m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

    for _, row in filtered_df.iterrows():
        popup_text = f"{row['약국명']}<br>{row['소재지(도로명)']}<br>{row['전화번호']}"
        folium.Marker([row["위도"], row["경도"]], popup=popup_text).add_to(m)

    st_folium(m, width=700, height=500)
    st.write("### 📋 약국 목록")
    st.dataframe(filtered_df[["약국명", "소재지(도로명)", "전화번호"]].reset_index(drop=True))
else:
    st.markdown("💡 지역 버튼을 눌러 심야약국 위치를 확인하세요.")
