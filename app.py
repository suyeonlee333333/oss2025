import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# -------------------- 데이터 로드 --------------------
@st.cache_data  # st.cache 대신 st.cache_data 사용
def load_data():
    df = pd.read_csv("library_data.csv")
    df['평가년도'] = pd.to_datetime(df['평가년도'], format='%Y')
    return df

df = load_data()

# -------------------- UI --------------------
st.title("📚 대한민국 공공도서관 분석")

# -------------------- 행정구역 필터 --------------------
# 행정구역 목록 가져오기
district_list = sorted(df['행정구역'].dropna().unique())

# 행정구역 선택
selected_district = st.sidebar.selectbox("🔎 행정구역 선택", district_list)

# 행정구역 선택에 따라 데이터 필터링
filtered_df = df[df['행정구역'] == selected_district]

# -------------------- 행정구역별 분석 --------------------
st.subheader(f"📍 {selected_district} 지역 공공도서관 분석")

# 1. 도서관 유형별 장서 수
st.subheader("도서관 유형별 장서 수")
library_type_chart = filtered_df.groupby("도서관구분")['장서수(인쇄)'].sum().sort_values(ascending=False)
st.bar_chart(library_type_chart)

# 2. 연도별 대출자 수 변화
st.subheader("연도별 대출자 수 변화")
yearly_borrowers = filtered_df.groupby("평가년도")['대출자수'].sum()
st.line_chart(yearly_borrowers)

# 3. 도서관별 대출자수 vs 도서 예산
st.subheader("도서관별 대출자수 vs 도서 예산")
plt.figure(figsize=(10, 6))
sns.scatterplot(data=filtered_df, x='대출자수', y='도서예산(자료구입비)', hue='도서관구분')
plt.title(f'{selected_district} 도서관별 대출자수 vs 도서 예산')
st.pyplot()

# 4. 도서관별 사서 수
st.subheader("도서관별 사서 수")
library_staff = filtered_df.groupby("도서관명")['사서수'].sum().sort_values(ascending=False)
st.bar_chart(library_staff)
