import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

@st.cache_data
def load_data():
    # 1번 시트: 월별 무임승차 데이터
    df_ride = pd.read_excel('re_study_data.xlsx', sheet_name=0)
    # 2번 시트: 월별 인구 수 (연령별)
    df_pop = pd.read_excel('re_study_data.xlsx', sheet_name='월별 인구 수')
    
    # 월-연도 컬럼이 없으면 생성
    if 'YearMonth' not in df_ride.columns:
        df_ride['YearMonth'] = pd.to_datetime(df_ride[['연도', '월']].assign(일=1))
    if 'YearMonth' not in df_pop.columns:
        df_pop['YearMonth'] = pd.to_datetime(df_pop[['연도', '월']].assign(일=1))
    
    return df_ride, df_pop

df_ride, df_pop = load_data()

st.title("🚇 무임승차 연령 기준 조정 시 예상 손실 예측")

# 1) 월 선택
available_months = df_ride['YearMonth'].dt.strftime('%Y-%m').sort_values().unique()
selected_month = st.selectbox("📅 분석할 월 선택:", available_months)
selected_date = pd.to_datetime(selected_month + "-01")

# 해당 월 데이터 필터링
ride_data = df_ride[df_ride['YearMonth'] == selected_date]
pop_data = df_pop[df_pop['YearMonth'] == selected_date]

if ride_data.empty or pop_data.empty:
    st.warning("선택한 월에 데이터가 충분하지 않습니다.")
else:
    # 2) 기준 연령 선택 (예: 60~70세)
    min_age = int(pop_data['연령'].min())
    max_age = int(pop_data['연령'].max())
    selected_age = st.slider("🔢 무임승차 기준 연령 선택", min_age, max_age, value=65)
    
    # 3) 65세 기준 무임 인원 및 손실액 (기존 데이터에서)
    base_ride = ride_data.iloc[0]
    base_free_ride = base_ride['무임인원']  # 65세 기준 무임인원
    base_loss = base_ride['무임손실 (백만)']  # 65세 기준 무임손실액 (백만 원)
    # 1인당 평균 손실액 계산
    loss_per_person = base_loss / base_free_ride if base_free_ride > 0 else 0
    
    # 4) 선택 연령 이상 인구 수 합산 (월별 인구 데이터에서)
    eligible_pop = pop_data[pop_data['연령'] >= selected_age]['인구수'].sum()
    
    # 5) 예상 무임 손실액 계산
    estimated_loss = eligible_pop * loss_per_person
    
    # 6) 결과 출력
    st.subheader("📌 예상 무임승차 인원 및 손실액")
    st.markdown(f"""
    - 무임승차 기준 연령: **{selected_age}세 이상**  
    - 예상 무임승차 인원: **{eligible_pop:,}명**  
    - 1인당 평균 무임 손실액: **{loss_per_person:.2f} 백만원**  
    - 예상 총 무임 손실액: **{estimated_loss:,.2f} 백만원**  
    """)
    
    # 7) 기준 연령별 예상 무임 인원 및 손실액 시각화
    st.subheader("📊 기준 연령별 예상 무임손실 추이")
    # 여러 연령 기준에서 추이 계산 (예: min_age~max_age)
    age_range = range(min_age, max_age+1)
    estimated_ride_list = []
    estimated_loss_list = []
    for age in age_range:
        pop_sum = pop_data[pop_data['연령'] >= age]['인구수'].sum()
        estimated_ride_list.append(pop_sum)
        estimated_loss_list.append(pop_sum * loss_per_person)
    
    plot_df = pd.DataFrame({
        '연령기준': age_range,
        '예상무임인원': estimated_ride_list,
        '예상무임손실액': estimated_loss_list
    })
    
    fig, ax1 = plt.subplots(figsize=(10,6))
    ax2 = ax1.twinx()
    sns.lineplot(data=plot_df, x='연령기준', y='예상무임인원', ax=ax1, color='blue', label='예상 무임 인원')
    sns.lineplot(data=plot_df, x='연령기준', y='예상무임손실액', ax=ax2, color='red', label='예상 무임 손실액 (백만원)')
    ax1.set_xlabel("무임승차 기준 연령")
    ax1.set_ylabel("예상 무임 인원", color='blue')
    ax2.set_ylabel("예상 무임 손실액 (백만원)", color='red')
    ax1.grid(True)
    ax1.legend(loc='upper left')
    ax2.legend(loc='upper right')
    plt.title(f"{selected_month} 기준 무임승차 기준 연령별 예상 무임 인원 및 손실액")
    st.pyplot(fig)
