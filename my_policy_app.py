import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

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

    model_1 = LinearRegression()
    model_1.fit(df[['Age']], df['FreeRidePassengers'])

    model_2 = LinearRegression()
    model_2.fit(df[['FreeRidePassengers']], df['LossFromFreeRides_MillionKRW'])

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
    total_old_population = df[df['Age'] >= 65]['SeniorPopulation'].sum()
    eligible_population = df[df['Age'] >= age]['SeniorPopulation'].sum()

    st.write(f"Debug - total_old_population: {total_old_population}")
    st.write(f"Debug - eligible_population (age {age}+): {eligible_population}")
    st.write(f"Debug - total_free_riders: {total_free_riders}")

    if total_old_population == 0 or total_free_riders == 0:
        return 0

    eligible_ratio = eligible_population / total_old_population
    return total_free_riders * eligible_ratio



def simulate_loss(age, df, total_free_riders, model_2, model_3):
    count = estimate_free_riders_by_virtual_policy(age, df, total_free_riders)
    if count == 0:
        return 0, 0, 0
    loss = float(model_2.predict([[count]])[0])
    total = float(model_3.predict([[loss]])[0])
    return count, loss, total

def predict_free_ride_loss(age_threshold):
    # merged_df에서 가장 최근 월 데이터만 사용 (예시: 2024-12 등)
    latest_row = merged_df.sort_values('YearMonth').iloc[-1]

    total_passengers = latest_row['SubwayUsage']
    total_free_riders = latest_row['FreeRidePassengers']

    age_data = latest_row.filter(regex=r'^\d+$')
    age_data.index = age_data.index.astype(int)

    # 최근 달에 대한 월별 age별 population DataFrame 구성
    df_month = pd.DataFrame({
        'Age': age_data.index,
        'SeniorPopulation': age_data.values,
        'FreeRidePassengers': [0] * len(age_data),
        'SubwayUsage': total_passengers
    })

    # 예측 실행
    count, loss, total = simulate_loss(age_threshold, df_month, total_free_riders)

    return f"""기준 연령: {age_threshold}세 이상
예상 무임승차 인원: {int(count):,}명
예상 손실액: {loss:.2f} 백만원
예상 누적 손실액: {total:.2f} 백만원"""



# --------------------------
# 2. Streamlit 앱 실행
# --------------------------
st.title("🚇 무임승차 연령 기준 조정 시 손실 예측 시뮬레이터")

main_df, model_1, model_2, model_3 = load_data_and_train_models()
df_pop = load_population_data()

available_months = sorted(set(main_df['YearMonth']) & set(df_pop['YearMonth']))
selected_month = st.selectbox("분석할 월 선택:", [d.strftime('%Y-%m') for d in available_months])
selected_date = pd.to_datetime(selected_month + '-01')

df_ride_month = main_df[main_df['YearMonth'] == selected_date]
df_pop_month = df_pop[df_pop['YearMonth'] == selected_date]

if df_ride_month.empty or df_pop_month.empty:
    st.warning("선택한 월에 대한 데이터가 부족합니다.")
else:
    # 🔽 연령별 인구 데이터 정리
    age_columns = [col for col in df_pop_month.columns if str(col).isnumeric()]
    df_age = df_pop_month[age_columns].melt(var_name='Age', value_name='SeniorPopulation')
    df_age['Age'] = df_age['Age'].astype(int)
    df_age = df_age.dropna()
    df_age = df_age[df_age['Age'] >= 65]  # 슬라이더 범위에 맞게 필터링

    total_free_riders = df_ride_month['FreeRidePassengers'].sum()

    # ✅ 슬라이더 범위 설정
    min_age = 65
    max_age = 100
    selected_age = st.slider("무임승차 기준 연령 선택", min_value=min_age, max_value=max_age, value=65)

    # 예측 실행
    count, loss, total = simulate_loss(selected_age, df_age, total_free_riders, model_2, model_3)

    st.subheader("예상 무임승차 인원 및 손실액")
    st.markdown(f"""
    - 기준 연령: **{selected_age}세 이상**  
    - 예상 무임승차 인원: **{count:,.0f}명**  
    - 예상 손실액: **{loss:,.2f} 백만원**  
    - 예상 누적 손실액: **{total:,.2f} 백만원**
    """)


    # 그래프 그리기
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
    ax2.set_ylabel("예상 손실액 (백만원)", color='red')

    ax1.tick_params(axis='y', labelcolor='blue')
    ax2.tick_params(axis='y', labelcolor='red')
    ax1.set_title(f"{selected_month} 기준 연령별 무임승차 추이")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')

    st.pyplot(fig)
