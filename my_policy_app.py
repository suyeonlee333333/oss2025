# my_policy_app.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# 1. 데이터 불러오기
@st.cache_data
def load_data():
    return pd.read_csv('results_df.csv', parse_dates=['YearMonth'])

df = load_data()

st.title("🚇 무임승차 연령 기준 조정에 따른 손실 분석")
st.markdown("특정 월을 기준으로 무임승차 연령 기준을 조정할 때 발생하는 손실을 시각화하고, 정책적으로 가장 유리한 기준을 제안합니다.")

# 2. 사용자 선택 - 분석할 월
available_months = df['YearMonth'].dt.strftime('%Y-%m').sort_values().unique()
selected_month = st.selectbox("📅 분석할 월을 선택하세요:", available_months)

# 3. 선택된 월 기준 데이터 필터링
selected_date = pd.to_datetime(selected_month + "-01")
filtered_df = df[df['YearMonth'] == selected_date]

if filtered_df.empty:
    st.warning("선택한 월의 데이터가 없습니다.")
else:
    # 4. 최적 연령 기준 계산 (총손실 최소)
    best_row = filtered_df.loc[filtered_df['EstimatedTotalLoss'].idxmin()]
    best_age = int(best_row['AgeThreshold'])
    min_loss = int(best_row['EstimatedTotalLoss'])

    st.subheader("📌 정책 제안")
    st.markdown(f"""
    - **분석 월**: {selected_month}  
    - **가장 낮은 총손실액을 기록한 연령 기준**: **{best_age}세**  
    - **예상 총손실액**: **{min_loss:,}백만원**
    """)

    # 5. 시각화
    st.subheader("📊 연령 기준별 손실 추이")

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(filtered_df['AgeThreshold'], filtered_df['EstimatedLoss'], label='Estimated Loss (백만원)', marker='o')
    ax.plot(filtered_df['AgeThreshold'], filtered_df['EstimatedTotalLoss'], label='Estimated Total Loss (백만원)', marker='s')
    ax.axvline(best_age, color='red', linestyle='--', label=f'최적 기준: {best_age}세')
    ax.set_title(f'{selected_month} 기준 연령 기준별 손실 추이')
    ax.set_xlabel('연령 기준')
    ax.set_ylabel('손실액 (백만원)')
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)
