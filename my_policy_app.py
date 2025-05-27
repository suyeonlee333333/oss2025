import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

# --------------------------
# 🔧 전역 상수
# --------------------------
BASE_FREE_AGE = 65
EXCEL_FILE = 're_study_data.xlsx'
SHEET_NAME_TRAIN = '학습시킬 데이터'
SHEET_NAME_POP = '월별 인구 수'


# --------------------------
# 1. 데이터 불러오기 및 모델 학습
# --------------------------
@st.cache_data
def load_data_and_train_models():
    df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME_TRAIN)
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

    model_1 = LinearRegression().fit(df[['Age']], df['FreeRidePassengers'])
    model_2 = LinearRegression().fit(df[['FreeRidePassengers']], df['LossFromFreeRides_MillionKRW'])
    model_3 = LinearRegression().fit(df[['LossFromFreeRides_MillionKRW']], df['CumulativeLoss_MillionKRW'])

    return df, model_1, model_2, model_3


@st.cache_data
def load_population_data():
    df_pop = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME_POP)

    df_pop.columns = df_pop.columns.astype(str).str.strip()

    if '월간 / 나이' in df_pop.columns:
        df_pop.rename(columns={'월간 / 나이': 'YearMonth'}, inplace=True)
    elif df_pop.columns[0] != 'YearMonth':
        df_pop.rename(columns={df_pop.columns[0]: 'YearMonth'}, inplace=True)

    df_pop = df_pop[~df_pop['YearMonth'].astype(str).str.contains('총')]
    df_pop['YearMonth'] = pd.to_datetime(df_pop['YearMonth'], errors='coerce')
    df_pop = df_pop.dropna(subset=['YearMonth'])

    return df_pop


# --------------------------
# 2. 시뮬레이션 함수
# --------------------------
def estimate_free_riders_by_virtual_policy(age, df, total_free_riders):
    total_old_population = df[df['Age'] >= BASE_FREE_AGE]['SeniorPopulation'].sum()
    eligible_population = df[df['Age'] >= age]['SeniorPopulation'].sum()

    if total_old_population == 0 or total_free_riders == 0:
        return 0

    eligible_ratio = eligible_population / total_old_population
    return total_free_riders * eligible_ratio


@st.cache_data
def batch_simulate_loss(df_age, total_free_riders, model_2, model_3, min_age, max_age):
    passengers_list, loss_list, total_list = [], [], []

    for age in range(min_age, max_age + 1):
        count = estimate_free_riders_by_virtual_policy(age, df_age, total_free_riders)
        if count == 0:
            loss, total = 0, 0
        else:
            loss = float(model_2.predict([[count]])[0])
            total = float(model_3.predict([[loss]])[0])
        passengers_list.append(count)
        loss_list.append(loss)
        total_list.append(total)

    return passengers_list, loss_list, total_list


# --------------------------
# 3. 메인 앱
# --------------------------
def main():
    st.title("🚇 무임승차 연령 기준 조정 시 손실 예측 시뮬레이터")

    main_df, _, model_2, model_3 = load_data_and_train_models()
    df_pop = load_population_data()

    available_months = sorted(set(main_df['YearMonth']) & set(df_pop['YearMonth']))
    selected_month = st.selectbox("분석할 월 선택:", [d.strftime('%Y-%m') for d in available_months])
    selected_date = pd.to_datetime(selected_month + '-01')

    df_ride_month = main_df[main_df['YearMonth'] == selected_date]
    df_pop_month = df_pop[df_pop['YearMonth'] == selected_date]

    if df_ride_month.empty or df_pop_month.empty:
        st.warning("선택한 월에 대한 데이터가 부족합니다.")
        return

    age_columns = [col for col in df_pop_month.columns if str(col).isnumeric()]
    df_age = df_pop_month[age_columns].melt(var_name='Age', value_name='SeniorPopulation')
    df_age['Age'] = df_age['Age'].astype(int)
    df_age = df_age.dropna()
    df_age = df_age[df_age['Age'] >= BASE_FREE_AGE]

    total_free_riders = df_ride_month['FreeRidePassengers'].sum()

    min_age = BASE_FREE_AGE
    max_age = 100
    selected_age = st.slider("무임승차 기준 연령 선택", min_value=min_age, max_value=max_age, value=BASE_FREE_AGE)

    passengers_list, loss_list, total_list = batch_simulate_loss(df_age, total_free_riders, model_2, model_3, min_age, max_age)
    count = passengers_list[selected_age - min_age]
    loss = loss_list[selected_age - min_age]
    total = total_list[selected_age - min_age]

    st.subheader("예상 무임승차 인원 및 손실액")
    st.markdown(f"""
    - 기준 연령: **{selected_age}세 이상**  
    - 예상 무임승차 인원: **{int(count):,}명**  
    - 예상 손실액: **{loss:,.2f} 백만원**  
    - 예상 누적 손실액: **{total:,.2f} 백만원**
    """)

    # 📈 그래프 시각화
    st.subheader("기준 연령 변화에 따른 손실 추이")
    age_range = list(range(min_age, max_age + 1))

    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax2 = ax1.twinx()

    ax1.plot(age_range, passengers_list, color='blue', marker='o', label='예상 무임 인원')
    ax2.plot(age_range, loss_list, color='red', marker='s', label='예상 손실액')

    ax1.set_xlabel("무임승차 기준 연령")
    ax1.set_ylabel("예상 무임 인원 (명)", color='blue')
    ax2.set_ylabel("예상 손실액 (백만원)", color='red')

    ax1.tick_params(axis='y', labelcolor='blue')
    ax2.tick_params(axis='y', labelcolor='red')
    ax1.set_title(f"{selected_month} 기준 연령별 무임승차 추이")

    # 콤마 포맷 추가
    ax1.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, _: f'{int(x):,}'))
    ax2.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:,.0f}'))

    # 범례
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')

    st.pyplot(fig)


# --------------------------
# 앱 실행
# --------------------------
if __name__ == "__main__":
    main()
