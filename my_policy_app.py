import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

@st.cache_data
def load_data():
    # 데이터 불러오기
    df_ride = pd.read_excel('re_study_data.xlsx', sheet_name=0)
    df_pop = pd.read_excel('re_study_data.xlsx', sheet_name='월별 인구 수')

    # --- df_ride 처리 ---
    df_ride.columns = df_ride.columns.str.strip()
    
    # '연도', '월' 숫자로 변환
    df_ride['연도'] = pd.to_numeric(df_ride['연도'], errors='coerce')
    df_ride['월'] = pd.to_numeric(df_ride['월'], errors='coerce')

    # 결측값 제거
    df_ride = df_ride.dropna(subset=['연도', '월'])

    # 정수형으로 바꾸기 (to_datetime 에러 방지)
    df_ride['연도'] = df_ride['연도'].astype(int)
    df_ride['월'] = df_ride['월'].astype(int)

    # 날짜 컬럼 생성
    df_ride['YearMonth'] = pd.to_datetime(dict(year=df_ride['연도'], month=df_ride['월'], day=1))

    # --- df_pop 처리 ---
    df_pop.columns = df_pop.columns.str.strip()

    # 첫 번째 열 이름 바꾸기
    df_pop.rename(columns={df_pop.columns[0]: '연월'}, inplace=True)

    # '연월' → datetime으로 변환 (예: "2021-1" → "2021-01-01")
    df_pop['YearMonth'] = pd.to_datetime(df_pop['연월'].astype(str) + '-1', errors='coerce')

    # 숫자 열만 선택해서 변환
    df_pop_numeric = df_pop.drop(columns=['연월']).copy()
    for col in df_pop_numeric.columns:
        if col != 'YearMonth':
            df_pop_numeric[col] = pd.to_numeric(df_pop_numeric[col], errors='coerce')

    return df_ride, df_pop_numeric

# 데이터 불러오기
df_ride, df_pop = load_data()



# 분석/시각화 코드


# 데이터 불러오기
df_ride, df_pop = load_data()

# 제목
st.title("🚇 무임승차 연령 기준 조정 시 예상 손실 예측")

# 1) 분석할 월 선택
available_months = df_ride['YearMonth'].dt.strftime('%Y-%m').sort_values().unique()
selected_month = st.selectbox("📅 분석할 월 선택:", available_months)
selected_date = pd.to_datetime(selected_month + "-01")

# 선택한 월에 해당하는 데이터 필터링
ride_data = df_ride[df_ride['YearMonth'] == selected_date]
pop_data = df_pop[df_pop['YearMonth'] == selected_date]

if ride_data.empty or pop_data.empty:
    st.warning("선택한 월에 데이터가 충분하지 않습니다.")
else:
    # 2) 기준 연령 선택
    min_age = int(pop_data['연령'].min())
    max_age = int(pop_data['연령'].max())
    selected_age = st.slider("🔢 무임승차 기준 연령 선택", min_age, max_age, value=65)

    # 3) 현재 기준 데이터 (예: 65세 기준)
    base_ride = ride_data.iloc[0]
    base_free_ride = base_ride['무임인원']
    base_loss = base_ride['무임손실 (백만)']
    loss_per_person = base_loss / base_free_ride if base_free_ride > 0 else 0

    # 4) 선택 연령 이상 인구 수
    eligible_pop = pop_data[pop_data['연령'] >= selected_age]['인구수'].sum()

    # 5) 예상 손실액 계산
    estimated_loss = eligible_pop * loss_per_person

    # 6) 결과 출력
    st.subheader("📌 예상 무임승차 인원 및 손실액")
    st.markdown(f"""
    - 무임승차 기준 연령: **{selected_age}세 이상**  
    - 예상 무임승차 인원: **{eligible_pop:,}명**  
    - 1인당 평균 무임 손실액: **{loss_per_person:.2f} 백만원**  
    - 예상 총 무임 손실액: **{estimated_loss:,.2f} 백만원**  
    """)

    # 7) 연령별 추이 시각화
    st.subheader("📊 기준 연령별 예상 무임손실 추이")

    age_range = range(min_age, max_age + 1)
    estimated_ride_list = []
    estimated_loss_list = []

    for age in age_range:
        pop_sum = pop_data[pop_data['연령'] >= age]['인구수'].sum()
        estimated_ride_list.append(pop_sum)
        estimated_loss_list.append(pop_sum * loss_per_person)

    # 시각화
    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax2 = ax1.twinx()

    ax1.plot(age_range, estimated_ride_list, color='blue', marker='o', label='예상 무임 인원')
    ax2.plot(age_range, estimated_loss_list, color='red', marker='s', label='예상 무임 손실액 (백만원)')

    ax1.set_xlabel("무임승차 기준 연령")
    ax1.set_ylabel("예상 무임 인원", color='blue')
    ax2.set_ylabel("예상 무임 손실액 (백만원)", color='red')

    ax1.tick_params(axis='y', labelcolor='blue')
    ax2.tick_params(axis='y', labelcolor='red')

    ax1.grid(True)
    ax1.set_title(f"{selected_month} 기준 무임승차 기준 연령별 예상 무임 인원 및 손실액")

    # 범례 추가
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper right')

    st.pyplot(fig)
