# eda_app.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io

class EDA:
    def __init__(self):
        self.run()

    def run(self):
        st.set_page_config(page_title="인구 데이터 EDA", layout="wide")  # ✨ 전체화면 설정
        st.title("📊 데이터 분석")

        file = st.file_uploader("population_trends.csv 파일을 업로드해 주세요", type="csv")
        if file is None:
            st.info("먼저 population_trends.csv 파일을 업로드해야 한다.")
            return

        df_raw = pd.read_csv(file)

        for col in ["연도", "인구", "출생아수(명)", "사망자수(명)"]:
            if col in df_raw.columns:
                df_raw[col] = pd.to_numeric(df_raw[col], errors="coerce")

        df = df_raw.fillna(0)
        dup_mask = df.duplicated(keep="first")
        df.loc[dup_mask, "지역"] = df.loc[dup_mask, "지역"] + "(중복)"

        st.sidebar.header("📂 데이터 정보")
        st.sidebar.write(f"총 행: {len(df):,d}개")
        st.sidebar.write(f"기간: {int(df['연도'].min())} – {int(df['연도'].max())}년")
        st.sidebar.markdown("---")

        last_year = int(df["연도"].max())
        start_year = last_year - 9

        tabs = st.tabs([
            "1) 데이터 요약",
            "2) 전국 인구 추이",
            "3) 최근 10년 지역별 변화량",
            "4) 연도별 증감 상위 100",
            "5) 피벗 테이블·누적 영역"
        ])

        with tabs[0]:
            st.subheader("✅ 전처리 데이터 샘플 (상위 10행)")
            st.dataframe(df.head(10), use_container_width=True)

            st.subheader("ℹ️ 데이터프레임 구조 (df.info())")
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.text(buffer.getvalue())

            st.subheader("📈 요약 통계 (df.describe())")
            st.dataframe(df.describe(), use_container_width=True)

        with tabs[1]:
            st.subheader("📉 전국 연도별 인구 추이")
            nationwide = df[df["지역"] == "전국"].sort_values("연도")

            fig1, ax1 = plt.subplots(figsize=(10, 5))
            ax1.plot(nationwide["연도"], nationwide["인구"], marker="o", linestyle="-", color="skyblue")
            ax1.set_title("전국 연도별 인구 추이", fontsize=14)
            ax1.set_xlabel("연도")
            ax1.set_ylabel("인구 수")
            ax1.grid(True)
            st.pyplot(fig1)

        with tabs[2]:
            st.subheader("📊 최근 10년 지역별 인구 변화량 순위")
            mask = (df["연도"].between(start_year, last_year) & (df["지역"] != "전국"))
            period_df = df[mask]

            pop_start = period_df[period_df["연도"] == start_year][["지역", "인구"]].set_index("지역").rename(columns={"인구": "start"})
            pop_end = period_df[period_df["연도"] == last_year][["지역", "인구"]].set_index("지역").rename(columns={"인구": "end"})
            change_df = pop_end.join(pop_start, how="inner")
            change_df["change"] = change_df["end"] - change_df["start"]
            change_df = change_df.sort_values("change", ascending=False)

            fig2, ax2 = plt.subplots(figsize=(10, 8))
            ax2.barh(change_df.index, change_df["change"], color="steelblue")
            ax2.set_xlabel("인구 변화량")
            ax2.set_ylabel("지역")
            ax2.set_title(f"{start_year}–{last_year}년 지역별 인구 변화량 순위")
            ax2.invert_yaxis()
            ax2.grid(axis="x", linestyle="--", alpha=0.5)
            st.pyplot(fig2)

            with st.expander("🔍 변화량 상세 데이터"):
                st.dataframe(change_df[["start", "end", "change"]], use_container_width=True)

        with tabs[3]:
            st.subheader("📑 지역·연도별 인구 증감 상위 100")

            df_delta = (
                df[df["지역"] != "전국"]
                .sort_values(["지역", "연도"])
                .assign(증감=lambda x: x.groupby("지역")["인구"].diff())
                .dropna(subset=["증감"])
            )

            delta_period = df_delta[df_delta["연도"].between(start_year, last_year)]

            top100 = (
                delta_period
                .assign(abs_change=lambda x: x["증감"].abs())
                .sort_values("abs_change", ascending=False)
                .head(100)
                .drop(columns="abs_change")
                .reset_index(drop=True)
            )

            max_abs = top100["증감"].abs().max()
            styled = (
                top100.style
                .background_gradient(cmap="RdBu", vmin=-max_abs, vmax=max_abs, subset=["증감"])
                .format({"인구": "{:,.0f}", "증감": "{:+,.0f}"})
            )
            st.dataframe(styled, use_container_width=True)

        with tabs[4]:
            st.subheader("🗺️ 연도·지역별 인구 피벗 테이블")
            pivot = pd.pivot_table(df, index="연도", columns="지역", values="인구", aggfunc="sum").sort_index()
            st.dataframe(pivot, use_container_width=True)

            st.subheader("📊 지역별 누적 영역 그래프")
            regions = [c for c in pivot.columns if c != "전국"]
            sns.set_theme(style="whitegrid")

            fig3, ax3 = plt.subplots(figsize=(12, 8))
            colors = sns.color_palette("tab20", n_colors=len(regions))
            ax3.stackplot(pivot.index, pivot[regions].T, labels=regions, colors=colors)
            ax3.set_xlabel("연도")
            ax3.set_ylabel("인구 수")
            ax3.set_title("연도별 지역 인구 누적 영역 그래프")
            ax3.legend(loc="upper left", bbox_to_anchor=(1.02, 1), title="지역")
            ax3.margins(0, 0)
            st.pyplot(fig3)

# ✅ 반드시 있어야 함
if __name__ == "__main__":
    EDA()
