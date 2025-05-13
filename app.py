import streamlit as st
import pandas as pd
import plotly.express as px

@st.cache_data
def load_data():
    return pd.read_csv("public_library_data.csv")

df = load_data()

st.title("📚 대한민국 공공도서관 위치 지도")

# -------------------- 대한민국 전체 지도용 selectbox --------------------
sido_list = sorted(df["시도명"].dropna().unique())
selected_sido = st.sidebar.selectbox("🗺️ [대한민국 지도용] 시/도 선택", ["전체"] + sido_list)

if selected_sido != "전체":
    filtered_df_map = df[df["시도명"] == selected_sido]
else:
    filtered_df_map = df

st.subheader(f"📍 '{selected_sido}' 지역 도서관 지도 (대한민국 전체 기준)")

if not filtered_df_map.empty:
    fig_map = px.scatter_mapbox(
        filtered_df_map,
        lat="위도",
        lon="경도",
        color_discrete_sequence=["blue"],
        hover_name="도서관명",
        hover_data={"위도": False, "경도": False, "주소": True, "도서관유형": True},
        zoom=5 if selected_sido == "전체" else 8,
        height=600
    )

    fig_map.update_layout(
        mapbox_style="open-street-map",
        mapbox_center={"lat": 36.5, "lon": 127.8},
        margin={"r": 0, "t": 0, "l": 0, "b": 0}
    )

    st.plotly_chart(fig_map, use_container_width=True)
else:
    st.warning("선택한 지역에 해당하는 도서관 정보가 없습니다.")

# -------------------- 구분선 --------------------
st.divider()

# -------------------- 복합 필터 지도 --------------------
st.sidebar.markdown("---")
st.sidebar.header("🔎 상세 조건 필터")
sido_multi = st.sidebar.multiselect("시/도 필터", sorted(df["시도명"].dropna().unique()), default=df["시도명"].unique())
gubun = st.sidebar.multiselect("도서관 유형", sorted(df["도서관유형"].dropna().unique()), default=df["도서관유형"].unique())
year_range = st.sidebar.slider("개관년도 범위", int(df["개관년도"].min()), int(df["개관년도"].max()), (2000, 2024))

filtered_df_full = df[
    (df["시도명"].isin(sido_multi)) &
    (df["도서관유형"].isin(gubun)) &
    (df["개관년도"] >= year_range[0]) &
    (df["개관년도"] <= year_range[1])
]

st.subheader(f"📊 상세 조건에 따른 도서관 지도 (총 {len(filtered_df_full)}개)")

if not filtered_df_full.empty:
    fig_full = px.scatter_mapbox(
        filtered_df_full,
        lat="위도",
        lon="경도",
        color="시도명",
        hover_name="도서관명",
        hover_data=["도서관유형", "주소"],
        zoom=5,
        height=600
    )

    fig_full.update_layout(
        mapbox_style="open-street-map",
        margin={"r": 0, "t": 0, "l": 0, "b": 0}
    )

    st.plotly_chart(fig_full, use_container_width=True)
else:
    st.info("선택한 조건에 해당하는 도서관이 없습니다.")
