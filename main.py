# 표준 라이브러리
import datetime
from io import BytesIO
import os

# 서드파티 라이브러리
import streamlit as st
import time
import pandas as pd
import FinanceDataReader as fdr
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from dotenv import load_dotenv
import numpy as np


load_dotenv()

# 회사별 DF 불러오기
@st.cache_data
def get_krx_company_list() -> pd.DataFrame:
    try:
        url = 'http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13'
        df_listing = pd.read_html(url, header=0, flavor='bs4', encoding='EUC-KR')[0]
        df_listing = df_listing[['회사명', '종목코드']].copy()
        df_listing['종목코드'] = df_listing['종목코드'].apply(lambda x: f'{x:06}')
        return df_listing
    except Exception as e:
        st.error(f"상장사 명단을 불러오는 데 실패했습니다: {e}")
        return pd.DataFrame(columns=['회사명', '종목코드'])

# 종목코드|회사명으로 불러오기 가능
def get_stock_code_by_company(company_name: str) -> str:
    if company_name.isdigit() and len(company_name) == 6:
        return company_name

    company_df = get_krx_company_list()
    codes = company_df[company_df['회사명'] == company_name]['종목코드'].values
    if len(codes) > 0:
        return codes[0]
    else:
        raise ValueError(f"'{company_name}'을 찾을 수 없습니다. 종목코드 6자리를 직접 입력해보세요.")




#사이드바 설정
company_name = st.sidebar.text_input('조회할 회사를 입력하세요')
chart_type = st.sidebar.radio("Select Chart Type", ("Candle_Stick", "Line"), index=0)

today = datetime.datetime.today()
jan_1 = datetime.date(today.year, 1, 1)

selected_dates = st.sidebar.date_input(
    '조회할 기간을 선택하세요',
    (jan_1, today),
    format="MM.DD.YYYY",
)


confirm_btn = st.sidebar.button('조회하기')

#인트로 화면
if ("price_df" not in st.session_state) and (not confirm_btn):

    st.title("📈 주가 대시보드")

    st.caption(
        "회사명 또는 종목코드(6자리)를 입력하고 "
        "기간을 선택한 뒤 ‘조회하기’를 눌러주세요."
    )

    with st.expander("사용 방법", expanded=True):
        st.markdown("""
        - **회사명**(예: 삼성전자) 또는 **종목코드 6자리** 입력  
        - 기간 선택 후 **조회하기** 클릭  
        """)

    st.divider()

    if "company_name" in st.session_state:
        st.info(
            f"최근 조회: **{st.session_state['company_name']}** "
            "(Pages에서 지표/뉴스 확인 가능)"
        )

    demo_on = st.toggle("주가 확인", value=True)

    if demo_on:
        n = 120
        idx = pd.date_range(
            end=pd.Timestamp.today().normalize(),
            periods=n,
            freq="B"
        )

        base = 10000 + np.cumsum(np.random.randn(n) * 80)
        close = pd.Series(base, index=idx).round()
        open_ = (close.shift(1).fillna(close.iloc[0]) + np.random.randn(n) * 30).round()
        high = pd.concat([open_, close], axis=1).max(axis=1) + abs(np.random.randn(n) * 50)
        low = pd.concat([open_, close], axis=1).min(axis=1) - abs(np.random.randn(n) * 50)

        demo_fig = go.Figure(
            data=[go.Candlestick(
                x=idx,
                open=open_,
                high=high,
                low=low,
                close=close
            )]
        )

        demo_fig.update_layout(
            title="캔들차트로 주가 흐름 미리보기",
            xaxis_rangeslider_visible=False,
            height=420,
            margin=dict(l=10, r=10, t=50, b=10),
        )

        cA, cB, cC = st.columns(3)
        cA.metric("현재가", f"{close.iloc[-1]:,.0f}")
        cB.metric(
            "기간 수익률",
            f"{((close.iloc[-1]/close.iloc[0]-1)*100):.2f}%"
        )
        dd = (close / close.cummax() - 1).min() * 100
        cC.metric("최대낙폭", f"{dd:.2f}%")

        st.plotly_chart(demo_fig, use_container_width=True)

# 회사에 대한 주가 데이터 수집
if confirm_btn:
    try:
        with st.spinner('데이터를 수집하는 중...'):
            stock_code = get_stock_code_by_company(company_name)
            start_date = selected_dates[0].strftime("%Y%m%d")
            end_date = selected_dates[1].strftime("%Y%m%d")
            price_df = fdr.DataReader(stock_code, start_date, end_date)

        if price_df.empty:
            st.info("해당 기간의 주가 데이터가 없습니다.")
        else:
            st.session_state["company_name"] = company_name
            st.session_state["price_df"] = price_df

    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")

# 주가 데이터가 있으면 차트 및 통계 표시
if "price_df" in st.session_state:
    price_df = st.session_state["price_df"]
    company_name = st.session_state.get("company_name", "Company")

    st.subheader(f"[{company_name}]")

    low_price = price_df['Low'].min()
    high_price = price_df['High'].max()
    low_date = price_df['Low'].idxmin()
    high_date = price_df['High'].idxmax()

    price_df["MA5"] = price_df["Close"].rolling(5).mean()
    price_df["MA20"] = price_df["Close"].rolling(20).mean()
    price_df["MA60"] = price_df["Close"].rolling(60).mean()
    price_df["MA120"] = price_df["Close"].rolling(120).mean()

#상단 최저가/최고가 메트릭
    close = price_df["Close"].dropna()
    if len(close) >= 2:
        start_close = float(close.iloc[0])
        end_close = float(close.iloc[-1])

        diff = end_close - start_close
        pct = (diff / start_close) * 100

        period_return = pct

        high_close = float(close.max())
        low_close = float(close.min())

        cummax = close.cummax()
        drawdown = (close / cummax) - 1.0
        mdd = float(drawdown.min() * 100)

        daily_ret = close.pct_change().dropna()
        vol_annual = float(daily_ret.std() * np.sqrt(252) * 100) if len(daily_ret) > 1 else 0.0

        arrow = "▲" if diff > 0 else ("▼" if diff < 0 else "—")
        diff_abs = abs(diff)

        c1, c2, c3, c4, c5, c6 = st.columns(6)

        c1.metric(
            "현재가",
            f"{end_close:,.0f}",
            f"{arrow} {abs(diff):,.0f} ({abs(diff_abs):.2f}%)"
        )

        c2.metric("기간 수익률", f"{period_return:.2f}%")
        c3.metric("최고가(종가)", f"{high_close:,.0f}")
        c4.metric("최저가(종가)", f"{low_close:,.0f}")
        c5.metric("최대낙폭(MDD)", f"{mdd:.2f}%")
        c6.metric("변동성(일간)", "-" if pd.isna(vol_annual) else f"{vol_annual:.2f}%")
    else:
        st.info("지표를 계산할 데이터가 부족합니다.")

#차트 그리기
    fig = make_subplots(rows=1, cols=1, shared_xaxes=True)


#radio에 따른 차트 그리기
    if chart_type == "Candle_Stick":
            fig.add_trace(
                go.Candlestick(
                    x=price_df.index,
                    open=price_df['Open'],
                    high=price_df['High'],
                    low=price_df['Low'],
                    close=price_df['Close'],
                    name="Price"
                ),
                row=1, col=1
            )
            fig.update_layout(xaxis_rangeslider_visible=False)
    else:
        fig.add_trace(
            go.Scatter(
                x=price_df.index,
                y=price_df['Close'],
                mode='lines',
                name='Close'
            ),
            row=1, col=1
        )

    fig.add_annotation(
        x=low_date, y=low_price,
        text=f"최저가<br>{low_price:,}",
        showarrow=True, arrowhead=2,
        arrowcolor="blue",
        font=dict(color="blue"),
        ay=40
    )

    fig.add_annotation(
        x=high_date, y=high_price,
        text=f"최고가<br>{high_price:,}",
        showarrow=True, arrowhead=2,
        arrowcolor="red",
        font=dict(color="red"),
        ay=-40
    )
    st.plotly_chart(fig, use_container_width=True)


#최저가/최고가 표 x,y좌표에 표식

    fig.add_annotation(
        x=low_date, y=low_price,
        text=f"최저가<br>{low_price:,}",
        showarrow=True, arrowhead=2,
        arrowcolor="blue",
        font=dict(color="blue"),
        ay=40
    )

    fig.add_annotation(
        x=high_date, y=high_price,
        text=f"최고가<br>{high_price:,}",
        showarrow=True, arrowhead=2,
        arrowcolor="red",
        font=dict(color="red"),
        ay=-40
    )

    fig.update_layout(
        title=f"{company_name} Stock Chart",
        xaxis_title="Date",
        yaxis_title="Price"
    )

    
#하락/상승 확률 메트릭
    LOOKBACK_DAYS = 60
    rets = price_df["Close"].pct_change().dropna().tail(LOOKBACK_DAYS)
    up_prob = (rets > 0).mean() * 100
    down_prob = 100 - up_prob

    c3, c4 = st.columns(2)
    c3.metric("오를까?👍", f"{up_prob:.1f}%")
    c4.metric("내릴까?👎️", f"{down_prob:.1f}%")

#최근 10일간 주가 데이터 엑셀 다운로드 버튼
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        price_df.to_excel(writer, index=True, sheet_name='Sheet1')

    st.download_button(
        label="📥 엑셀 파일 다운로드",
        data=output.getvalue(),
        file_name=f"{company_name}_주가.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
