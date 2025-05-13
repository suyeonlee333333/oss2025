import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 데이터 로드 함수
@st.cache
def load_data():
    # 데이터 로드 (CSV 파일로 가정)
    df = pd.read_csv("library_data.csv")
    return df

# 데이터 로드
df = load_data()

# -------------------- UI --------------------
st.title("📚 전국 공공도서관 정보 분석")

# 도서관 유형 필터
library_types = st.sidebar.multiselect("도서관 유형 선택", df["도서관구분"].unique(), default=df["도서관구분"].unique())

# 데이터 필터링
filtered_df = df[df["도서관구분"].isin(library_types)]

# -------------------- 도서관 유형별 분석 --------------------
st.subheader("도서관 유형별 장서 수")
library_type_count = filtered_df.groupby("도서관구분")["장서수(인쇄)"].sum().sort_values()

fig, ax = plt.subplots()
library_type_count.plot(kind="bar", ax=ax, color='skyblue')
ax.set_title("도서관 유형별 장서 수")
ax.set_ylabel("장서 수")
st.pyplot(fig)

# -------------------- 도서관 유형별 대출자 수 --------------------
st.subheader("도서관 유형별 대출자 수")
library_type_borrowers = filtered_df.groupby("도서관구분")["대출자수"].sum().sort_values()

fig2, ax2 = plt.subplots()
library_type_borrowers.plot(kind="bar", ax=ax2, color='salmon')
ax2.set_title("도서관 유형별 대출자 수")
ax2.set_ylabel("대출자 수")
st.pyplot(fig2)

# -------------------- 도서관 연도별 장서 수 변화 --------------------
st.subheader("도서관 개관 연도별 장서 수 변화")
yearly_data = filtered_df.groupby("평가년도")["장서수(인쇄)"].sum()

fig3, ax3 = plt.subplots()
yearly_data.plot(kind="line", ax=ax3, marker='o', color='green')
ax3.set_title("개관 연도별 장서 수 변화")
ax3.set_ylabel("장서 수")
ax3.set_xlabel("평가 연도")
st.pyplot(fig3)

# -------------------- 도서관 연도별 대출자 수 변화 --------------------
st.subheader("도서관 개관 연도별 대출자 수 변화")
yearly_borrowers = filtered_df.groupby("평가년도")["대출자수"].sum()

fig4, ax4 = plt.subplots()
yearly_borrowers.plot(kind="line", ax=ax4, marker='o', color='purple')
ax4.set_title("개관 연도별 대출자 수 변화")
ax4.set_ylabel("대출자 수")
ax4.set_xlabel("평가 연도")
st.pyplot(fig4)

# -------------------- 도서관 통계 출력 --------------------
st.subheader("도서관 평균 통계")
avg_stats = filtered_df[["장서수(인쇄)", "대출자수", "사서수"]].mean()

st.write(f"평균 장서 수: {avg_stats['장서수(인쇄)']:.0f}")
st.write(f"평균 대출자 수: {avg_stats['대출자수']:.0f}")
st.write(f"평균 사서 수: {avg_stats['사서수']:.0f}")
