import streamlit as st
import pandas as pd
import pydeck as pdk
import numpy as np

# -------------------- 데이터 로드 --------------------
@st.cache_data
def load_data():
    df = pd.read_csv("library_data.csv")  # 데이터 파일 경로 맞게 수정
    df = df.dropna(subset=['위도', '경도'])
    df['위도'] = df['위도'].astype(float)
    df['경도'] = df['경도'].astype(float)
    df['평가년도'] = pd.to_datetime(df['평가년도'], errors='coerce')
    return df

df = load_data()

# -------------------- UI --------------------
st.title("📚 전국 공공도서관 정보")

# 날짜 필터 (평가년도)
date_range = st.date_input("평가년도 범위", [df['평가년도'].min().date(), df['평가년도'].max().date()])

# 지역 필터 (행정구역)
광역시도_목록 = sorted(df['행정구역'].dropna().unique())
selected_regions = st.multiselect("광역시/도 선택", 광역시도_목록)

# 도서관 구분 필터
library_type_목록 = sorted(df['도서관구분'].dropna().unique())
selected_types = st.multiselect("도서관 구분 선택", library_type_목록)

# -------------------- 필터링 --------------------
filtered = df[
    (df['평가년도'].dt.date >= date_range[0]) & (df['평가년도'].dt.date <= date_range[1])
]

if selected_regions:
    filtered = filtered[filtered['행정구역'].isin(selected_regions)]

if selected_types:
    filtered = filtered[filtered['도서관구분'].isin(selected_types)]

# -------------------- 요약 통계 --------------------
st.subheader("도서관 정보 요약")
col1, col2, col3, col4 = st.columns(4)
if not filtered.empty:
    col1.metric("도서관 수", len(filtered))
    col2.metric("평균 장서 수", f"{filtered['장서수(인쇄)'].mean():,.0f}")
    col3.metric("평균 대출자수", f"{filtered['대출자수'].mean():,.0f}")
    col4.metric("평균 도서예산", f"{filtered['도서예산(자료구입비)'].mean():,.0f}")

    top_region = filtered['행정구역'].value_counts().idxmax()
    st.markdown(f"**가장 많은 도서관이 있는 지역:** {top_region}")
else:
    st.warning("선택한 조건에 해당하는 도서관 데이터가 없습니다.")

# -------------------- 도서관 평가년도 변화 라인 차트 --------------------
st.subheader("도서관 개관년도 변화 추이")
if not filtered.empty:
    line_data = filtered.sort_values("평가년도")[['평가년도', '장서수(인쇄)']]
    st.line_chart(line_data.rename(columns={'평가년도': 'index'}).set_index('index'))

# -------------------- 지도 시각화 --------------------
st.subheader("도서관 위치")
if not filtered.empty:
    map_data = filtered.rename(columns={'위도': 'latitude', '경도': 'longitude'})
    map_data['평가년도'] = map_data['평가년도'].dt.strftime('%Y-%m-%d')

    def library_size_to_color(size):
        if size <= 10000:
            return [0, 255, 0, 140]  # 작은 도서관: 초록색
        elif size <= 50000:
            return [255, 165, 0, 140]  # 중간 도서관: 주황색
        else:
            return [255, 0, 0, 160]  # 큰 도서관: 빨간색

    map_data['color'] = map_data['장서수(인쇄)'].apply(library_size_to_color)

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_data,
        get_position='[longitude, latitude]',
        get_radius='장서수(인쇄) * 0.1',  # 장서 수에 따라 크기 조정
        get_fill_color='color',
        pickable=True
    )

    view_state = pdk.ViewState(
        latitude=map_data['latitude'].mean(),
        longitude=map_data['longitude'].mean(),
        zoom=6
    )

    st.pydeck_chart(pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        initial_view_state=view_state,
        layers=[layer],
        tooltip={"text": "{도서관명}\n장서수: {장서수(인쇄)}\n평가년도: {평가년도}\n{행정구역}"}
    ))

