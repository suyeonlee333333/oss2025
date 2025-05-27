import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

# --------------------------
# 1. 데이터 불러오기 및 모델 학습
# --------------------------
@st.cache_data
def load_data_and_train_models():
    df = pd.read_excel('re_study_data.xlsx')
    df = df.rename(columns={
        '연령': 'Age',
        '무임인원': 'FreeRidePassengers',
        '무임손실 (백만)': 'LossFromFreeRides_MillionKRW',
        '누적손실액': 'CumulativeLoss_MillionKRW',
        '고령 인구수': 'SeniorPopulation',
        '지하철 이용량': 'SubwayUsage',
        '연도': 'Year',
        '월': 'Month'
    })
    df['YearMonth'] = pd.to_datetime(df['Year'].astype(str) + '-' + df['Month'].astype(str).str.zfill(2))

    # 모델 1: Age → FreeRidePassengers
    model_1 = LinearRegression()
    model_1.fit(df[['Age']], df['FreeRidePassengers'])

    # 모델 2: FreeRidePassengers → Loss
    model_2 = LinearRegression()
    model_2.fit(df[['FreeRidePassengers']], df['LossFromFreeRides_MillionKRW'])

    # 모델 3: Loss → Cumulative Loss
    model_3 = LinearRegression()
    model_3.fit(df[['LossFromFreeRides_MillionKRW']], df['CumulativeLoss_MillionKRW'])

    return df, model_1, model_2, model_3


@st.cache_data
def load_population_data():
    df_pop = pd.read_excel('re_study_data.xlsx', sheet_name='월별 인구 수')
    df_pop.columns = df_pop.columns.str.strip()
    df_pop.rename(columns={df_pop.columns[0]: 'YearMonth'}, inplace=True)
    df_pop = df_pop[~df_pop['YearMonth'].astype(str).str.contains('합')]
    df_pop['YearMonth'] = pd.to_datetime(df_pop['YearMonth'], errors='coerce')
    df_pop = df_pop.dropna(subset=['YearMonth'])
    return df_pop


def estimate_free_riders_by_virtual_policy(age, df, total_free_riders):
    total_old_population = df['SeniorPopulation'].sum()
    eligible_df = df[df['Age'] >= age]
    if eligible_df.empty or total_old_population == 0:
        return 0
    eligible_population = eligible_df['SeniorPopulation'].sum()
    eligible_ratio = eligible_population / total_old_population
    return total_free_riders * eligible_ratio


def simulate_loss(age, df, total_free_riders, model_2, model_3):
    count = estimate_free_riders_by_virtual_policy(age, df, total_free_riders)
    if count == 0:
        return 0, 0, 0
    loss = model_2.predict([[count]])[0]
    total = model_3.predict([[loss]])[0]
    return count, loss, total

# --------------------------
# 2. Streamlit 앱 실행
# --------------------------
st.title("🚇 무임승차 연령 기준 조정 시 손실 예측 시뮬레이터")

# 모델 학습 및 데이터 로드
main_df, model_1, model_2, model_3 = load_data_and_train_models()
df_pop = load_population_data()

# 사용 가능한 월 리스트 생성
available_months = sorted(set(main_df['YearMonth']) & set(df_pop['YearMonth']))
selected_month = st.selectbox("분석할 월 선택:", [d.strftime('%Y-%m') for d in available_months])
selected_date = pd.to_datetime(selected_month + '-01')

# 월별 데이터 필터링
df_ride_month = main_df[main_df['YearMonth'] == selected_date]
df_pop_month = df_pop[df_pop['YearMonth'] == selected_date]

if df_ride_month.empty or df_pop_month.empty:
    st.warning("선택한 월에 대한 데이터가 부족합니다.")
else:
    # 인구 데이터를 정리 (연령 컬럼 추출)
    # 인구 데이터를 정리 (연령 컬럼 추출)
    age_columns = [col for col in df_pop_month.columns if str(col).isnumeric()]
    df_age = df_pop_month[age_columns].melt(var_name='Age', value_name='SeniorPopulation')
    df_age['Age'] = df_age['Age'].astype(int)
    df_age = df_age.dropna()
    
    # 🔽 슬라이더 범위에 맞게 65세 이상만 필터링
    df_age = df_age[df_age['Age'] >= 65]
    
    # 총 무임인원
    total_free_riders = df_ride_month['FreeRidePassengers'].sum()
    
    # ✅ 슬라이더 범위 고정: 65 ~ 100세
    selected_age = st.slider("무임승차 기준 연령 선택", 65, 100, value=65)

    # 예측 실행
    count, loss, total = simulate_loss(selected_age, df_age, total_free_riders, model_2, model_3)

    # 결과 출력
    st.subheader("예상 무임승차 인원 및 손실액")
    st.markdown(f"""
    - 기준 연령: **{selected_age}세 이상**  
    - 예상 무임승차 인원: **{count:,.0f}명**  
    - 예상 손실액: **{loss:,.2f} 백만원**  
    - 예상 누적 손실액: **{total:,.2f} 백만원**
    """)

    # 다양한 연령 기준 변화 시나리오
    st.subheader("기준 연령 변화에 따른 손실 추이")
    age_range = range(min_age, max_age + 1)
    passengers_list, loss_list, total_list = [], [], []

    for age in age_range:
        c, l, t = simulate_loss(age, df_age, total_free_riders, model_2, model_3)
        passengers_list.append(c)
        loss_list.append(l)
        total_list.append(t)

    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax2 = ax1.twinx()

    ax1.plot(age_range, passengers_list, color='blue', marker='o', label='예상 무임 인원')
    ax2.plot(age_range, loss_list, color='red', marker='s', label='예상 손실액')

    ax1.set_xlabel("무임승차 기준 연령")
    ax1.set_ylabel("예상 무임 인원", color='blue')
    ax2.set_ylabel("예상 무임 손실액 (백만원)", color='red')

    ax1.tick_params(axis='y', labelcolor='blue')
    ax2.tick_params(axis='y', labelcolor='red')
    ax1.set_title(f"{selected_month} 기준 연령별 무임승차 추이")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')

    st.pyplot(fig)
