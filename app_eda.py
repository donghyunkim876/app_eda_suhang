import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Matplotlib 한글 폰트 설정 (Windows 기준, Mac/Linux는 폰트명 변경 필요)
# 한글 폰트가 설치되어 있지 않으면, 시스템 기본 폰트 사용 또는 설치 필요
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False  # 마이너스 폰트 깨짐 방지

# 지역명 번역 맵 (필요에 따라 추가/수정)
REGION_TRANSLATION_MAP = {
    '전국': 'National',
    '서울특별시': 'Seoul',
    '부산광역시': 'Busan',
    '대구광역시': 'Daegu',
    '인천광역시': 'Incheon',
    '광주광역시': 'Gwangju',
    '대전광역시': 'Daejeon',
    '울산광역시': 'Ulsan',
    '세종특별자치시': 'Sejong',
    '경기도': 'Gyeonggi',
    '강원도': 'Gangwon',
    '충청북도': 'Chungbuk',
    '충청남도': 'Chungnam',
    '전라북도': 'Jeonbuk',
    '전라남도': 'Jeonnam',
    '경상북도': 'Gyeongbuk',
    '경상남도': 'Gyeongnam',
    '제주특별자치도': 'Jeju'
    # '세종특별자치시 (중복)': 'Sejong (Duplicate)' # 중복 처리된 이름도 번역 가능
}

# ---------------------
# Firebase 설정 (기존 설정 유지)
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화 (기존 설정 유지)
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""
    st.session_state.df_population_eda = None  # 인구 데이터용 DataFrame
    st.session_state.uploaded_population_file_id = None


# ---------------------
# 홈 페이지 클래스 (기존 설정 유지)
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 홈")
        if st.session_state.get("logged_in"):
            st.success(f"환영합니다, {st.session_state.get('user_email')}님!")

        # 앱 소개 및 EDA 페이지 안내
        st.markdown("""
                ---
                **인구 통계 분석 도구**
                이 애플리케이션은 사용자가 인구 관련 CSV 파일을 업로드하여,
                시간에 따른 인구 변화, 지역별 특성, 그리고 연간 증감 추이 등
                다양한 통계 데이터를 직관적으로 시각화하고 분석할 수 있도록 돕습니다.
                인구 동향을 파악하고 미래를 예측하는 데 유용한 정보를 제공합니다.
                """)
        st.markdown("---")
        st.info("💡 **데이터 분석 페이지**로 이동하여 'population_trends.csv' 파일을 업로드하고 인구 동향을 탐색해 보세요!")


# ---------------------
# 로그인 페이지 클래스 (기존 설정 유지)
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일 주소")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인에 성공했습니다!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 정보가 올바르지 않습니다.")


# ---------------------
# 회원가입 페이지 클래스 (기존 설정 유지)
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일 주소")
        password = st.text_input("비밀번호 (6자 이상)", type="password")
        name = st.text_input("이름")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대폰 번호 (선택 사항)")

        if st.button("회원 가입하기"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입이 완료되었습니다! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception as e:
                st.error(f"회원가입 중 오류가 발생했습니다: {e}")


# ---------------------
# 비밀번호 찾기 페이지 클래스 (기존 설정 유지)
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 재설정")
        email = st.text_input("이메일 주소")
        if st.button("비밀번호 재설정 이메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀워드 재설정 이메일이 발송되었습니다. 이메일을 확인해주세요.")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"이메일 전송 실패: {e}")


# ---------------------
# 사용자 정보 수정 페이지 클래스 (기존 설정 유지)
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 내 정보 관리")

        email = st.session_state.get("user_email", "")
        st.text_input("이메일", value=email, disabled=True, help="이메일은 변경할 수 없습니다.")  # 이메일 변경 불가하도록
        name = st.text_input("이름", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대폰 번호", value=st.session_state.get("user_phone", ""))

        current_profile_image_url = st.session_state.get("profile_image_url")
        if current_profile_image_url:
            st.image(current_profile_image_url, caption="현재 프로필 이미지", width=150)

        uploaded_file = st.file_uploader("새 프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            try:
                storage.child(file_path).put(uploaded_file, st.session_state.id_token)
                image_url = storage.child(file_path).get_url(st.session_state.id_token)
                st.session_state.profile_image_url = image_url
                st.image(image_url, caption="새 프로필 이미지 미리보기", width=150)
                st.success("프로필 이미지 업로드 완료!")
            except Exception as e:
                st.error(f"이미지 업로드 실패: {e}")

        if st.button("정보 업데이트"):
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            try:
                firestore.child("users").child(email.replace(".", "_")).update({
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "profile_image_url": st.session_state.get("profile_image_url", "")
                })
                st.success("사용자 정보가 성공적으로 저장되었습니다.")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"정보 저장 실패: {e}")


# ---------------------
# 로그아웃 페이지 클래스 (기존 설정 유지)
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("안전하게 로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()


# ---------------------
# EDA 페이지 클래스 (인구 데이터 분석에 맞게 재구성 및 차별화)
# ---------------------
class EDA:
    def __init__(self):
        self.run_eda_app()

    def run_eda_app(self):
        st.set_page_config(page_title="인구 데이터 통계 분석", layout="wide")
        st.title("📊 Population Data Analysis Dashboard")  # 영어 제목으로 변경

        uploaded_file = st.file_uploader("Upload Population Trends Data (population_trends.csv)", type="csv")  # 영어 문구

        # 파일이 업로드되지 않았거나, 새로운 파일이 업로드된 경우 데이터 로드 및 전처리
        if uploaded_file is None:
            st.info("👆 Please upload a CSV file to start analysis. (e.g., population_trends.csv)")  # 영어 문구
            st.session_state.df_population_eda = None
            st.session_state.uploaded_population_file_id = None
            return
        elif st.session_state.uploaded_population_file_id != uploaded_file.file_id:
            df_raw = pd.read_csv(uploaded_file)
            st.session_state.df_population_eda = self._preprocess_population_data(df_raw)
            st.session_state.uploaded_population_file_id = uploaded_file.file_id
            st.success("🎉 Dataset successfully loaded and ready for analysis!")  # 영어 문구

        df = st.session_state.df_population_eda

        st.sidebar.header("📊 Analysis Period Setting")  # 영어 제목
        if df is not None and '연도' in df.columns:
            all_years = sorted(df["연도"].unique())
            if all_years:
                min_year = int(all_years[0])
                max_year = int(all_years[-1])

                selected_period_years = st.sidebar.slider(
                    "Analyze data for the last N years?",  # 영어 문구
                    min_value=1,
                    max_value=max_year - min_year + 1,
                    value=min(10, max_year - min_year + 1),
                    step=1
                )

                analysis_start_year = max_year - selected_period_years + 1
                st.sidebar.markdown(
                    f"**Selected Analysis Range:** \n- **Start Year:** {analysis_start_year} \n- **End Year:** {max_year}")  # 영어 문구

                st.session_state.start_year_for_analysis = analysis_start_year
                st.session_state.last_year = max_year
                st.session_state.years_to_analyze = selected_period_years
            else:
                st.sidebar.info("No 'Year' data found for period setting.")  # 영어 문구
        else:
            st.sidebar.info("Waiting for data load...")  # 영어 문구

        tabs = st.tabs([
            "1. Data Overview",  # 탭 이름 변경
            "2. National Population Trend",  # 탭 이름 변경
            "3. Regional Population Change Rank",  # 탭 이름 변경
            "4. Annual Regional Change Records",  # 탭 이름 변경
            "5. Regional Population Composition"  # 탭 이름 변경
        ])

        with tabs[0]:  # 1) 데이터 개요
            st.header("🔍 Dataset Basic Information")  # 영어 제목
            st.markdown("Check the structure, content, and quality of the uploaded dataset at a glance.")  # 영어 문구

            st.subheader("📋 Data Preview (Top 5 Rows)")  # 영어 제목
            st.dataframe(df.head(), use_container_width=True)

            st.subheader("📊 DataFrame Structure (df.info())")  # 영어 제목
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.text(buffer.getvalue())

            st.subheader("📈 Summary Statistics (df.describe())")  # 영어 제목
            st.dataframe(df.describe().applymap(lambda x: f"{x:,.2f}"), use_container_width=True)

            st.subheader("🚫 Data Quality Check Results")  # 영어 제목
            missing = df.isnull().sum()
            total_rows = len(df)
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Missing Values", f"{missing.sum():,d}")  # 영어 문구
                if missing.sum() == 0:
                    st.success("No missing values found in any columns. 👍")  # 영어 문구
                else:
                    st.warning("Some columns have missing values. (Preprocessing completed)")  # 영어 문구
                    st.dataframe(
                        missing[missing > 0].reset_index().rename(columns={0: 'Missing Count', 'index': 'Column Name'}),
                        hide_index=True)  # 영어 컬럼명

            with col2:
                duplicates = df.duplicated().sum()
                st.metric("Total Duplicate Rows", f"{duplicates:,d}")  # 영어 문구
                if duplicates > 0:
                    st.warning(
                        f"Found {duplicates:,d} duplicate rows. (Preprocessing completed: '(Duplicate)' added to region name)")  # 영어 문구
                else:
                    st.success("No duplicate rows found. ✨")  # 영어 문구

        with tabs[1]:  # 2) 전국 핵심 지표 추이
            st.header("📉 National Population and Key Indicators Trend")  # 영어 제목
            st.markdown("""
            Visually analyze the annual changes in the total national population,
            births, and deaths, which are key factors influencing population changes.
            """)  # 영어 문구
            nationwide_data = df[df["지역"] == "전국"].sort_values("연도")

            if nationwide_data.empty:
                st.warning("⚠️ 'National' data is missing. Please check the source file.")  # 영어 문구
            else:
                fig1, ax1 = plt.subplots(figsize=(14, 7))

                # 인구 추이
                ax1.plot(nationwide_data["연도"], nationwide_data["인구"], marker="o", linestyle="-", color="#1f77b4",
                         label="Total Population", linewidth=2)  # 영어 라벨

                # 출생아수, 사망자수 (보조 y축 사용)
                ax2 = ax1.twinx()
                if '출생아수(명)' in nationwide_data.columns:
                    ax2.plot(nationwide_data["연도"], nationwide_data["출생아수(명)"], marker="x", linestyle="--",
                             color="#2ca02c", label="Births", linewidth=1.5)  # 영어 라벨
                if '사망자수(명)' in nationwide_data.columns:
                    ax2.plot(nationwide_data["연도"], nationwide_data["사망자수(명)"], marker="s", linestyle=":",
                             color="#d62728", label="Deaths", linewidth=1.5)  # 영어 라벨

                ax1.set_title("National Annual Population and Key Indicators Change", fontsize=18, pad=20)  # 영어 제목
                ax1.set_xlabel("Year", fontsize=14)  # 영어 레이블
                ax1.set_ylabel("Population (Count)", fontsize=14, color="#1f77b4")  # 영어 레이블
                ax2.set_ylabel("Births/Deaths (Count)", fontsize=14)  # 영어 레이블

                ax1.tick_params(axis='y', labelcolor="#1f77b4")
                ax2.tick_params(axis='y')

                # 범례 통합
                lines, labels = ax1.get_lines(), [l.get_label() for l in ax1.get_lines()]
                lines2, labels2 = ax2.get_lines(), [l.get_label() for l in ax2.get_lines()]
                ax2.legend(lines + lines2, labels + labels2, loc='upper left', bbox_to_anchor=(0.0, 1.0))

                ax1.grid(True, linestyle='--', alpha=0.6)

                # --- 2035년 인구 예측 ---
                st.subheader("Population Prediction for 2035")  # 영어 제목
                st.markdown("""
                This prediction for 2035 population is based on the average annual change in
                births and deaths over the last 3 years in the 'National' data.
                **Note:** This is a simplified linear projection and may not reflect complex demographic changes.
                """)  # 영어 문구

                last_3_years_data = nationwide_data.tail(3)
                if len(last_3_years_data) < 2:
                    st.warning("Not enough data (at least 2 years) to predict population for 2035.")  # 영어 문구
                else:
                    # Calculate average annual change in births and deaths
                    avg_birth_change = last_3_years_data[
                        '출생아수(명)'].diff().mean() if '출생아수(명)' in nationwide_data.columns else 0
                    avg_death_change = last_3_years_data[
                        '사망자수(명)'].diff().mean() if '사망자수(명)' in nationwide_data.columns else 0

                    current_population = nationwide_data['인구'].iloc[-1]
                    current_year = nationwide_data['연도'].iloc[-1]

                    # Project births and deaths for 2035
                    num_years_to_project = 2035 - current_year

                    # Assuming average annual change in births/deaths continues
                    projected_births = nationwide_data['출생아수(명)'].iloc[
                                           -1] + avg_birth_change * num_years_to_project if '출생아수(명)' in nationwide_data.columns else 0
                    projected_deaths = nationwide_data['사망자수(명)'].iloc[
                                           -1] + avg_death_change * num_years_to_project if '사망자수(명)' in nationwide_data.columns else 0

                    # Ensure projected births/deaths don't go negative for simplicity
                    projected_births = max(0, projected_births)
                    projected_deaths = max(0, projected_deaths)

                    # Simplified population projection based on net natural change
                    # Using the latest year's birth/death count to calculate net change for each projected year
                    latest_births = nationwide_data['출생아수(명)'].iloc[-1]
                    latest_deaths = nationwide_data['사망자수(명)'].iloc[-1]
                    net_change_per_year = latest_births - latest_deaths

                    predicted_2035_population = current_population + (net_change_per_year * num_years_to_project)
                    predicted_2035_population = int(max(0, predicted_2035_population))  # 인구는 음수가 될 수 없음

                    st.write(f"**Predicted National Population in 2035:** {predicted_2035_population:,.0f}")  # 영어 문구

                    # Add prediction to the plot
                    ax1.plot(2035, predicted_2035_population, marker='*', markersize=15, color='orange',
                             label='Predicted 2035 Population')  # 영어 라벨

                    # Update legend with predicted point
                    lines, labels = ax1.get_lines(), [l.get_label() for l in ax1.get_lines()]
                    lines2, labels2 = ax2.get_lines(), [l.get_label() for l in ax2.get_lines()]
                    ax2.legend(lines + lines2, labels + labels2, loc='upper left', bbox_to_anchor=(0.0, 1.0))

                st.pyplot(fig1)  # 예측 포함된 그래프 출력

        with tabs[2]:  # 3) 지역별 인구 변화량 순위
            st.header(
                f"📊 Regional Population Net Change Rank for Last {st.session_state.get('years_to_analyze', 'N')} Years ({st.session_state.get('start_year_for_analysis', 'Start')}–{st.session_state.get('last_year', 'End')})")  # 영어 제목
            st.markdown("""
            Calculate the population change for each administrative division over the period selected in the sidebar,
            and visualize the ranking of regions with the highest increase or decrease.
            """)  # 영어 문구

            start_year_calc = st.session_state.get('start_year_for_analysis')
            end_year_calc = st.session_state.get('last_year')

            if start_year_calc is None or end_year_calc is None:
                st.warning("Analysis period setting is required. Please check the sidebar.")  # 영어 문구
                return

            filtered_df_period = df[(df["연도"].between(start_year_calc, end_year_calc)) & (df["지역"] != "전국")]

            if filtered_df_period.empty:
                st.warning(
                    f"No regional population data available for the selected period ({start_year_calc}–{end_year_calc}).")  # 영어 문구
            else:
                pop_start_df = filtered_df_period[filtered_df_period["연도"] == start_year_calc][["지역", "인구"]].set_index(
                    "지역").rename(columns={"인구": "Start_Population"})  # 영어 컬럼명
                pop_end_df = filtered_df_period[filtered_df_period["연도"] == end_year_calc][["지역", "인구"]].set_index(
                    "지역").rename(columns={"인구": "End_Population"})  # 영어 컬럼명

                population_change_df = pop_end_df.join(pop_start_df, how="inner")
                population_change_df["Net_Change"] = population_change_df["End_Population"] - population_change_df[
                    "Start_Population"]  # 영어 컬럼명
                population_change_df["Change_Rate (%)"] = (
                            population_change_df["Net_Change"] / population_change_df["Start_Population"] * 100).round(
                    2)  # 변화율 컬럼 추가
                population_change_df = population_change_df.sort_values("Net_Change", ascending=False)

                # 지역명 영어 번역
                population_change_df.index = population_change_df.index.map(
                    lambda x: REGION_TRANSLATION_MAP.get(x, x.replace(' (중복)', ' (Dup)')))

                top_bottom_display_count = st.slider("Display Top/Bottom N Regions for Population Change?", 5,
                                                     min(30, len(population_change_df)), 10)  # 영어 문구

                if top_bottom_display_count * 2 > len(population_change_df):
                    display_change_data = population_change_df
                else:
                    display_change_data = pd.concat([population_change_df.head(top_bottom_display_count),
                                                     population_change_df.tail(top_bottom_display_count)])
                    display_change_data = display_change_data.sort_values("Net_Change", ascending=False)

                st.subheader("Net Population Change (Thousands)")  # 영어 제목
                fig2, ax2 = plt.subplots(figsize=(12, max(6, len(display_change_data) * 0.45)))

                colors = ['lightcoral' if x < 0 else 'lightskyblue' for x in display_change_data["Net_Change"]]
                bars = sns.barplot(x=display_change_data["Net_Change"] / 1000, y=display_change_data.index,
                                   palette=colors, ax=ax2)  # 천명 단위로 변경

                ax2.set_xlabel("Population Net Change (Thousands)", fontsize=12)  # 영어 레이블
                ax2.set_ylabel("Region", fontsize=12)  # 영어 레이블
                ax2.set_title(
                    f"Regional Population Net Change ({start_year_calc}–{end_year_calc}, Top/Bottom {top_bottom_display_count})",
                    fontsize=16)  # 영어 제목
                ax2.grid(axis="x", linestyle="--", alpha=0.5)

                # 막대 그래프에 값 표시
                for bar in bars.patches:
                    ax2.text(bar.get_width() + (50 if bar.get_width() > 0 else -150),
                             bar.get_y() + bar.get_height() / 2,
                             f'{int(bar.get_width() * 1000):,+d}',  # 원래 값으로 다시 변환하여 표시, 천단위 콤마, 부호
                             va='center', ha='left' if bar.get_width() > 0 else 'right',
                             color='dimgray', fontsize=9)

                plt.tight_layout()
                st.pyplot(fig2)

                st.markdown(
                    "> **Analysis Point:** This graph shows how much the population of each region has increased or decreased over a specific period, helping to identify regions with active population inflow/outflow."
                )  # 영어 문구

                st.subheader("Population Change Rate (%)")  # 영어 제목
                fig_rate, ax_rate = plt.subplots(figsize=(12, max(6, len(display_change_data) * 0.45)))

                colors_rate = ['lightcoral' if x < 0 else 'lightskyblue' for x in
                               display_change_data["Change_Rate (%)"]]
                bars_rate = sns.barplot(x=display_change_data["Change_Rate (%)"], y=display_change_data.index,
                                        palette=colors_rate, ax=ax_rate)

                ax_rate.set_xlabel("Population Change Rate (%)", fontsize=12)  # 영어 레이블
                ax_rate.set_ylabel("Region", fontsize=12)  # 영어 레이블
                ax_rate.set_title(
                    f"Regional Population Change Rate ({start_year_calc}–{end_year_calc}, Top/Bottom {top_bottom_display_count})",
                    fontsize=16)  # 영어 제목
                ax_rate.grid(axis="x", linestyle="--", alpha=0.5)

                # 막대 그래프에 값 표시
                for bar in bars_rate.patches:
                    ax_rate.text(bar.get_width() + (0.5 if bar.get_width() > 0 else -0.5),
                                 bar.get_y() + bar.get_height() / 2,
                                 f'{bar.get_width():+.2f}%',
                                 va='center', ha='left' if bar.get_width() > 0 else 'right',
                                 color='dimgray', fontsize=9)

                plt.tight_layout()
                st.pyplot(fig_rate)
                st.markdown(
                    "> **Analysis Point:** This graph visualizes the percentage change in population, offering a relative perspective on growth or decline, which can be particularly useful for comparing regions of different sizes."
                )  # 영어 문구

                with st.expander("Detailed Population Change Data"):  # 영어 문구
                    # 숫자에 천단위 콤마와 부호 추가, 변화율은 % 표시
                    formatted_df = population_change_df.copy()
                    formatted_df["Start_Population"] = formatted_df["Start_Population"].astype(int).apply(
                        lambda x: f"{x:,.0f}")
                    formatted_df["End_Population"] = formatted_df["End_Population"].astype(int).apply(
                        lambda x: f"{x:,.0f}")
                    formatted_df["Net_Change"] = formatted_df["Net_Change"].astype(int).apply(lambda x: f"{x:+,.0f}")
                    formatted_df["Change_Rate (%)"] = formatted_df["Change_Rate (%)"].apply(lambda x: f"{x:+.2f}%")
                    st.dataframe(formatted_df, use_container_width=True)

        with tabs[3]:  # 4) 연간 지역별 증감 기록
            st.header("📑 Top/Bottom Annual Regional Population Change Records")  # 영어 제목
            st.markdown("""
            Displays records of the largest annual population changes (increase or decrease) for each region.
            This helps in identifying regions with significant demographic shifts in a particular year.
            """)  # 영어 문구

            start_year_delta = st.session_state.get('start_year_for_analysis')
            end_year_delta = st.session_state.get('last_year')

            if start_year_delta is None or end_year_delta is None:
                st.warning("Analysis period setting is required. Please check the sidebar.")  # 영어 문구
                return

            df_yearly_delta = (
                df[df["지역"] != "전국"]
                .sort_values(["지역", "연도"])
                .assign(Annual_Change=lambda x: x.groupby("지역")["인구"].diff())  # 영어 컬럼명
                .dropna(subset=["Annual_Change"])
            )
            # 지역명 영어 번역
            df_yearly_delta['지역'] = df_yearly_delta['지역'].map(
                lambda x: REGION_TRANSLATION_MAP.get(x, x.replace(' (중복)', ' (Dup)')))

            filtered_yearly_delta = df_yearly_delta[df_yearly_delta["연도"].between(start_year_delta, end_year_delta)]

            if filtered_yearly_delta.empty:
                st.warning(
                    f"No annual change data available for the selected period ({start_year_delta}–{end_year_delta}).")  # 영어 문구
            else:
                num_records_to_display = st.slider("Number of Annual Change Records to Display (Top/Bottom)", 10, 200,
                                                   100)  # 영어 문구

                top_and_bottom_records = (
                    filtered_yearly_delta
                    .assign(abs_change=lambda x: x["Annual_Change"].abs())
                    .sort_values("abs_change", ascending=False)
                    .head(num_records_to_display)
                    .drop(columns="abs_change")
                    .reset_index(drop=True)
                )

                max_abs_delta = top_and_bottom_records["Annual_Change"].abs().max()
                styled_table = (
                    top_and_bottom_records.style
                    .background_gradient(cmap="coolwarm", vmin=-max_abs_delta, vmax=max_abs_delta,
                                         subset=["Annual_Change"])  # 영어 컬럼명
                    .format({
                        "인구": "{:,.0f}",
                        "Annual_Change": "{:+,.0f}",  # 영어 컬럼명
                        "출생아수(명)": "{:,.0f}",  # 임시로 한글 유지, 데이터에 따라 변경 필요
                        "사망자수(명)": "{:,.0f}"  # 임시로 한글 유지, 데이터에 따라 변경 필요
                    })
                )
                st.dataframe(styled_table, use_container_width=True)
                st.markdown(
                    f"> **Note:** The 'Annual_Change' column represents the year-on-year population change.")  # 영어 문구

        with tabs[4]:  # 5) 지역별 인구 구성 변화
            st.header("📈 Regional Population Composition Change Trend and Pivot Table")  # 영어 제목
            st.markdown("""
            Visualizes how regional population distribution has changed annually,
            and the shifting proportion of each region within the total population.
            """)  # 영어 문구

            population_pivot = pd.pivot_table(df[df["지역"] != "전국"], index="연도", columns="지역", values="인구",
                                              aggfunc="sum").sort_index()

            if population_pivot.empty:
                st.warning(
                    "No data to create pivot table and graphs. Please check if regional data (excluding 'National') exists.")  # 영어 문구
            else:
                st.subheader("📚 Annual Regional Population Pivot Table")  # 영어 제목
                # 컬럼명 번역
                population_pivot.columns = [REGION_TRANSLATION_MAP.get(col, col.replace(' (중복)', ' (Dup)')) for col in
                                            population_pivot.columns]
                st.dataframe(population_pivot.applymap(lambda x: f"{x:,.0f}"), use_container_width=True)

                st.subheader("📊 Regional Population Accumulated Change Area Chart")  # 영어 제목
                all_regions_translated = [col for col in population_pivot.columns]

                if len(all_regions_translated) > 20:
                    selected_regions_for_area = st.multiselect(
                        "Select Regions for Area Chart (Max 20 Recommended)",  # 영어 문구
                        options=all_regions_translated,
                        default=all_regions_translated[:min(5, len(all_regions_translated))]
                    )
                    plot_data_for_area = population_pivot[selected_regions_for_area]
                else:
                    plot_data_for_area = population_pivot

                if plot_data_for_area.empty:
                    st.warning("No regions selected for the accumulated area chart.")  # 영어 문구
                else:
                    sns.set_theme(style="whitegrid")
                    fig3, ax3 = plt.subplots(figsize=(14, 8))

                    colors_for_area = plt.cm.get_cmap('tab20',
                                                      len(plot_data_for_area.columns))  # 'Spectral' 대신 'tab20'으로 변경

                    ax3.stackplot(plot_data_for_area.index, plot_data_for_area.T, labels=plot_data_for_area.columns,
                                  colors=[colors_for_area(i) for i in range(len(plot_data_for_area.columns))])

                    ax3.set_xlabel("Year", fontsize=12)  # 영어 레이블
                    ax3.set_ylabel("Total Population (Count)", fontsize=12)  # 영어 레이블
                    ax3.set_title("Annual Regional Population Composition Change (Accumulated)", fontsize=16)  # 영어 제목
                    ax3.legend(loc="upper left", bbox_to_anchor=(1.02, 1), title="Region", ncol=1, fontsize=10)  # 영어 제목
                    ax3.margins(0, 0)
                    plt.tight_layout()
                    st.pyplot(fig3)
                    st.markdown(
                        "> **Analysis Point:** This graph visually displays the changing relative proportion of each region within the total population over time, useful for identifying growth or decline in specific areas."
                    )  # 영어 문구

    def _preprocess_population_data(self, df_raw):
        # 원본 데이터를 복사하여 전처리
        df_processed = df_raw.copy()

        # '세종' 지역의 모든 데이터 열의 결측치('-')를 숫자 0으로 치환
        # '세종' 지역에 해당하는 행들을 먼저 필터링
        sejong_mask = df_processed['지역'] == '세종특별자치시'
        if sejong_mask.any():  # '세종' 지역 데이터가 있는 경우에만 처리
            # '세종' 지역의 모든 컬럼에서 '-'를 0으로 치환
            df_processed.loc[sejong_mask] = df_processed.loc[sejong_mask].replace('-', '0')

        # '인구', '출생아수(명)', '사망자수(명)' 열을 숫자로 변환
        # errors='coerce'를 사용하여 숫자로 변환할 수 없는 값은 NaN으로 만들고, fillna(0)으로 NaN을 0으로 채움
        numeric_cols = ["연도", "인구", "출생아수(명)", "사망자수(명)"]
        for col in numeric_cols:
            if col in df_processed.columns:
                df_processed[col] = pd.to_numeric(df_processed[col], errors="coerce").fillna(0)

        # 중복 처리: '지역' 컬럼에 "(중복)" 추가
        # '연도'와 '지역'을 기준으로 중복 판단 후 첫 번째 등장하는 행만 유지하고, 그 이후의 중복 행에 "(중복)" 추가
        dup_mask = df_processed.duplicated(subset=['연도', '지역'], keep="first")
        df_processed.loc[dup_mask, "지역"] = df_processed.loc[dup_mask, "지역"].astype(str) + " (중복)"

        return df_processed


# ---------------------
# 페이지 객체 생성 (기존 설정 유지)
# ---------------------
Page_Login = st.Page(Login, title="로그인", icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="회원가입", icon="📝", url_path="register")
Page_FindPW = st.Page(FindPassword, title="비밀번호 찾기", icon="🔎", url_path="find-password")
Page_Home = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="홈", icon="🏠", url_path="home",
                    default=True)
Page_User = st.Page(UserInfo, title="내 정보", icon="👤", url_path="user-info")
Page_Logout = st.Page(Logout, title="로그아웃", icon="�", url_path="logout")
Page_EDA = st.Page(EDA, title="데이터 분석", icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행 (기존 설정 유지)
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()
�