import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# CSV 파일 불러오기
df = pd.read_csv("night_pharmacy1.csv", encoding="utf-8-sig")
df = df.dropna(subset=["위도", "경도"])

# 앱 제목
st.title("💊 부산 심야약국 위치 지도")

# 🔍 약국 검색
st.subheader("🔍 약국명 검색")
search_term = st.text_input("약국명을 입력하세요:")

if search_term:
    filtered_search = df[df["약국명"].str.contains(search_term, case=False, na=False)]
    if not filtered_search.empty:
        st.success(f"{len(filtered_search)}개 약국이 검색되었습니다.")
        center_lat = filtered_search["위도"].mean()
        center_lon = filtered_search["경도"].mean()
        m_search = folium.Map(location=[center_lat, center_lon], zoom_start=13)

        for _, row in filtered_search.iterrows():
            popup_text = f"{row['약국명']}<br>{row['소재지(도로명)']}<br>{row['전화번호']}"
            folium.Marker([row["위도"], row["경도"]], popup=popup_text).add_to(m_search)

        st_folium(m_search, width=700, height=500)
        st.markdown("**📋 검색된 약국 목록**")
        st.dataframe(filtered_search[["약국명", "소재지(도로명)", "전화번호"]].reset_index(drop=True))
    else:
        st.warning("검색 결과가 없습니다.")

# 📍 구 선택
st.subheader("📍 지역별 약국 보기")

districts = sorted(df["관리지역"].unique())

# 세션 상태 초기화
if "selected_district" not in st.session_state:
    st.session_state.selected_district = None

# 구 버튼 나열
cols = st.columns(4)
for i, district in enumerate(districts):
    if cols[i % 4].button(district):
        st.session_state.selected_district = district

selected_district = st.session_state.selected_district

# 선택된 구 처리
if selected_district:
    st.markdown(f"### 🏙️ 선택한 지역: **{selected_district}**")

    # 관리지역 필터 (부분 포함)
    filtered_df = df[df["관리지역"].str.contains(selected_district, na=False)]

    if not filtered_df.empty:
        center_lat = filtered_df["위도"].mean()
        center_lon = filtered_df["경도"].mean()

        m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

        for _, row in filtered_df.iterrows():
            popup_text = f"{row['약국명']}<br>{row['소재지(도로명)']}<br>{row['전화번호']}"
            folium.Marker([row["위도"], row["경도"]], popup=popup_text).add_to(m)

        # 지도 출력
        st_folium(m, width=700, height=500)

        # 💡 지도 아래 여백 줄이기 위한 CSS
        st.markdown(
            """
            <style>
            .element-container:has(.folium-map) + .element-container {
                margin-top: -30px !important;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        # 📋 약국 목록
        st.markdown("**📋 약국 목록**")
        st.dataframe(filtered_df[["약국명", "소재지(도로명)", "전화번호"]].reset_index(drop=True))
    else:
        st.warning("해당 지역에 약국 데이터가 없습니다.")
else:
    st.info("💡 지역 버튼을 눌러 심야약국 위치를 확인하세요.")
