# 🇰🇷 국내 실거래 매매 가이드

## 소수점 거래 지원 증권사

### 1. 키움증권 (KIWOOM)

**장점:**
- ✅ OpenAPI 제공
- ✅ Python 지원
- ✅ 소수점 거래 가능 (미국 주식)
- ✅ 실시간 데이터
- ✅ 안정적

**단점:**
- ❌ Windows 필수 (HTS 설치)
- ❌ 복잡한 초기 설정

**소수점 거래:**
- 미국 주식: 최소 0.01주
- 한국 주식: 정수 주만 가능

#### 필수 설치
1. 키움 OpenAPI+ 다운로드
2. HTS 설치 및 로그인
3. Python 라이브러리 설치
   ```bash
   pip install pykiwoom
   ```

#### 코드 예시
```python
from pykiwoom.kiwoom import *
import pandas as pd
from datetime import datetime
from src.strategy.ma_shannon_hybrid import MovingAverageShannonHybridStrategy

class KiwoomTradingBot:
    def __init__(self):
        # 키움 API 연결
        self.kiwoom = Kiwoom()
        self.kiwoom.CommConnect()  # 로그인
        
        # 전략 초기화
        self.strategy = MovingAverageShannonHybridStrategy(
            name="MA Shannon Hybrid",
            params={
                "stock_ticker": "TQQQ",  # 미국 주식
                "ma_period": 200,
                "stock_pct": 0.5,
                "band_threshold": 0.1
            }
        )
        
        logger.info("✅ 키움 API 연결 완료")
    
    def get_account_info(self):
        """계좌 정보 조회"""
        accounts = self.kiwoom.GetLoginInfo("ACCNO")  # 계좌번호
        account = accounts.split(';')[0]
        
        # 잔고 조회
        self.kiwoom.OPW00001_request(account)
        
        # 테이블 데이터 가져오기
        data = self.kiwoom.tr_data
        cash = int(data['주문가능금액']) / 100
        
        logger.info(f"계좌: {account}")
        logger.info(f"주문가능금액: {cash:,.0f}원")
        
        return cash
    
    def get_historical_data(self, code: str, period: int = 400):
        """과거 데이터 수집 (일봉)"""
        # TQQQ 종목코드
        df = self.kiwoom.block_request(
            "opt10081",
            종목코드=code,
            기준일자=datetime.now().strftime("%Y%m%d"),
            수정주가구분=1,
            output="주식일봉차트조회",
            next=0
        )
        
        # 데이터 변환
        df = df.rename(columns={
            '일자': 'Date',
            '시가': 'Open',
            '고가': 'High',
            '저가': 'Low',
            '종가': 'Close',
            '거래량': 'Volume'
        })
        
        return df
    
    def buy_stock(self, code: str, qty: float, price: float = 0):
        """소수점 매수"""
        accounts = self.kiwoom.GetLoginInfo("ACCNO")
        account = accounts.split(';')[0]
        
        # 시장가 주문
        self.kiwoom.SendOrder(
            "매수",
            "0101",  # 화면번호
            account,
            1,  # 매수
            code,
            qty,  # 소수점 수량
            0,  # 시장가
            "03",  # 주문유형 (03: 시장가)
            ""  # 원주문번호
        )
        
        logger.info(f"📈 {code} {qty}주 시장가 매수 주문")
    
    def sell_stock(self, code: str, qty: float):
        """소수점 매도"""
        accounts = self.kiwoom.GetLoginInfo("ACCNO")
        account = accounts.split(';')[0]
        
        self.kiwoom.SendOrder(
            "매도",
            "0101",
            account,
            2,  # 매도
            code,
            qty,
            0,
            "03",
            ""
        )
        
        logger.info(f"📉 {code} {qty}주 시장가 매도 주문")
```

---

### 2. 이베스트투자증권 (eBest)

**장점:**
- ✅ xingAPI 제공
- ✅ Python 지원
- ✅ 소수점 거래 가능

**단점:**
- ❌ Windows 필수
- ❌ HTS 설치 필요

**라이브러리:**
```bash
pip install python-xing
```

---

### 3. 대신증권

**장점:**
- ✅ OpenAPI 제공
- ✅ 소수점 거래 지원

**단점:**
- ❌ Windows 필수
- ❌ 문서 한정

---

### 4. KB증권

**장점:**
- ✅ 모바일 API
- ✅ 소수점 거래 활발

**단점:**
- ❌ Python API 없음 (REST만)
- ❌ 웹 기반

**REST API 예시:**
```python
import requests

def kb_buy_fractional(symbol, amount_usd):
    """KB증권 소수점 매수"""
    url = "https://api.kbsec.com/v1/trade/order"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "symbol": symbol,
        "side": "buy",
        "type": "fractional",  # 소수점 거래
        "amount": amount_usd  # 달러 금액
    }
    
    response = requests.post(url, headers=headers, json=data)
    return response.json()
```

---

## 추천: 키움증권 + pykiwoom

### 1단계: 환경 설정

```bash
# 1. 키움 OpenAPI+ 다운로드 및 설치
# https://www.kiwoom.com/h/customer/download/VOpenApiInfoView

# 2. HTS 실행 및 로그인

# 3. Python 라이브러리 설치
pip install pykiwoom pyqt5

# 4. 소수점 거래 신청 (증권사에 문의)
```

### 2단계: 코드 구현

```python
from pykiwoom.kiwoom import *
from src.strategy.ma_shannon_hybrid import MovingAverageShannonHybridStrategy

def main():
    # 키움 API 초기화
    kiwoom = Kiwoom()
    kiwoom.CommConnect()
    
    # 전략 초기화
    strategy = MovingAverageShannonHybridStrategy()
    
    # 계좌 조회
    accounts = kiwoom.GetLoginInfo("ACCNO")
    account = accounts.split(';')[0]
    cash = get_account_balance(kiwoom, account)
    
    # 데이터 수집
    data = get_historical_data(kiwoom, "TQQQ")
    
    # 신호 생성
    signals = strategy.generate_signals(data)
    latest = signals.iloc[-1]
    
    # 거래 실행
    if latest['Signal'] == 1:
        if latest['Mode'] == 'ABOVE':
            # TQQQ 95% 매수
            qty = cash * 0.95 / data['Close'].iloc[-1]
            kiwoom.SendOrder("매수", "0101", account, 1, "TQQQ", qty, 0, "03", "")
```

---

## 소수점 거래 주의사항

### 1. 최소 거래 단위
```python
# 미국 주식 소수점 거래
min_qty = 0.01  # 최소 0.01주

# 주문 금액 계산
cash = 1000000  # 100만원
price = 50  # 주가 $50
qty = cash / price  # 0.001주 (최소 단위 미만!)

# 최소 단위로 반올림
qty = max(0.01, round(qty, 2))  # 0.01주로 제한
```

### 2. 포트폴리오 비율 계산
```python
# 백테스트는 정수 주로 계산
target_qty = int(portfolio_value * 0.5 / price)

# 실제는 소수점으로 계산
target_qty = portfolio_value * 0.5 / price
target_qty = round(target_qty, 2)  # 소수점 2자리

# 50% 비율 정확히 달성 가능
```

### 3. 전략 수정 필요

현재 `ma_shannon_hybrid.py`는 정수 주로 계산되어 소수점 거래를 위해 수정 필요:

```python
# 기존 코드 (simple_engine.py)
target_quantity = int(target_value / price)

# 소수점 거래 버전
target_quantity = round(target_value / price, 2)
```

---

## 구현 체크리스트

### 필수 작업
- [ ] 증권사 API 설치 (키움 OpenAPI+)
- [ ] 소수점 거래 신청
- [ ] Python 라이브러리 설치 (pykiwoom)
- [ ] 로그인 자동화
- [ ] 소수점 비율 계산 수정
- [ ] 예외 처리

### 안전장치
- [ ] 최소 거래 단위 체크
- [ ] 포지션 크기 제한 (95%)
- [ ] 일일 손실 한도
- [ ] 주문 실패 재시도
- [ ] 로그 기록

### 모니터링
- [ ] 거래 알림 (텔레그램/이메일)
- [ ] 포트폴리오 현황
- [ ] 일일 리포트

---

## 빠른 시작

### 1. 키움증권 계좌 개설
https://www.kiwoom.com/h/customer/main

### 2. OpenAPI+ 다운로드
https://www.kiwoom.com/h/customer/download/VOpenApiInfoView

### 3. 소수점 거래 신청
고객센터 (1588-9482) 문의

### 4. 설치
```bash
pip install pykiwoom pyqt5
```

### 5. 실행
```bash
python examples/live_trading_kiwoom.py
```

---

## 주의사항

### ⚠️ Windows 필수
국내 증권사 API는 대부분 Windows 환경에서만 동작합니다.
- VirtualBox/VMware로 Windows 사용
- 또는 AWS Windows 인스턴스

### ⚠️ HTS 실행 필수
API는 HTS(증권사 프로그램)와 통신하므로 HTS가 항상 실행되어야 합니다.

### ⚠️ 수수료 확인
```python
# 소수점 거래 수수료가 다를 수 있음
# 실제 확인 필수
commission_rate = 0.001  # 0.1% (가정)
```

### ⚠️ 과거 데이터 제한
국내 증권사 API는 과거 데이터가 제한적일 수 있습니다.
- 최대 400일봉만 조회 가능
- KIS Developers API 사용 권장

---

## 대안: KIS Developers API

**한국투자증권의 REST API**

**장점:**
- ✅ OS 무관 (Windows 불필요)
- ✅ 간단한 REST API
- ✅ Python 직접 호출
- ✅ 소수점 거래 지원

**설치:**
```bash
pip install pykis
```

**코드 예시:**
```python
from pykis import KisOpenAPI

# API 초기화
api = KisOpenAPI(
    base_url="https://openapi.koreainvestment.com",
    key="YOUR_API_KEY",
    secret="YOUR_SECRET_KEY"
)

# 소수점 매수
response = api.order_buy_fractional(
    symbol="TQQQ",
    quantity=0.5  # 0.5주
)
```

**문서:**
https://developers.koreainvestment.com/

---

## 추천: KIS Developers API

**Windows 없이 바로 시작 가능!**

1. 한국투자증권 계좌 개설
2. KIS Developers 가입
3. API 키 발급
4. `pip install pykis`
5. 실행!

