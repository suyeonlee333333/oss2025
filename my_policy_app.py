import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# 데이터 불러오는 함수. 캐시 사용으로 매번 다시 읽지 않음
@st.cache_data
def load_data():
    df_ride = pd.read_excel('re_study_data.xlsx', sheet_name=0)
    df_pop = pd.read_excel('re_study_data.xlsx', sheet_name='월별 인구 수')

    # df_ride 전처리
    df_ride.columns = df_ride.columns.str.strip()
    df_ride['연도'] = pd.to_numeric(df_ride['연도'], errors='coerce')
    df_ride['월'] = pd.to_numeric(df_ride['월'], errors='coerce')
    df_ride = df_ride.dropna(subset=['연도', '월'])
    df_ride['연도'] = df_ride['연도'].astype(int)
    df_ride['월'] = df_ride['월'].astype(int)
    df_ride['YearMonth'] = pd.to_datetime(df_ride['연도'].astype(str) + '-' + df_ride['월'].astype(str).str.zfill(2))

    # df_pop 전처리
    df_pop.columns = df_pop.columns.str.strip()
    df_pop.rename(columns={df_pop.columns[0]: '연월'}, inplace=True)
    df_pop['YearMonth'] = pd.to_datetime(df_pop['연월'].astype(str) + '-1', errors='coerce')

    for col in df_pop.columns[2:]:
        if isinstance(df_pop[col], pd.Series):
            df_pop[col] = pd.to_numeric(df_pop[col], errors='coerce')

    return df_ride, df_pop


# 데이터 불러오기
st.title("🚇 무임승차 연령 기준 조정 시 예상 손실 예측")
df_ride, df_pop = load_data()

# 선택 가능한 월 목록 구성
available_months = df_ride['YearMonth'].dt.strftime('%Y-%m').sort_values().unique()
selected_month = st.selectbox("\ud83d\udcc5 \ubd84석\ud560 \uc6d4 \uc120\ud0dd:", available_months)
selected_date = pd.to_datetime(selected_month + "-01")

# 해당 월 데이터 필터링
ride_data = df_ride[df_ride['YearMonth'] == selected_date]
pop_data = df_pop[df_pop['YearMonth'] == selected_date]

# 데이터 없을 경우 경고 및 사용 가능한 날짜 안내
if ride_data.empty or pop_data.empty:
    st.warning("선택한 월에 데이터가 충분하지 않습니다. 다른 월을 선택해주세요.")
    st.info(f"사용 가능한 월 목록: {', '.join(available_months)}")
else:
    # 연령 추출: 세 번째 열부터가 연령별 인구이므로 열 이름을 숫자로 변환
    age_columns = df_pop.columns[2:-1] if 'YearMonth' in df_pop.columns else df_pop.columns[2:]
    age_list = [int(col) for col in age_columns if col.isnumeric()]
    min_age = min(age_list)
    max_age = max(age_list)

    selected_age = st.slider("\ud83d\udd22 \ubb34임승차 \uae30준 \uc5f0령 \uc120\ud0dd", min_age, max_age, value=65)

    # ride_data에서 무임 인원, 손실 추출
    base_ride = ride_data.iloc[0]
    base_free_ride = base_ride['무임인원']
    base_loss = base_ride['무임손실 (백만)']
    loss_per_person = base_loss / base_free_ride if base_free_ride > 0 else 0

    # 해당 연령 이상 인구수 계산
    eligible_pop = pop_data.loc[:, str(selected_age):].sum(axis=1).values[0]
    estimated_loss = eligible_pop * loss_per_person

    # 결과 출력
    st.subheader("\ud83d\udccc \uc608상 \ubb34임승차 인원 및 손실액")
    st.markdown(f"""
    - 무임승차 기준 연령: **{selected_age}세 이상**  
    - 예상 무임승차 인원: **{eligible_pop:,.0f}명**  
    - 1인당 평균 무임 손실액: **{loss_per_person:.2f} 백만원**  
    - 예상 총 무임 손실액: **{estimated_loss:,.2f} 백만원**  
    """)

    # 기준 연령 변화에 따른 시나리오 분석
    st.subheader("\ud83d\udcca \uae30준 \uc5f0령별 \uc608상 \ubb34임승승 추이")

    age_range = range(min_age, max_age + 1)
    estimated_ride_list = []
    estimated_loss_list = []

    for age in age_range:
        pop_sum = pop_data.loc[:, str(age):].sum(axis=1).values[0]
        estimated_ride_list.append(pop_sum)
        estimated_loss_list.append(pop_sum * loss_per_person)
    st.write("선택된 날짜:", selected_date)
    st.write("ride_data rows:", ride_data.shape[0])
    st.write("pop_data rows:", pop_data.shape[0])


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

    # 범례 통합
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper right')

    st.pyplot(fig)
