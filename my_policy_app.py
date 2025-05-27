import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from matplotlib import font_manager as fm, rc
from datetime import datetime

# -----------------------------
# 한글 폰트 설정 함수
# -----------------------------
def set_korean_font():
    # 기본적으로 사용할 수 있는 나눔고딕 또는 다른 폰트 설정
    try:
        font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"  # 리눅스용
        font_name = fm.FontProperties(fname=font_path, size=10).get_name()
        rc('font', family=font_name)
    except:
        st.warning("한글 폰트 로딩에 실패했습니다. 영어로 대체될 수 있습니다.")

# -----------------------------
# 데이터 로딩 및 모델 학습
# -----------------------------
@st.cache_data
def load_data_and_train_models():
    df = pd.read_excel("re_study_data.xlsx", sheet_name="학습시킬 데이터")
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
    df_pop = pd.read_excel("re_study_data.xlsx", sheet_name="월별 인구 수")
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
# 예측 함수들
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
# Streamlit 메인 앱
# -----------------------------
def main():
    set_korean_font()

    st.title("무임승차 연령 조정 시나리오 분석")

    df_main, model_1, model_2, model_3 = load_data_and_train_models()
    df_pop = load_population_data()

    available_months = sorted(set(df_main['YearMonth']) & set(df_pop['YearMonth']))
    selected_month = st.selectbox("분석할 기준 월 선택:", [d.strftime('%Y-%m') for d in available_months])
    selected_date = pd.to_datetime(selected_month + '-01')

    df_ride_month = df_main[df_main['YearMonth'] == selected_date]
    df_pop_month = df_pop[df_pop['YearMonth'] == selected_date]

    if df_ride_month.empty or df_pop_month.empty:
        st.warning("선택한 월에 데이터가 없습니다.")
        return

    # 나이별 인구 추출
    age_columns = [col for col in df_pop_month.columns if col.isnumeric()]
    df_age = df_pop_month[age_columns].melt(var_name='Age', value_name='SeniorPopulation')
    df_age['Age'] = df_age['Age'].astype(int)
    df_age = df_age[df_age['Age'] >= 65]

    total_riders = df_ride_month['FreeRidePassengers'].sum()

    selected_age = st.slider("무임승차 기준 연령 설정", min_value=65, max_value=100, value=65)

    riders, loss, cum_loss = simulate_loss(selected_age, df_age, total_riders, model_2, model_3)

    st.subheader("예측 결과")
    st.markdown(f"""
    - 기준 연령: **{selected_age}세 이상**
    - 예상 무임승차 인원: **{riders:,.0f}명**
    - 예상 손실액: **{loss:,.2f}백만원**
    - 누적 손실 추정치: **{cum_loss:,.2f}백만원**
    """)

    st.subheader("연령별 손실 변화")
    age_range = range(65, 101)
    riders_list, loss_list, cum_list = batch_simulate_loss(df_age, total_riders, model_2, model_3, 65, 100)

    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax2 = ax1.twinx()
    ax1.plot(age_range, riders_list, 'b-o', label='무임승차 인원')
    ax2.plot(age_range, loss_list, 'r-s', label='손실액')

    ax1.set_xlabel("기준 연령")
    ax1.set_ylabel("무임승차 인원", color='blue')
    ax2.set_ylabel("손실액 (백만원)", color='red')
    ax1.set_title(f"연령에 따른 무임승차 인원 및 손실액 변화 ({selected_month})")
    fig.tight_layout()
    st.pyplot(fig)

    st.subheader("정책적 시사점 (AI 분석)")
    if loss >= 10000:
        st.markdown("""
        🔴 **예상 손실이 매우 큽니다.**
        - 무임승차 기준 연령을 상향 조정하는 방안을 고려해야 합니다.
        - 재정 부담 완화를 위해 소득 기반의 대상자 선별도 검토할 수 있습니다.
        """)
    elif loss < 3000:
        st.markdown("""
        🟢 **손실이 비교적 낮습니다.**
        - 현재 정책이 재정적으로도 지속 가능할 수 있습니다.
        - 또는 더 많은 계층에 혜택을 확대할 여지가 있습니다.
        """)
    else:
        st.markdown("""
        🟡 **손실이 중간 수준입니다.**
        - 연령 조정 외에도 시간대 제한, 지역 제한 등의 하이브리드 정책 도입을 고려할 수 있습니다.
        """)

if __name__ == "__main__":
    main()
