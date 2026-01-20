import os
import datetime
import pandas as pd
import streamlit as st
import requests
import feedparser
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="재무제표 & 뉴스", layout="wide")
st.title("재무제표 & 최근 뉴스")

if "price_df" not in st.session_state or "company_name" not in st.session_state:
    st.warning("먼저 메인 페이지에서 종목을 조회해 주세요.")
    st.stop()

company_name = st.session_state["company_name"]

st.subheader(f"[{company_name}]")

tab1, tab2 = st.tabs(["재무제표", "최근 뉴스"])

with tab1:
    st.markdown(f"### {company_name}재무제표")
    dart_api_key = os.getenv("DART_API_KEY")

    if not dart_api_key:
        st.info(".env에 DART_API_KEY가 없어서 재무제표를 불러올 수 없어요. (예: DART_API_KEY=xxxxxxxx)")
        st.stop()

    try:
        import OpenDartReader

        dart = OpenDartReader(dart_api_key)

        corp_list = dart.corp_codes
        if corp_list is None or corp_list.empty:
            st.error("DART 기업 목록(corp_codes)을 불러오지 못했습니다.")
            st.stop()

        hit = corp_list[corp_list["corp_name"] == company_name]
        if hit.empty:
            hit = corp_list[corp_list["corp_name"].str.contains(company_name, na=False)]

        if hit.empty:
            st.error("DART에서 해당 회사명을 찾지 못했습니다. (회사명 정확히 입력 필요)")
            st.stop()

        corp_code = hit.iloc[0]["corp_code"]

        today = datetime.date.today()
        year = today.year

        y = st.selectbox("연도 선택", [year, year - 1, year - 2, year - 3], index=1)
        report = st.selectbox("보고서", ["11011(사업보고서)", "11012(반기보고서)", "11013(1분기)", "11014(3분기)"], index=0)
        reprt_code = report.split("(")[0]

        fs_div = st.selectbox("재무제표 종류", ["CFS(연결)", "OFS(별도)"], index=0).split("(")[0]

        fs = dart.finstate(corp=corp_code, bsns_year=y, reprt_code=reprt_code)

        if fs is None or (hasattr(fs, "empty") and fs.empty):
            st.info("해당 조건의 재무제표 데이터가 없습니다.")
            st.stop()

        if "fs_div" in fs.columns:
            fs_filtered = fs[fs["fs_div"] == fs_div].copy()

            # 연결(CFS)이 없는 회사는 비어있을 수 있어서 fallback
            if fs_filtered.empty:
                st.info(f"{fs_div} 데이터가 없어서 OFS(별도)로 표시합니다.")
                fs_filtered = fs[fs["fs_div"] == "OFS"].copy()
        else:
            fs_filtered = fs.copy()

        fs = fs_filtered


        if fs is None or (hasattr(fs, "empty") and fs.empty):
            st.info("해당 조건의 재무제표 데이터가 없습니다.")
        else:
            cols_keep = [c for c in ["fs_div", "sj_div", "sj_nm", "account_nm", "thstrm_amount", "frmtrm_amount", "bfefrmtrm_amount", "currency"] if c in fs.columns]
            fs_view = fs[cols_keep].copy()

            for col in ["thstrm_amount", "frmtrm_amount", "bfefrmtrm_amount"]:
                if col in fs_view.columns:
                    fs_view[col] = (
                        fs_view[col]
                        .astype(str)
                        .str.replace(",", "", regex=False)
                        .str.replace("None", "", regex=False)
                    )
                    fs_view[col] = pd.to_numeric(fs_view[col], errors="coerce")

            st.dataframe(fs_view, use_container_width=True)

            st.markdown("#### 빠른 요약(주요 계정)")
            key_accounts = ["매출액", "영업이익", "당기순이익", "자산총계", "부채총계", "자본총계"]
            if "account_nm" in fs_view.columns and "thstrm_amount" in fs_view.columns:
                summary = fs_view[fs_view["account_nm"].isin(key_accounts)][["account_nm", "thstrm_amount"]].dropna()
                if not summary.empty:
                    summary = summary.drop_duplicates("account_nm").set_index("account_nm")
                    st.table(summary.style.format("{:,.0f}"))
                else:
                    st.info("주요 계정(매출/이익/자산 등)이 이 보고서에서 바로 매칭되지 않았어요. 표에서 검색해서 확인해 주세요.")

    except Exception as e:
        st.error(f"재무제표 불러오기 오류: {e}")

with tab2:
    st.markdown("### 최근 뉴스 (Google News RSS)")

    q = st.text_input("검색 키워드", value=company_name)
    num = st.slider("기사 개수", 5, 30, 10)

    rss_url = "https://news.google.com/rss/search"
    params = {"q": q, "hl": "ko", "gl": "KR", "ceid": "KR:ko"}

    try:
        r = requests.get(rss_url, params=params, timeout=10)
        r.raise_for_status()
        feed = feedparser.parse(r.text)

        if not feed.entries:
            st.info("검색 결과가 없습니다.")
        else:
            for i, item in enumerate(feed.entries[:num], start=1):
                title = item.get("title", "")
                link = item.get("link", "")
                published = item.get("published", "")

                st.markdown(f"**{i}. {title}**")
                if published:
                    st.caption(published)
                if link:
                    st.write(link)
                st.divider()

    except Exception as e:
        st.error(f"뉴스 불러오기 오류: {e}")
