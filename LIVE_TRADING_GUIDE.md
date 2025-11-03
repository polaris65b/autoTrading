# 🚀 실전 매매 구현 가이드

## 현재 상태
- ✅ 백테스팅 완료 (ma_shannon_hybrid 최적)
- ❌ 실거래 시스템 없음

---

## 구현 방법 옵션

### Option 1: Interactive Brokers (IBKR) - 추천

**장점:**
- 글로벌 시장 접근 (한/미/유럽/선물/옵션)
- Python API 공식 지원 (`ib_insync` 라이브러리)
- 수수료 저렴
- 안정적 API

**단점:**
- 계좌 개설 복잡
- 최소 입금 ($10,000+)
- 영어 문서

#### 구현 예시:

```python
from ib_insync import *
import pandas as pd
from datetime import datetime, timedelta
from src.strategy.ma_shannon_hybrid import MovingAverageShannonHybridStrategy

# IBKR 연결
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)  # TWS/IB Gateway

# 전략 초기화
strategy = MovingAverageShannonHybridStrategy(
    name="MA Shannon Hybrid Live",
    params={
        "stock_ticker": "TQQQ",
        "ma_period": 200,
        "stock_pct": 0.5,
        "band_threshold": 0.1
    }
)

# 계좌 정보 조회
account_values = ib.accountValues()
cash = float([v for v in account_values if v.tag == 'TotalCashValue'][0].value)
print(f"현재 현금: ${cash:,.2f}")

# TQQQ 계약 생성
contract = Stock('TQQQ', 'SMART', 'USD')

# 실시간 데이터 구독
ib.reqMktData(contract, '', False, False)

def on_pending_tickers(tickers):
    """실시간 가격 업데이트"""
    for ticker in tickers:
        if ticker.contract.symbol == 'TQQQ':
            current_price = ticker.marketPrice()
            process_trading_signal(current_price)

# 실시간 가격 구독
ib.pendingTickersEvent += on_pending_tickers

# 일봉 데이터로 신호 생성
bars = ib.reqHistoricalData(
    contract,
    endDateTime='',
    durationStr='400 D',
    barSizeSetting='1 day',
    whatToShow='TRADES',
    useRTH=True
)

# 신호 생성
df = util.df(bars)
signals = strategy.generate_signals(df)
latest_signal = signals.iloc[-1]
```

---

### Option 2: Alpaca - 미국 시장 전용

**장점:**
- 미국 주식 전용 (우리 전략에 적합!)
- Python API 우수 (`alpaca-trade-api`)
- 수수료 무료
- 계좌 개설 쉬움

**단점:**
- 미국 시장만
- Paper trading만 가능 (실거래 제한적)

#### 구현 예시:

```python
import alpaca_trade_api as tradeapi
from src.strategy.ma_shannon_hybrid import MovingAverageShannonHybridStrategy

# API 인증
api = tradeapi.REST(
    'YOUR_API_KEY',
    'YOUR_SECRET_KEY',
    'https://paper-api.alpaca.markets',  # Paper trading
    api_version='v2'
)

# 전략 초기화
strategy = MovingAverageShannonHybridStrategy(
    name="MA Shannon Hybrid",
    params={
        "stock_ticker": "TQQQ",
        "ma_period": 200,
        "stock_pct": 0.5,
        "band_threshold": 0.1
    }
)

# 계좌 조회
account = api.get_account()
cash = float(account.cash)
print(f"현재 현금: ${cash:,.2f}")

# 일봉 데이터 수집
bars = api.get_bars(
    'TQQQ',
    tradeapi.TimeFrame.Day,
    start='2024-01-01T00:00:00-04:00',
    end='2025-11-01T23:59:59-04:00'
).df

# 신호 생성
signals = strategy.generate_signals(bars)
latest_signal = signals.iloc[-1]

# 모드에 따라 거래
if latest_signal['Signal'] == 1:
    if latest_signal['Mode'] == 'ABOVE':
        # TQQQ 100% 매수
        qty = int(cash * 0.95 / bars['close'].iloc[-1])  # 95% 투자
        api.submit_order(
            symbol='TQQQ',
            qty=qty,
            side='buy',
            type='market',
            time_in_force='day'
        )
        print(f"📈 TQQQ {qty}주 매수")
    else:
        # TQQQ 50%로 축소
        position = api.get_position('TQQQ')
        if position:
            reduce_qty = position.qty // 2
            api.submit_order(
                symbol='TQQQ',
                qty=reduce_qty,
                side='sell',
                type='market',
                time_in_force='day'
            )
            print(f"📉 TQQQ {reduce_qty}주 매도")
```

---

### Option 3: 한국 증권사 API (키움/이베스트 등)

**장점:**
- 한국 시장 직접 접근
- 국내 거래 가능
- 한국어 지원

**단점:**
- 제한적 신뢰성
- 실시간/안정성 이슈
- API 문서 부족

---

## 실제 구현 추천 단계

### Step 1: Paper Trading 시작

1. **Alpaca로 Paper Trading**
   ```bash
   pip install alpaca-trade-api
   ```
   - 무료 계좌 개설
   - $100,000 가상 자금
   - 실전과 동일 환경

2. **매일 자동 실행**
   ```python
   import schedule
   import time

   def daily_trade():
       # 매일 장 마감 후 실행
       strategy = MovingAverageShannonHybridStrategy()
       # ... 신호 생성 및 거래
       
   # 매일 17:00 실행 (미국 장 마감 후)
   schedule.every().day.at("17:00").do(daily_trade)
   
   while True:
       schedule.run_pending()
       time.sleep(60)
   ```

### Step 2: 실제 자금 투입

1. **소액 테스트**
   - $1,000 ~ $5,000
   - 1개월 모니터링
   
2. **점진 확대**
   - 성과 확인 후 확대
   - MDD 주의

### Step 3: 모니터링 & 알림

1. **이메일/텔레그램 알림**
   ```python
   import smtplib
   
   def send_notification(message):
       # 이메일 발송
       pass
   
   def on_trade_executed(trade):
       send_notification(f"✅ 거래 완료: {trade}")
   ```

2. **대시보드 구축**
   - 실시간 포트폴리오 현황
   - 자동 리포트

---

## ⚠️ 실거래 주의사항

### 1. 수수료 고려
```python
# 백테스트는 수수료 0.1%
# 실제는 수수료 다를 수 있음
commission_rate = 0.001  # IBKR 기준
```

### 2. 슬리피지 (Slippage)
```python
# 시장가 주문 시 가격차 발생
# 백테스트와 실제 차이 존재
expected_price = 100.0
actual_price = 100.5  # 슬리피지
```

### 3. 체결 실패
```python
# 예외 처리 필수
try:
    order = api.submit_order(...)
    if order.status != 'filled':
        logger.warning("체결 실패")
except Exception as e:
    logger.error(f"주문 실패: {e}")
```

### 4. 리스크 관리
```python
# 위치 크기 제한
MAX_POSITION_SIZE = 0.95  # 포트폴리오의 95%
MAX_DAILY_LOSS = 0.05     # 일일 5% 손실 시 중단
```

---

## 🎯 구현 체크리스트

### 필수 구현
- [ ] API 연동 (IBKR 또는 Alpaca)
- [ ] 실시간 데이터 수집
- [ ] 신호 생성 (기존 전략 활용)
- [ ] 자동 주문 실행
- [ ] 예외 처리 & 로깅
- [ ] 포트폴리오 모니터링

### 권장 구현
- [ ] 이메일/텔레그램 알림
- [ ] 일일 성과 리포트
- [ ] MDD 알림 (손실 과다 시)
- [ ] 백업 실행 환경 (서버)

---

## 📝 빠른 시작 (Alpaca Paper Trading)

### 1. 계좌 개설
https://alpac.markets/signup

### 2. API 키 발급
Dashboard → Your API Keys

### 3. 코드 작성
```bash
# 새 파일 생성
touch live_trading.py
```

```python
import alpaca_trade_api as tradeapi
from datetime import datetime
from src.strategy.ma_shannon_hybrid import MovingAverageShannonHybridStrategy

API_KEY = "YOUR_KEY"
SECRET_KEY = "YOUR_SECRET"

def main():
    api = tradeapi.REST(API_KEY, SECRET_KEY, base_url='https://paper-api.alpaca.markets')
    
    # 전략 초기화
    strategy = MovingAverageShannonHybridStrategy()
    
    # 계좌 조회
    account = api.get_account()
    print(f"💰 계좌 현금: ${account.cash}")
    
    # 데이터 수집
    bars = api.get_bars('TQQQ', tradeapi.TimeFrame.Day, limit=400).df
    
    # 신호 생성
    signals = strategy.generate_signals(bars)
    latest = signals.iloc[-1]
    
    print(f"📊 현재 모드: {latest['Mode']}")
    print(f"📊 신호: {latest['Signal']}")
    
    # TODO: 거래 로직 구현
    
if __name__ == '__main__':
    main()
```

### 4. 실행
```bash
python live_trading.py
```

---

## 💡 추가 자료

- **IBKR Python API**: https://ib-insync.readthedocs.io/
- **Alpaca API**: https://alpaca.markets/docs/
- **전략 예제**: `src/strategy/ma_shannon_hybrid.py`

---

## ⚡ 다음 단계

1. **Paper Trading 시작** (1주)
2. **모니터링 시스템 구축** (1주)
3. **소액 실거래 테스트** (1개월)
4. **점진 확대**

