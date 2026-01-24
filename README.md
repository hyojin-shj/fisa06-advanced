# 📈StockFlow(주가 조회 & 분석)

> "주식 초보자를 위한 핵심 지표와 데이터를 직관적으로 정리한 쉬운 주식 분석 대시보드"
> <br>
[![Video Label](https://youtu.be/DRanEaQ13ZA?si=GGWEkvlSGxZHIGRQ)


<br>

## 📅 프로젝트 정보
- **유형:** 개인 프로젝트
- **개발 기간:** **2026.01.19 ~ 2026.01.20**

- ### 🛠️ Tech Stack
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![FinanceDataReader](https://img.shields.io/badge/FinanceDataReader-2E7D32?style=for-the-badge&logo=databricks&logoColor=white)
![Matplotlib](https://img.shields.io/badge/Matplotlib-11557C?style=for-the-badge&logo=plotly&logoColor=white)

<br>

## ✨ 주요 기능

- **상장사 기간별 주가조회**
  - KRX KIND 페이지를 크롤링하여 **회사명 ↔ 종목코드 자동 매핑**
  - `FinanceDataReader`를 활용해 **Open / High / Low / Close / Volume** 데이터 수집
  - 사용자가 직접 조회 기간 선택 가능하며 주가 추이를 Candel/Line graph로 시각화
  - matrix '오를까/내릴까?'를 통해 초보자가 흐름을 직관적으로 파악 가능

- **이동평균선 분석&거래량 보조 분석**
  - 종목의 기간별 이동평균선(MA)을 함께 제공하여 **단기 / 중기 추세를 직관적으로 파악**
  - 가격 변동과 함께 **거래량 흐름을 동시에 확인**

- **재무재표 및 관련 뉴스**
  - 선택한 종목 기준으로 **초보자도 이해하기 쉬운 핵심 재무 지표 제공**
  - 숫자 위주의 재무제표를 요약 형태로 노출
  - 선택한 종목과 연관된 최근 뉴스를 제공하여 가격 변동 원인을 뉴스 맥락에서 함께 이해 가능

- **엑셀 다운로드**
  - 조회된 전체 주가 데이터를 `.xlsx` 파일로 다운로드
  - `BytesIO` 기반으로 로컬 저장 없이 즉시 다운로드 가능

---
