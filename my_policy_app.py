# 무임승차 연령 조정 AI 정책 시뮬레이터

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import platform
from sklearn.linear_model import LinearRegression

# --------------------------
# 0. 한글 폰트 설정 (OS에 따라 자동 적용)
# --------------------------
def set_korean_font():
    if platform.system() == 'Windows':
        plt.rcParams['font.family'] = 'Malgun Gothic'
    elif platform.system() == 'Darwin':
        plt.rcParams['font.family'] = 'AppleGothic'
    else:
        import subprocess, os
        font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
        if not os.path.exists(font_path):
            subprocess.call(["apt-get", "install", "-y", "fonts-nanum"])
            fm._rebuild()
        plt.rcParams['font.family'] = 'NanumGothic'
    plt.rcParams['axes.unicode_minus'] = False

set_korean_font()

# --------------------------
# 1. 상수 및 설정
# --------------------------
DATA_FILE = 're_study_data.xlsx'
DATA_SHEET_LEARN = '학습시킬 데이터'
MIN_AGE = 65
MAX_AGE = 100

# --------------------------
# 2. 데이터 불러오기 및 모델 학습
# --------------------------
@st.cache_data

def load_data_and_train_models():
    df = pd.read_excel(DATA_FILE, sheet_name=DATA_SHEET_LEARN)
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
    df_pop = pd.read_excel(DATA_FILE, sheet_name='월별 인구 수', header=0)
    df_pop.columns = df_pop.columns.astype(str).str.strip()
    if '월간 / 나이' in df_pop.columns:
        df_pop.rename(columns={'월간 / 나이': 'YearMonth'}, inplace=True)
    elif df_pop.columns[0] != 'YearMonth':
        df_pop.rename(columns={df_pop.columns[0]: 'YearMonth'}, inplace=True)
    df_pop = df_pop[~df_pop['YearMonth'].astype(str).str.contains('총')]
    df_pop['YearMonth'] = pd.to_datetime(df_pop['YearMonth'], errors='coerce')
    return df_pop.dropna(subset=['YearMonth'])

# --------------------------
# 3. 시뮬레이션 함수
# --------------------------
def estimate_free_riders_by_virtual_policy(age, df_age, total_free_riders):
    total_old_population = df_age['SeniorPopulation'].sum()
    eligible_population = df_age[df_age['Age'] >= age]['SeniorPopulation'].sum()
    return total_free_riders * (eligible_population / total_old_population) if total_old_population else 0

def simulate_loss(age, df_age, total_free_riders, model_2, model_3):
    count = estimate_free_riders_by_virtual_policy(age, df_age, total_free_riders)
    if count == 0:
        return 0, 0, 0
    loss = float(model_2.predict([[count]])[0])
    total = float(model_3.predict([[loss]])[0])
    return count, loss, total

def batch_simulate_loss(df_age, total_free_riders, model_2, model_3, min_age, max_age):
    passengers_list, loss_list, total_list = [], [], []
    for age in range(min_age, max_age + 1):
        count, loss, total = simulate_loss(age, df_age, total_free_riders, model_2, model_3)
        passengers_list.append(count)
        loss_list.append(loss)
        total_list.append(total)
    return passengers_list, loss_list, total_list

# --------------------------
# 4. 연도별 손실 예측 및 시사점 도출
# --------------------------
def policy_analysis_over_years(main_df, df_pop, model_2, model_3, base_age=65):
    results = []
    for year in range(2021, 2025):
        date = pd.to_datetime(f"{year}-01-01")
        df_ride = main_df[main_df['YearMonth'] == date]
        df_pop_month = df_pop[df_pop['YearMonth'] == date]
        if df_ride.empty or df_pop_month.empty:
            continue
        age_cols = [c for c in df_pop_month.columns if str(c).isnumeric()]
        df_age = df_pop_month[age_cols].melt(var_name='Age', value_name='SeniorPopulation')
        df_age['Age'] = df_age['Age'].astype(int)
        df_age = df_age[df_age['Age'] >= MIN_AGE]
        total_free_riders = df_ride['FreeRidePassengers'].sum()
        count, loss, total = simulate_loss(base_age, df_age, total_free_riders, model_2, model_3)
        results.append({"연도": year, "예상 무임 인원": count, "예상 손실": loss})
    return pd.DataFrame(results)

# --------------------------
# 5. Streamlit 앱 실행
# --------------------------
def main():
    st.title("🚇 무임승차 연령 조정 AI 예측 및 정책 시사점 분석기")
    main_df, model_1, model_2, model_3 = load_data_and_train_models()
    df_pop = load_population_data()

    # 선택 UI
    available_months = sorted(set(main_df['YearMonth']) & set(df_pop['YearMonth']))
    selected_month = st.selectbox("분석할 월 선택:", [d.strftime('%Y-%m') for d in available_months])
    selected_date = pd.to_datetime(selected_month + '-01')
    selected_age = st.slider("무임승차 기준 연령 선택", min_value=MIN_AGE, max_value=MAX_AGE, value=65)

    # 현재 시점 손실 예측
    df_ride_month = main_df[main_df['YearMonth'] == selected_date]
    df_pop_month = df_pop[df_pop['YearMonth'] == selected_date]
    age_columns = [col for col in df_pop_month.columns if str(col).isnumeric()]
    df_age = df_pop_month[age_columns].melt(var_name='Age', value_name='SeniorPopulation')
    df_age['Age'] = df_age['Age'].astype(int)
    df_age = df_age[df_age['Age'] >= MIN_AGE]

    total_free_riders = df_ride_month['FreeRidePassengers'].sum()
    count, loss, total = simulate_loss(selected_age, df_age, total_free_riders, model_2, model_3)

    st.subheader("🔍 선택 월 기준 예측")
    st.markdown(f"""
    - 기준 연령: **{selected_age}세 이상**  
    - 예상 무임승차 인원: **{count:,.0f}명**  
    - 예상 손실액: **{loss:,.2f} 백만원**  
    - 예상 누적 손실액: **{total:,.2f} 백만원**
    """)

    # 연령 변화 시각화
    st.subheader("📊 연령 기준 변화에 따른 손실 추이")
    passengers_list, loss_list, _ = batch_simulate_loss(df_age, total_free_riders, model_2, model_3, MIN_AGE, MAX_AGE)
    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax2 = ax1.twinx()
    age_range = range(MIN_AGE, MAX_AGE + 1)
    ax1.plot(age_range, passengers_list, color='blue', label='예상 무임 인원')
    ax2.plot(age_range, loss_list, color='red', label='예상 손실액')
    ax1.set_xlabel("연령")
    ax1.set_ylabel("무임 인원", color='blue')
    ax2.set_ylabel("손실액 (백만원)", color='red')
    ax1.legend(loc='upper left')
    ax2.legend(loc='upper right')
    st.pyplot(fig)

    # 연도별 분석
    st.subheader("📈 연도별(1월 기준) 손실 추이 및 정책 시사점")
    df_policy = policy_analysis_over_years(main_df, df_pop, model_2, model_3, base_age=selected_age)
    st.dataframe(df_policy)

    if not df_policy.empty:
        avg_loss = df_policy['예상 손실'].mean()
        st.markdown(f"**👉 평균 예상 손실액**: {avg_loss:,.2f} 백만원")
        if avg_loss >= 15000:
            st.warning("🔴 손실이 매우 큽니다. 연령 기준 상향 고려가 필요합니다.")
        elif avg_loss >= 10000:
            st.info("🟠 손실 부담이 존재합니다. 단계적 조정 검토가 필요합니다.")
        else:
            st.success("🟢 현재 연령 기준은 유지해도 손실 관리가 가능합니다.")

if __name__ == "__main__":
    main()
