# app.py ─ Population Trends Dashboard
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io

# ────────────────────────────────────────────────
# 기본 설정
# ────────────────────────────────────────────────
st.set_page_config(page_title="Population Trends Dashboard", layout="wide")
st.title("📊 Population Trends 대시보드")

# ────────────────────────────────────────────────
# 1) CSV 업로드
# ────────────────────────────────────────────────
file = st.file_uploader("population_trends.csv 파일을 업로드해 주세요", type="csv")

if file is None:
    st.info("먼저 CSV 파일을 업로드해야 한다.")
    st.stop()

# ────────────────────────────────────────────────
# 2) 데이터 로드 & 전처리
# ────────────────────────────────────────────────
df_raw = pd.read_csv(file)

# 필수 컬럼 존재 여부 검사
required_cols = {"연도", "지역", "인구"}
if not required_cols.issubset(df_raw.columns):
    st.error(f"CSV 파일에 {required_cols} 컬럼이 모두 포함돼야 한다.")
    st.stop()

# 숫자형 변환 및 결측치 0 치환
df_raw["연도"] = pd.to_numeric(df_raw["연도"], errors="coerce").astype(int)
df_raw["인구"] = pd.to_numeric(df_raw["인구"], errors="coerce")
df = df_raw.fillna(0)

# 중복 행 표시(첫 번째만 남기고 나머지 ‘(중복)’)
dup_mask = df.duplicated(keep="first")
df.loc[dup_mask, "지역"] += "(중복)"

# 최근 10년 범위 계산
last_year  = int(df["연도"].max())
start_year = last_year - 9

# ────────────────────────────────────────────────
# 3) 탭 UI
# ────────────────────────────────────────────────
tabs = st.tabs([
    "1) 데이터 요약",
    "2) 전국 인구 추이",
    "3) 최근 10년 지역별 변화량",
    "4) 연도별 증감 상위 100",
    "5) 피벗·누적 영역 그래프"
])

# ────────────────── 1) 데이터 요약 ──────────────────
with tabs[0]:
    st.subheader("✅ 데이터 샘플 (상위 10행)")
    st.dataframe(df.head(10), use_container_width=True)

    st.subheader("ℹ️ 데이터프레임 구조")
    buffer = io.StringIO()
    df.info(buf=buffer)
    st.text(buffer.getvalue())

    st.subheader("📈 요약 통계")
    st.dataframe(df.describe(), use_container_width=True)

# ────────────────── 2) 전국 인구 추이 ──────────────────
with tabs[1]:
    st.subheader("📉 전국 연도별 총인구 추이")
    national = df.groupby("연도")["인구"].sum().reset_index()

    fig1, ax1 = plt.subplots(figsize=(10, 5))
    ax1.plot(national["연도"], national["인구"], marker="o", color="skyblue")
    ax1.set_xlabel("연도")
    ax1.set_ylabel("총인구")
    ax1.set_title("전국 총인구 변화")
    ax1.grid(True)
    st.pyplot(fig1)

# ───────────── 3) 최근 10년 지역별 변화량 ─────────────
with tabs[2]:
    st.subheader(f"📊 {start_year}–{last_year} 지역별 인구 변화량")

    mask = df["연도"].between(start_year, last_year) & (df["지역"] != "전국")
    period = df[mask]

    start_pop = period[period["연도"] == start_year][["지역", "인구"]]\
                .set_index("지역").rename(columns={"인구": "start"})
    end_pop   = period[period["연도"] == last_year][["지역", "인구"]]\
                .set_index("지역").rename(columns={"인구": "end"})

    change = end_pop.join(start_pop, how="inner")
    change["변화량"] = change["end"] - change["start"]
    change_sorted = change.sort_values("변화량", ascending=False)

    fig2, ax2 = plt.subplots(figsize=(10, 8))
    ax2.barh(change_sorted.index, change_sorted["변화량"], color="steelblue")
    ax2.invert_yaxis()
    ax2.set_xlabel("인구 변화량")
    ax2.set_title("최근 10년 지역별 인구 변화량")
    ax2.grid(axis="x", linestyle="--", alpha=0.5)
    st.pyplot(fig2)

    st.dataframe(change_sorted, use_container_width=True)

# ───────────── 4) 연도별 증감 상위 100 ─────────────
with tabs[3]:
    st.subheader(f"📑 {start_year}–{last_year} 연도별 인구 증감 상위 100")

    delta_df = df[df["지역"] != "전국"].sort_values(["지역", "연도"])
    delta_df["증감"] = delta_df.groupby("지역")["인구"].diff()
    delta_recent = delta_df[delta_df["연도"].between(start_year, last_year)]\
                   .dropna(subset=["증감"])

    top100 = (delta_recent
              .assign(abs_change=lambda x: x["증감"].abs())
              .sort_values("abs_change", ascending=False)
              .head(100)
              .drop(columns="abs_change")
              .reset_index(drop=True))

    vmax = top100["증감"].abs().max()
    styled = (top100.style
              .background_gradient("RdBu", vmin=-vmax, vmax=vmax, subset=["증감"])
              .format({"인구": "{:,.0f}", "증감": "{:+,.0f}"}))

    st.dataframe(styled, use_container_width=True)

# ───────────── 5) 피벗 테이블·누적 영역 ─────────────
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
    ax3.set_title("연도별 지역 누적 인구 그래프")
    ax3.legend(loc="upper left", bbox_to_anchor=(1.02, 1), title="지역")
    ax3.margins(0, 0)
    st.pyplot(fig3)
