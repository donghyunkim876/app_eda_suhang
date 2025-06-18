import streamlit as st
import pyrebase4 as pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Matplotlib 한글 폰트 설정 (Windows 기준, Mac/Linux는 폰트명 변경 필요)
plt.rcParams['font.family'] = 'Malgun Gothic' # Windows users, use 'Malgun Gothic'
# For macOS: 'AppleGothic'
# For Linux: 'NanumGothic' (requires installation: sudo apt-get install fonts-nanum-extra)
plt.rcParams['axes.unicode_minus'] = False # 마이너스 폰트 깨짐 방지

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
    st.session_state.df_population_eda = None # 인구 데이터용 DataFrame
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
        st.text_input("이메일", value=email, disabled=True, help="이메일은 변경할 수 없습니다.") # 이메일 변경 불가하도록
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
        st.title("📊 인구 데이터 통계 분석")

        uploaded_file = st.file_uploader("인구 동향 데이터 파일 업로드 (population_trends.csv)", type="csv")

        # 파일이 업로드되지 않았거나, 새로운 파일이 업로드된 경우 데이터 로드 및 전처리
        if uploaded_file is None:
            st.info("👆 분석을 시작하려면 CSV 파일을 업로드해 주세요. (예: population_trends.csv)")
            st.session_state.df_population_eda = None
            st.session_state.uploaded_population_file_id = None
            return
        elif st.session_state.uploaded_population_file_id != uploaded_file.file_id:
            df_raw = pd.read_csv(uploaded_file)
            st.session_state.df_population_eda = self._preprocess_population_data(df_raw)
            st.session_state.uploaded_population_file_id = uploaded_file.file_id
            st.success("🎉 데이터셋이 성공적으로 로드되고 분석 준비를 마쳤습니다!")

        df = st.session_state.df_population_eda

        st.sidebar.header("📊 분석 기간 설정")
        if df is not None and '연도' in df.columns:
            all_years = sorted(df["연도"].unique())
            if all_years:
                min_year = int(all_years[0])
                max_year = int(all_years[-1])
                
                # 분석할 연도 범위 슬라이더
                selected_period_years = st.sidebar.slider(
                    "최근 몇 년간의 데이터를 분석할까요?",
                    min_value=1,
                    max_value=max_year - min_year + 1,
                    value=min(10, max_year - min_year + 1), # 기본값은 10년 또는 전체 기간 중 짧은 것
                    step=1
                )
                
                analysis_start_year = max_year - selected_period_years + 1
                st.sidebar.markdown(f"**선택된 분석 범위:** \n- **시작 연도:** {analysis_start_year}년 \n- **종료 연도:** {max_year}년")
                
                st.session_state.start_year_for_analysis = analysis_start_year
                st.session_state.last_year = max_year
                st.session_state.years_to_analyze = selected_period_years
            else:
                st.sidebar.info("데이터에 '연도' 정보가 없어 기간 설정을 할 수 없습니다.")
        else:
            st.sidebar.info("데이터 로드를 기다리는 중입니다...")

        tabs = st.tabs([
            "1. 데이터 개요",
            "2. 전국 핵심 지표 추이",
            "3. 지역별 인구 변화 순위",
            "4. 연간 지역별 증감 기록",
            "5. 지역별 인구 구성 변화"
        ])

        with tabs[0]: # 1) 데이터 개요
            st.header("🔍 데이터셋 기본 정보 확인")
            st.markdown("업로드된 데이터셋의 구조, 내용, 그리고 품질을 한눈에 파악합니다.")

            st.subheader("📋 데이터 미리보기 (상위 5행)")
            st.dataframe(df.head(), use_container_width=True)

            st.subheader("📊 데이터프레임 컬럼 정보 (df.info())")
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.text(buffer.getvalue())

            st.subheader("📈 주요 통계 요약 (df.describe())")
            st.dataframe(df.describe().applymap(lambda x: f"{x:,.2f}"), use_container_width=True) # 소수점 두 자리까지, 콤마

            st.subheader("🚫 데이터 품질 검사 결과")
            missing = df.isnull().sum()
            total_rows = len(df)
            col1, col2 = st.columns(2)
            with col1:
                st.metric("총 결측값 수", f"{missing.sum():,d}개")
                if missing.sum() == 0:
                    st.success("모든 데이터에 결측값이 없습니다. 👍")
                else:
                    st.warning("일부 컬럼에 결측값이 있습니다. (전처리 완료)")
                    st.dataframe(missing[missing > 0].reset_index().rename(columns={0: '결측값 개수', 'index': '컬럼명'}), hide_index=True)
            
            with col2:
                duplicates = df.duplicated().sum()
                st.metric("총 중복 행 수", f"{duplicates:,d}개")
                if duplicates > 0:
                    st.warning(f"데이터셋에 {duplicates:,d}개의 중복 행이 발견되었습니다. (전처리 완료: 지역명에 '(중복)' 추가)")
                else:
                    st.success("중복된 행이 없습니다. ✨")


        with tabs[1]: # 2) 전국 핵심 지표 추이
            st.header("📉 전국 인구 및 출생/사망 지표 추이")
            st.markdown("""
            대한민국 전체 인구와 인구 변동에 영향을 미치는 출생아 수, 사망자 수의 연도별 변화를 시각적으로 분석합니다.
            """)
            nationwide_data = df[df["지역"] == "전국"].sort_values("연도")

            if nationwide_data.empty:
                st.warning("⚠️ '전국' 데이터가 없습니다. 원본 파일을 확인해 주세요.")
            else:
                fig1, ax1 = plt.subplots(figsize=(14, 7))
                
                # 인구 추이
                ax1.plot(nationwide_data["연도"], nationwide_data["인구"], marker="o", linestyle="-", color="#1f77b4", label="총 인구", linewidth=2)
                
                # 출생아수, 사망자수 (보조 y축 사용)
                ax2 = ax1.twinx()
                if '출생아수(명)' in nationwide_data.columns:
                    ax2.plot(nationwide_data["연도"], nationwide_data["출생아수(명)"], marker="x", linestyle="--", color="#2ca02c", label="출생아수", linewidth=1.5)
                if '사망자수(명)' in nationwide_data.columns:
                    ax2.plot(nationwide_data["연도"], nationwide_data["사망자수(명)"], marker="s", linestyle=":", color="#d62728", label="사망자수", linewidth=1.5)

                ax1.set_title("전국 연도별 인구 및 주요 지표 변화", fontsize=18, pad=20)
                ax1.set_xlabel("연도", fontsize=14)
                ax1.set_ylabel("인구 수 (명)", fontsize=14, color="#1f77b4")
                ax2.set_ylabel("출생/사망자 수 (명)", fontsize=14)
                
                ax1.tick_params(axis='y', labelcolor="#1f77b4")
                ax2.tick_params(axis='y')

                # 범례 통합
                lines, labels = ax1.get_lines(), [l.get_label() for l in ax1.get_lines()]
                lines2, labels2 = ax2.get_lines(), [l.get_label() for l in ax2.get_lines()]
                ax2.legend(lines + lines2, labels + labels2, loc='upper left', bbox_to_anchor=(0.0, 1.0))
                
                ax1.grid(True, linestyle='--', alpha=0.6)
                st.pyplot(fig1)

                st.markdown(
                    "> **분석 요점:** 이 그래프는 전국 인구의 장기적인 추세와 함께, 출생 및 사망이라는 핵심적인 인구 변동 요인이 시간에 따라 어떻게 변화해왔는지를 보여줍니다. 인구 감소의 원인과 속도를 파악하는 데 유용합니다."
                )

        with tabs[2]: # 3) 최근 선택 기간 지역별 변화량
            st.header(f"📊 최근 {st.session_state.get('years_to_analyze', 'N')}년 ({st.session_state.get('start_year_for_analysis', 'Start')}–{st.session_state.get('last_year', 'End')}) 지역별 인구 순변화량")
            st.markdown("""
            사이드바에서 지정한 기간 동안 각 행정 구역의 인구 변화량을 계산하여,
            가장 인구가 많이 늘거나 줄어든 지역의 순위를 시각화합니다.
            """)
            
            start_year_calc = st.session_state.get('start_year_for_analysis')
            end_year_calc = st.session_state.get('last_year')

            if start_year_calc is None or end_year_calc is None:
                st.warning("분석 기간 설정이 필요합니다. 사이드바를 확인해주세요.")
                return

            filtered_df_period = df[(df["연도"].between(start_year_calc, end_year_calc)) & (df["지역"] != "전국")]

            if filtered_df_period.empty:
                st.warning(f"선택된 기간 ({start_year_calc}년 – {end_year_calc}년)에 해당하는 지역별 인구 데이터가 없습니다.")
            else:
                pop_start_df = filtered_df_period[filtered_df_period["연도"] == start_year_calc][["지역", "인구"]].set_index("지역").rename(columns={"인구": "시작_인구"})
                pop_end_df = filtered_df_period[filtered_df_period["연도"] == end_year_calc][["지역", "인구"]].set_index("지역").rename(columns={"인구": "종료_인구"})
                
                population_change_df = pop_end_df.join(pop_start_df, how="inner")
                population_change_df["변화량"] = population_change_df["종료_인구"] - population_change_df["시작_인구"]
                population_change_df = population_change_df.sort_values("변화량", ascending=False)
                
                top_bottom_display_count = st.slider("인구 변화 상위/하위 몇 개 지역을 볼까요?", 5, min(30, len(population_change_df)), 10)
                
                if top_bottom_display_count * 2 > len(population_change_df):
                    display_change_data = population_change_df
                else:
                    display_change_data = pd.concat([population_change_df.head(top_bottom_display_count), population_change_df.tail(top_bottom_display_count)])
                    display_change_data = display_change_data.sort_values("변화량", ascending=False)

                fig2, ax2 = plt.subplots(figsize=(12, max(6, len(display_change_data) * 0.45))) # 그래프 크기 동적 조절
                
                # 변화량에 따라 색상 다르게 적용
                colors = ['lightcoral' if x < 0 else 'lightskyblue' for x in display_change_data["변화량"]]
                sns.barplot(x=display_change_data["변화량"], y=display_change_data.index, palette=colors, ax=ax2)
                
                ax2.set_xlabel("인구 변화량 (명)", fontsize=12)
                ax2.set_ylabel("지역명", fontsize=12)
                ax2.set_title(f"{start_year_calc}년 – {end_year_calc}년 지역별 인구 순변화량 (상위/하위 {top_bottom_display_count}개)", fontsize=16)
                ax2.grid(axis="x", linestyle="--", alpha=0.5)
                plt.tight_layout() # 레이아웃 조정
                st.pyplot(fig2)

                st.markdown(
                    "> **분석 요점:** 특정 기간 동안 각 지역의 인구가 얼마나 증가하거나 감소했는지 보여주며, 인구 유입/유출이 활발한 지역을 식별하는 데 도움을 줍니다."
                )
                with st.expander("자세한 인구 변화량 데이터 보기"):
                    st.dataframe(population_change_df[["시작_인구", "종료_인구", "변화량"]].astype(int).applymap(lambda x: f"{x:,.0f}"), use_container_width=True)


        with tabs[3]: # 4) 연간 지역별 증감 기록
            st.header("📑 연도별 지역 인구 증감 최고/최저 기록")
            st.markdown("""
            매년 전국 각 지역에서 발생한 인구 증감량 중 가장 큰 변화를 보인 기록들을 보여줍니다.
            이는 특정 연도에 급격한 인구 변동이 있었던 지역을 찾아내는 데 유용합니다.
            """)

            start_year_delta = st.session_state.get('start_year_for_analysis')
            end_year_delta = st.session_state.get('last_year')

            if start_year_delta is None or end_year_delta is None:
                st.warning("분석 기간 설정이 필요합니다. 사이드바를 확인해주세요.")
                return

            df_yearly_delta = (
                df[df["지역"] != "전국"]
                .sort_values(["지역", "연도"])
                .assign(연간_증감량=lambda x: x.groupby("지역")["인구"].diff())
                .dropna(subset=["연간_증감량"])
            )

            filtered_yearly_delta = df_yearly_delta[df_yearly_delta["연도"].between(start_year_delta, end_year_delta)]

            if filtered_yearly_delta.empty:
                st.warning(f"선택된 기간 ({start_year_delta}년 – {end_year_delta}년)에 해당하는 연간 증감 데이터가 없습니다.")
            else:
                num_records_to_display = st.slider("표시할 상위/하위 연간 증감 기록 개수", 10, 200, 100)

                top_and_bottom_records = (
                    filtered_yearly_delta
                    .assign(abs_change=lambda x: x["연간_증감량"].abs())
                    .sort_values("abs_change", ascending=False)
                    .head(num_records_to_display)
                    .drop(columns="abs_change")
                    .reset_index(drop=True)
                )

                max_abs_delta = top_and_bottom_records["연간_증감량"].abs().max()
                styled_table = (
                    top_and_bottom_records.style
                    .background_gradient(cmap="coolwarm", vmin=-max_abs_delta, vmax=max_abs_delta, subset=["연간_증감량"]) # 색상 팔레트 변경
                    .format({
                        "인구": "{:,.0f}",
                        "연간_증감량": "{:+,.0f}",
                        "출생아수(명)": "{:,.0f}",
                        "사망자수(명)": "{:,.0f}"
                    })
                )
                st.dataframe(styled_table, use_container_width=True)
                st.markdown(f"> **참고:** '연간_증감량' 컬럼은 해당 연도 인구에서 전년도 인구를 뺀 값입니다.")

        with tabs[4]: # 5) 지역별 인구 구성 변화
            st.header("📈 지역별 인구 구성 변화 추이 및 피벗 테이블")
            st.markdown("""
            각 연도별로 지역별 인구 분포가 어떻게 변화해왔는지,
            그리고 전체 인구에서 각 지역이 차지하는 비중의 변화를 시각적으로 보여줍니다.
            """)
            
            pivot = pd.pivot_table(df[df["지역"] != "전국"], index="연도", columns="지역", values="인구", aggfunc="sum").sort_index()
            
            if pivot.empty:
                st.warning("데이터가 없어 피벗 테이블 및 그래프를 생성할 수 없습니다. '전국'을 제외한 지역 데이터가 있는지 확인해주세요.")
            else:
                st.subheader("📚 연도별 지역별 인구 피벗 테이블")
                st.dataframe(pivot.applymap(lambda x: f"{x:,.0f}"), use_container_width=True)

                st.subheader("📊 지역별 인구 누적 변화 영역 그래프")
                all_regions = [col for col in pivot.columns]
                
                # 너무 많은 지역은 선택적으로 표시
                if len(all_regions) > 20:
                    selected_regions_for_area = st.multiselect(
                        "누적 영역 그래프에 포함할 지역 선택 (최대 20개 권장)",
                        options=all_regions,
                        default=all_regions[:min(5, len(all_regions))] # 기본으로 상위 5개 지역 (가나다순)
                    )
                    plot_data_for_area = pivot[selected_regions_for_area]
                else:
                    plot_data_for_area = pivot
                    
                if plot_data_for_area.empty:
                    st.warning("선택된 지역이 없어 누적 영역 그래프를 그릴 수 없습니다.")
                else:
                    sns.set_theme(style="whitegrid") # 테마 변경
                    fig3, ax3 = plt.subplots(figsize=(14, 8))
                    
                    # 'tab20' 팔레트가 아닌 다른 팔레트 사용 또는 사용자 정의 색상
                    colors_for_area = plt.cm.get_cmap('Spectral', len(plot_data_for_area.columns)) 
                    
                    ax3.stackplot(plot_data_for_area.index, plot_data_for_area.T, labels=plot_data_for_area.columns, colors=[colors_for_area(i) for i in range(len(plot_data_for_area.columns))])
                    
                    ax3.set_xlabel("연도", fontsize=12)
                    ax3.set_ylabel("총 인구 수", fontsize=12)
                    ax3.set_title("연도별 지역 인구 구성 변화 (누적)", fontsize=16)
                    ax3.legend(loc="upper left", bbox_to_anchor=(1.02, 1), title="지역", ncol=1, fontsize=10) # 범례 컬럼 수 조정
                    ax3.margins(0, 0)
                    plt.tight_layout() # 레이아웃 조정
                    st.pyplot(fig3)
                    st.markdown(
                        "> **분석 요점:** 전체 인구에서 각 지역이 차지하는 상대적인 비중의 변화를 시간 흐름에 따라 시각적으로 보여주며, 특정 지역의 성장 또는 쇠퇴를 파악하는 데 유용합니다."
                    )


    def _preprocess_population_data(self, df_raw):
        # 원본 데이터를 복사하여 전처리
        df_processed = df_raw.copy()

        # 사용자 제공 코드에서 숫자형 컬럼 변환 및 결측치 처리
        numeric_cols = ["연도", "인구", "출생아수(명)", "사망자수(명)"]
        for col in numeric_cols:
            if col in df_processed.columns:
                # 숫자로 변환할 수 없는 값은 NaN으로 만든 후 0으로 채움
                df_processed[col] = pd.to_numeric(df_processed[col], errors="coerce").fillna(0)
        
        # 중복 처리: '지역' 컬럼에 "(중복)" 추가
        # 첫 번째 등장하는 행만 유지하고, 그 이후의 중복 행에 표시
        dup_mask = df_processed.duplicated(subset=['연도', '지역'], keep="first") # '연도'와 '지역'을 기준으로 중복 판단
        df_processed.loc[dup_mask, "지역"] = df_processed.loc[dup_mask, "지역"].astype(str) + " (중복)" # 문자열로 변환 후 추가

        return df_processed


# ---------------------
# 페이지 객체 생성 (기존 설정 유지)
# ---------------------
Page_Login    = st.Page(Login,    title="로그인",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="회원가입", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="비밀번호 찾기", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="홈", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="내 정보", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="로그아웃",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="데이터 분석",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행 (기존 설정 유지)
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()
