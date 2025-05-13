# app.py

import streamlit as st
import pandas as pd

# 데이터 불러오기
try:
    df = pd.read_csv('library_data.csv')
except FileNotFoundError:
    st.error("❗ 데이터 파일을 찾을 수 없습니다. 'library_data.csv'가 현재 폴더에 있는지 확인해주세요.")
    st.stop()

# Streamlit 제목
st.title("📚 전국 공공도서관 정보")

# 필터: 행정구역(시도) 선택
region = st.selectbox("📍 지역(행정구역) 선택", sorted(df['행정구역'].dropna().unique()))
filtered_df = df[df['행정구역'] == region]

# 선택된 지역 정보 표시
st.write(f"🔍 선택된 지역: **{region}**")
st.write(f"📊 도서관 수: {filtered_df.shape[0]}개")

# 선택된 지역의 도서관 정보 출력
st.dataframe(
    filtered_df[['도서관명', '행정구역', '시군구', '장서수(인쇄)', '사서수', '대출자수', '대출권수', '도서예산(자료구입비)']]
)

# 도서관명 검색
search_term = st.text_input("🔎 도서관명으로 검색")

# 검색 기능
if search_term:
    search_result = df[df['도서관명'].str.contains(search_term, case=False, na=False)]
    if not search_result.empty:
        st.write(f"🔍 **'{search_term}'** 검색 결과:")
        st.dataframe(
            search_result[['도서관명', '행정구역', '시군구', '장서수(인쇄)', '사서수', '대출자수', '대출권수', '도서예산(자료구입비)']]
        )
    else:
        st.warning("검색 결과가 없습니다.")

