import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Indicators", layout="wide")
st.title("부가 지표 (이동평균선 / 거래량)")

if "price_df" not in st.session_state:
    st.warning("먼저 메인 페이지에서 종목을 조회해 주세요.")
    st.stop()

price_df = st.session_state["price_df"].copy()
company_name = st.session_state.get("company_name", "Company")
st.subheader(f"[{company_name}] 부가 분석 지표")

price_df["MA5"] = price_df["Close"].rolling(5, min_periods=1).mean()
price_df["MA20"] = price_df["Close"].rolling(20, min_periods=1).mean()
price_df["MA60"] = price_df["Close"].rolling(60, min_periods=1).mean()
price_df["MA120"] = price_df["Close"].rolling(120, min_periods=1).mean()

def last_cross(series_a: pd.Series, series_b: pd.Series, lookback=60):
    a = series_a.dropna()
    b = series_b.dropna()
    idx = a.index.intersection(b.index)
    if len(idx) < 3:
        return None, None
    a = a.loc[idx].tail(lookback)
    b = b.loc[idx].tail(lookback)
    diff = a - b
    sign = diff.apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    sign_shift = sign.shift(1)
    cross_points = sign[(sign != sign_shift) & (sign != 0) & (sign_shift != 0)]
    if cross_points.empty:
        return None, None
    last_idx = cross_points.index[-1]
    direction = "골든크로스" if diff.loc[last_idx] > 0 else "데드크로스"
    return direction, last_idx

cross_5_20, cross_5_20_date = last_cross(price_df["MA5"], price_df["MA20"], lookback=90)

ma_fig = go.Figure()
ma_fig.add_trace(go.Scatter(x=price_df.index, y=price_df["MA5"], mode="lines", name="MA 5"))
ma_fig.add_trace(go.Scatter(x=price_df.index, y=price_df["MA20"], mode="lines", name="MA 20"))
ma_fig.add_trace(go.Scatter(x=price_df.index, y=price_df["MA60"], mode="lines", name="MA 60"))
ma_fig.add_trace(go.Scatter(x=price_df.index, y=price_df["MA120"], mode="lines", name="MA 120"))
ma_fig.update_layout(
    title="Moving Averages (5 / 20 / 60 / 120)",
    xaxis_title="Date",
    yaxis_title="Price",
    yaxis_tickformat=",",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=10, r=10, t=50, b=10)
)

c1, c2 = st.columns([2, 1])
with c1:
    st.plotly_chart(ma_fig, use_container_width=True)

    if cross_5_20 is None:
        st.info("현재: (MA5 vs MA20) 최근 교차 없음")
        st.caption("골든/데드크로스는 단기선이 중기선을 위/아래로 '돌파'할 때 발생합니다.")
    else:
        st.success(f"현재: (MA5 vs MA20) {cross_5_20}")
        st.caption("골든크로스=단기선이 중기/장기선을 상향 돌파, 데드크로스=하향 돌파")

with c2:
    st.markdown(f"""
### 이동평균선(MA) 정의
이동평균선은 **일정 기간의 종가 평균**을 이어 만든 선으로, **추세(방향)와 지지/저항**을 보기 위한 지표.
- **MA5 / MA20 / MA60 / MA120**: 단기 / 중기 / 장기 추세를 보여줍니다.
- **정배열**: MA5 > MA20 > MA60 > MA120 → 상승 추세 우세
- **역배열**: MA5 < MA20 < MA60 < MA120 → 하락 추세 우세

### 자주 쓰는 신호
- **골든크로스**: 단기선이 장기선을 상향 돌파 → 상승 전환 시그널
- **데드크로스**: 단기선이 장기선을 하향 돌파 → 하락 전환 시그널
- **지지/저항**: 가격이 MA 근처에서 반등/이탈하는지 관찰
""")

st.divider()

if "Volume" in price_df.columns:
    vol_fig = go.Figure()
    vol_fig.add_trace(go.Bar(x=price_df.index, y=price_df["Volume"], name="Volume"))
    vol_fig.update_layout(
        title="Volume",
        xaxis_title="Date",
        yaxis_title="Volume",
        yaxis_tickformat=",",
        margin=dict(l=10, r=10, t=50, b=10)
    )

    last_close = price_df["Close"].iloc[-1]
    prev_close = price_df["Close"].iloc[-2] if len(price_df) >= 2 else last_close
    last_vol = price_df["Volume"].iloc[-1]
    prev_vol = price_df["Volume"].iloc[-2] if len(price_df) >= 2 else last_vol

    price_dir = "상승" if last_close > prev_close else ("하락" if last_close < prev_close else "보합")
    vol_dir = "증가" if last_vol > prev_vol else ("감소" if last_vol < prev_vol else "보합")

    if price_dir == "상승" and vol_dir == "증가":
        vol_case = "가격 상승 + 거래량 증가"
        vol_meaning = "상승 움직임에 힘이 실렸을 가능성이 있어 추세 강화로 해석"
    elif price_dir == "상승" and vol_dir == "감소":
        vol_case = "가격 상승 + 거래량 감소"
        vol_meaning = "힘 없는 상승일 수 있어 단기 조정 가능성도 함께 체크"
    elif price_dir == "하락" and vol_dir == "증가":
        vol_case = "가격 하락 + 거래량 증가"
        vol_meaning = "매도 압력이 강해졌을 수 있어 하락 추세 강화로 해석"
    elif price_dir == "하락" and vol_dir == "감소":
        vol_case = "가격 하락 + 거래량 감소"
        vol_meaning = "하락 힘이 약해질 수 있어 바닥 다지기 가능성도 함께 체크"
    else:
        vol_case = f"가격 {price_dir} + 거래량 {vol_dir}"
        vol_meaning = "가격/거래량 방향이 뚜렷하지 않아 추가 관찰 필요"

    d1, d2 = st.columns([2, 1])
    with d1:
        st.plotly_chart(vol_fig, use_container_width=True)
        st.success(f"현재: {vol_case}")
        st.caption(vol_meaning)

    with d2:
        st.markdown(f"""
### 거래량(Volume) 정의
거래량은 **해당 기간에 거래된 주식 수(체결량)**로, 가격 움직임에 **힘(확신)**이 실렸는지 판단 가능.
- **가격 상승 + 거래량 증가**: 추세 강화 가능
- **가격 상승 + 거래량 감소**: 힘 없는 상승(조정 가능)
- **가격 하락 + 거래량 증가**: 매도 압력 강화 가능
- **가격 하락 + 거래량 감소**: 하락 힘 약화(바닥 다지기 가능)

""")
else:
    st.info("거래량(Volume) 데이터가 없습니다.")
