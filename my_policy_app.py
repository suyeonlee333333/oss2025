import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from datetime import datetime

# 파일 이름 상수
DATA_FILE = 're_study_data.xlsx'
DATA_SHEET = '학습시킬 데이터'
MIN_AGE = 65
MAX_AGE = 100

# -----------------------------
# 1. 데이터 로딩 및 모델 학습
# -----------------------------
@st.cache_data
def load_data_and_train_models():
    df = pd.read_excel(DATA_FILE, sheet_name=DATA_SHEET)
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
    df_pop = pd.read_excel(DATA_FILE, sheet_name='월별 인구 수')
    df_pop.columns = df_pop.columns.astype(str).str.strip()

    if '월간 / 나이' in df_pop.columns:
        df_pop.rename(columns={'월간 / 나이': 'YearMonth'}, inplace=True)
    else:
        df_pop.rename(columns={df_pop.columns[0]: 'YearMonth'}, inplace=True)

    df_pop = df_pop[~df_pop['YearMonth'].astype(str).str.contains('총')]
    df_pop['YearMonth'] = pd.to_datetime(df_pop['YearMonth'], errors='coerce')
    df_pop.dropna(subset=['YearMonth'], inplace=True)

    return df_pop

# -----------------------------
# 2. 예측 함수들
# -----------------------------
def estimate_free_riders(age, df_age, total_free_riders):
    eligible_population = df_age[df_age['Age'] >= age]['SeniorPopulation'].sum()
    total_population = df_age['SeniorPopulation'].sum()
    if total_population == 0 or total_free_riders == 0:
        return 0
    ratio = eligible_population / total_population
    return total_free_riders * ratio

def simulate_loss(age, df_age, total_free_riders, model_2, model_3):
    riders = estimate_free_riders(age, df_age, total_free_riders)
    if riders == 0:
        return 0, 0, 0
    loss = model_2.predict([[riders]])[0]
    cum_loss = model_3.predict([[loss]])[0]
    return riders, loss, cum_loss

def batch_simulate_loss(df_age, total_free_riders, model_2, model_3, min_age, max_age):
    riders_list, loss_list, cum_list = [], [], []
    for age in range(min_age, max_age + 1):
        riders, loss, cum_loss = simulate_loss(age, df_age, total_free_riders, model_2, model_3)
        riders_list.append(riders)
        loss_list.append(loss)
        cum_list.append(cum_loss)
    return riders_list, loss_list, cum_list

# -----------------------------
# 3. Streamlit 메인 앱
# -----------------------------
def main():
    st.title("Free Ride Policy Simulation")

    df_main, model_1, model_2, model_3 = load_data_and_train_models()
    df_pop = load_population_data()

    available_months = sorted(set(df_main['YearMonth']) & set(df_pop['YearMonth']))
    selected_month = st.selectbox("Select Month:", [d.strftime('%Y-%m') for d in available_months])
    selected_date = pd.to_datetime(selected_month + '-01')

    df_ride_month = df_main[df_main['YearMonth'] == selected_date]
    df_pop_month = df_pop[df_pop['YearMonth'] == selected_date]

    if df_ride_month.empty or df_pop_month.empty:
        st.warning("No data for selected month.")
        return

    # 나이별 인구
    age_columns = [col for col in df_pop_month.columns if col.isnumeric()]
    df_age = df_pop_month[age_columns].melt(var_name='Age', value_name='SeniorPopulation')
    df_age['Age'] = df_age['Age'].astype(int)
    df_age = df_age[df_age['Age'] >= MIN_AGE]

    total_riders = df_ride_month['FreeRidePassengers'].sum()

    selected_age = st.slider("Set Age Threshold", min_value=MIN_AGE, max_value=MAX_AGE, value=65)

    riders, loss, cum_loss = simulate_loss(selected_age, df_age, total_riders, model_2, model_3)

    st.subheader("Prediction Result")
    st.markdown(f"""
    - Threshold Age: **{selected_age} years**
    - Predicted Free Riders: **{riders:,.0f}**
    - Estimated Loss: **{loss:,.2f} million KRW**
    - Estimated Cumulative Loss: **{cum_loss:,.2f} million KRW**
    """)

    st.subheader("Policy Impact by Age")
    age_range = range(MIN_AGE, MAX_AGE + 1)
    riders_list, loss_list, cum_list = batch_simulate_loss(df_age, total_riders, model_2, model_3, MIN_AGE, MAX_AGE)

    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax2 = ax1.twinx()
    ax1.plot(age_range, riders_list, 'b-o', label='Free Riders')
    ax2.plot(age_range, loss_list, 'r-s', label='Loss')

    ax1.set_xlabel("Age Threshold")
    ax1.set_ylabel("Free Riders", color='blue')
    ax2.set_ylabel("Loss (million KRW)", color='red')

    ax1.tick_params(axis='y', labelcolor='blue')
    ax2.tick_params(axis='y', labelcolor='red')
    ax1.set_title(f"Impact by Age Threshold ({selected_month})")

    fig.tight_layout()
    st.pyplot(fig)

    # -----------------------------
    # 정책 시사점 도출 예시
    # -----------------------------
    st.subheader("AI-based Policy Suggestion")

    policy_insight = ""
    if loss >= 10000:
        policy_insight = (
            "👉 Estimated loss is very high.\n"
            "- Consider raising the age threshold to reduce fiscal burden.\n"
            "- Also, evaluate low-income or vulnerable population exceptions."
        )
    elif loss < 3000:
        policy_insight = (
            "✅ Loss is relatively low.\n"
            "- Current policy seems sustainable.\n"
            "- Maintain or gradually expand benefit coverage."
        )
    else:
        policy_insight = (
            "⚖️ Moderate loss observed.\n"
            "- You may explore hybrid policies like time-limited free rides or regional restrictions."
        )

    st.markdown(policy_insight)

if __name__ == "__main__":
    main()
