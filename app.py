import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# -------------------- 데이터 로드 --------------------
@st.cache_data
def load_data():
    df = pd.read_csv("library_data.csv")
    df['평가년도'] = pd.to_datetime(df['평가년도'], format='%Y')
    return df

df = load_data()

# -------------------- UI --------------------
st.title("📚 대한민국 공공도서관 분석")

# -------------------- 행정구역 필터 (다중 선택) --------------------
district_list = sorted(df['행정구역'].dropna().unique())
selected_districts = st.sidebar.multiselect("🔎 행정구역 선택 (다중 선택 가능)", district_list, default=[district_list[0]])

# 선택된 지역 데이터 필터링
filtered_df = df[df['행정구역'].isin(selected_districts)]

# -------------------- 사용자 정의 지표 계산 --------------------
filtered_df['이용률 점수'] = (
    filtered_df['대출권수'] / (filtered_df['장서수(인쇄)'] + 1) +
    filtered_df['대출자수'] / (filtered_df['사서수'] + 1)
)

# -------------------- 전체 비교 분석 --------------------
st.subheader("📊 선택된 행정구역 비교 분석")

# 1. 도서관 수 비교
library_counts = filtered_df.groupby('행정구역')['도서관명'].nunique()
st.bar_chart(library_counts.rename("도서관 수"))

# 2. 평균 사용자 정의 지표 비교
score_avg = filtered_df.groupby('행정구역')['이용률 점수'].mean().sort_values()
st.subheader("⚖️ 지역별 평균 이용률 점수 비교")
st.bar_chart(score_avg)

# -------------------- 단일 지역일 경우 상세 분석 --------------------
if len(selected_districts) == 1:
    district = selected_districts[0]
    district_df = filtered_df[filtered_df['행정구역'] == district]

    st.subheader(f"📍 {district} 지역 공공도서관 상세 분석")

    # 도서관 개수
    library_count = district_df['도서관명'].nunique()
    st.write(f"🎉 {district} 지역에는 총 {library_count}개의 도서관이 있습니다.")

    # 도서관 이름
    st.write("📚 도서관 이름 목록:")
    for name in district_df['도서관명'].unique():
        st.write(f"- {name}")

    # 연도별 대출자 수
    st.subheader("연도별 대출자 수 변화")
    yearly_borrowers = district_df.groupby("평가년도")['대출자수'].sum()
    st.line_chart(yearly_borrowers)

    # 대출자 수 vs 도서 예산
    st.subheader("도서관별 대출자수 vs 도서 예산")
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=district_df, x='대출자수', y='도서예산(자료구입비)', hue='도서관구분')
    plt.title(f'{district} 도서관별 대출자수 vs 도서 예산')
    st.pyplot()
