# 📖 사용법 가이드

주식 백테스팅 시스템 사용 방법

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 가상환경 활성화
source venv/bin/activate  # macOS/Linux
# 또는
venv\Scripts\activate     # Windows

# 필수 패키지 설치 확인
pip install -r requirements.txt
```

### 2. 백테스팅 실행

백테스팅은 설정 파일 기반으로 실행합니다:

```bash
# 제공된 설정 파일로 실행
python backtest.py -c config_qqq.yaml   # QQQ 백테스팅
python backtest.py -c config_aapl.yaml  # AAPL 백테스팅
python backtest.py -c config_spy.yaml   # SPY 백테스팅

# 커스텀 설정 파일로 실행
python backtest.py -c my_config.yml
```

### 3. 설정 파일 생성

백테스팅 설정을 위한 설정 파일을 생성합니다:

```bash
# 대화형 설정 파일 생성
python examples/config_generator.py

# 또는 예제 파일 복사
cp config.yml.example config.yml
```

설정 파일 예시 (`config.yml`):

```yaml
backtest:
  start_date: "2010-01-01"
  end_date: "2024-12-31"
  initial_cash: 100000
  commission_rate: 0.001

portfolio:
  strategies:
    - name: "buyhold"
      enabled: true
      params:
        position_pct: 1.0
        
assets:
  tickers:
    - "QQQ"
```

### 4. 데이터 수집 (개발용)

```python
from src.data.collector import StockDataCollector
from datetime import datetime, timedelta

# 데이터 수집기 생성
collector = StockDataCollector()

# 최근 1년 데이터 수집
end_date = datetime.now()
start_date = end_date - timedelta(days=365)

# AAPL(Apple) 데이터 수집
df = collector.collect_ohlcv("AAPL", start_date.strftime("%Y-%m-%d"))
print(df.head())
```


## 🎛️ 설정 파일 사용법

백테스팅 시스템은 YAML 기반 설정 파일을 통해 쉽게 설정할 수 있습니다.

### 설정 파일 로드

```python
from src.config.loader import load_config

# 설정 파일 로드
config = load_config("config.yml")

# 설정 사용
print(f"백테스팅 기간: {config.backtest.start_date} ~ {config.backtest.end_date}")
print(f"초기 자본금: ${config.backtest.initial_cash:,.0f}")
print(f"거래 종목: {config.assets.tickers}")

# 사용 가능한 전략 확인
enabled_strategies = [s.name for s in config.portfolio.strategies if s.enabled]
print(f"활성화된 전략: {enabled_strategies}")
```

### 주요 설정 항목

| 항목 | 설명 | 예시 |
|------|------|------|
| `backtest.start_date` | 백테스팅 시작일 | `"2023-01-01"` |
| `backtest.end_date` | 백테스팅 종료일 | `"2024-12-31"` |
| `backtest.initial_cash` | 초기 자본금 (USD) | `100000` |
| `backtest.commission_rate` | 수수료율 | `0.001` (0.1%) |
| `assets.tickers` | 거래할 종목 목록 | `["AAPL", "GOOGL"]` |
| `portfolio.strategies` | 사용할 전략 목록 | 섀넌, 이동평균 등 |
| `risk.max_positions` | 최대 보유 종목 수 | `10` |
| `risk.stop_loss.enabled` | 손절 사용 여부 | `true` |

## 📊 백테스팅 실행 가이드

### 가장 간단한 방법

```bash
# 1. 설정 파일 선택 또는 생성
# - config_qqq.yaml: QQQ 백테스팅
# - config_aapl.yaml: AAPL 백테스팅  
# - config_spy.yaml: SPY 백테스팅
# - 또는 원하는 설정 파일 생성

# 2. 백테스팅 실행
python backtest.py -c config_qqq.yaml
```

### 결과 확인

백테스팅이 완료되면 다음 정보를 확인할 수 있습니다:
- 총 수익률 및 연환산 수익률
- 최고점/최저점 및 최대 낙폭
- 거래 내역
- 보유 종목 현황

### 커스텀 설정 파일 만들기

1. 예제 파일 복사:
   ```bash
   cp config.yml.example my_strategy.yml
   ```

2. 파일 편집:
   - `start_date`, `end_date`: 백테스팅 기간
   - `tickers`: 거래할 종목
   - `strategies`: 사용할 전략

3. 실행:
   ```bash
   python backtest.py -c my_strategy.yaml
   ```

## 📊 주요 모듈 사용법

### 데이터 수집 (Data Collector)

```python
from src.data.collector import StockDataCollector

collector = StockDataCollector()

# 1. 단일 종목 데이터 수집
df = collector.collect_ohlcv(
    ticker="AAPL",
    start_date="2020-01-01",
    end_date="2024-12-31"
)

# 2. 종목 정보 조회
info = collector.get_ticker_info("AAPL")
print(f"회사명: {info['longName']}")
print(f"섹터: {info['sector']}")

# 3. 종목명 조회
name = collector.get_ticker_name("TSLA")
print(f"종목명: {name}")  # Tesla, Inc.

# 4. 여러 종목 동시 수집
dfs = collector.collect_multiple(
    tickers=["AAPL", "GOOGL", "MSFT"],
    start_date="2024-01-01"
)

# 5. 데이터 저장 및 로드
# 저장
filepath = collector.save_to_csv(df, "AAPL", prefix="raw")
print(f"저장 완료: {filepath}")

# 로드
loaded_df = collector.load_from_csv(filepath)
```

**주요 파라미터**:
- `ticker`: 종목 티커 심볼 (예: "AAPL", "TSLA", "GOOGL")
- `start_date`: 시작일 (YYYY-MM-DD 형식)
- `end_date`: 종료일 (기본값: 오늘)
- `interval`: 데이터 간격 ("1d", "1h", "5m" 등)

### 포트폴리오 관리 (Portfolio)

```python
from src.backtest.portfolio import Portfolio
from datetime import datetime

# 포트폴리오 생성
portfolio = Portfolio(
    initial_cash=100_000,      # 초기 자본금 $100,000
    commission_rate=0.001       # 수수료율 0.1%
)

# 1. 매수
portfolio.buy("AAPL", 10, 150.00, datetime.now())
print(f"현금: ${portfolio.cash:,.2f}")

# 2. 현재가 업데이트
portfolio.update_price("AAPL", 155.00)

# 3. 보유 종목 조회
position = portfolio.get_position("AAPL")
print(f"평가 손익: ${position.profit_loss:.2f}")

# 4. 매도
portfolio.sell("AAPL", 5, 155.00, datetime.now())

# 5. 포트폴리오 요약
print("\n=== 총 자산 ===")
print(f"총 가치: ${portfolio.total_value:,.2f}")
print(f"총 수익률: {portfolio.total_profit_loss_pct:.2f}%")

# 6. 보유 종목 상세
holdings = portfolio.get_holdings_summary()
print(holdings)
```

**주요 메서드**:
- `buy(ticker, quantity, price, date)`: 매수
- `sell(ticker, quantity, price, date)`: 매도
- `update_price(ticker, price)`: 현재가 업데이트
- `get_position(ticker)`: 포지션 조회
- `total_value`: 총 자산 (현금 + 평가금)
- `total_profit_loss_pct`: 총 수익률

### 백테스팅 엔진 (BacktestEngine)

```python
from src.backtest.engine import BacktestEngine
from src.data.collector import StockDataCollector

# 1. 엔진 생성
engine = BacktestEngine(
    initial_cash=100_000,
    commission_rate=0.001
)

# 2. 데이터 수집
collector = StockDataCollector()
df = collector.collect_ohlcv("AAPL", "2023-01-01")

# 3. 전략 설정 (아직 구현 필요)
# engine.set_strategy(my_strategy)

# 4. 백테스팅 실행
# results = engine.run(df)

# 5. 결과 조회
# summary = engine.get_summary()
# print(summary)
```

## 🎯 미국 주요 종목 티커

```
AAPL   - Apple Inc.
MSFT   - Microsoft Corporation
GOOGL  - Alphabet Inc. (Google)
AMZN   - Amazon.com Inc.
META   - Meta Platforms Inc.
TSLA   - Tesla Inc.
NVDA   - NVIDIA Corporation
JPM    - JPMorgan Chase & Co.
V      - Visa Inc.
JNJ    - Johnson & Johnson
```

## ⚠️ 현재 상태

### ✅ 구현 완료
- ✅ 데이터 수집 모듈 (yfinance 기반)
- ✅ 포트폴리오 관리
- ✅ 백테스팅 엔진 기본 구조
- ✅ 전략 인터페이스

### 🚧 구현 예정
- ⏳ 섀넌 전략
- ⏳ 이동평균선 추매 전략
- ⏳ 리밸런싱 전략
- ⏳ 성과 지표 계산 (Sharpe Ratio, Max Drawdown 등)
- ⏳ 시각화 모듈
- ⏳ 상세 백테스팅 예제

## 🔍 예제 스크립트

### 예제 0: 설정 파일 생성

```bash
python examples/config_generator.py
```

### 예제 1: 데이터 수집 및 저장

```python
#!/usr/bin/env python3
"""데이터 수집 예제"""

from src.data.collector import StockDataCollector
from src.utils.logger import setup_logger
from datetime import datetime, timedelta

logger = setup_logger()

def collect_sample_data():
    """샘플 데이터 수집"""
    collector = StockDataCollector()
    
    tickers = ["AAPL", "GOOGL", "MSFT", "TSLA"]
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    for ticker in tickers:
        try:
            logger.info(f"{ticker} 데이터 수집 시작...")
            df = collector.collect_ohlcv(
                ticker=ticker,
                start_date=start_date.strftime("%Y-%m-%d")
            )
            collector.save_to_csv(df, ticker, prefix="raw")
            logger.info(f"{ticker} 수집 완료: {len(df)}개 일봉")
        except Exception as e:
            logger.error(f"{ticker} 수집 실패: {e}")

if __name__ == "__main__":
    collect_sample_data()
```

### 예제 2: 포트폴리오 관리

```python
#!/usr/bin/env python3
"""포트폴리오 관리 예제"""

from src.backtest.portfolio import Portfolio
from src.utils.logger import setup_logger
from datetime import datetime, timedelta

logger = setup_logger()

def portfolio_demo():
    """포트폴리오 데모"""
    # 포트폴리오 생성
    portfolio = Portfolio(
        initial_cash=100_000,
        commission_rate=0.001
    )
    
    logger.info(f"초기 자본금: ${portfolio.initial_cash:,.2f}")
    
    # 매수 시뮬레이션
    base_date = datetime.now()
    prices = [150, 155, 160, 158, 165]  # 5일간 가격 변화
    
    for i, price in enumerate(prices):
        date = base_date + timedelta(days=i)
        portfolio.update_price("AAPL", price) if i > 0 else None
        
        if i == 0:
            # 첫날 매수
            quantity = 100
            portfolio.buy("AAPL", quantity, price, date)
            logger.info(f"[{date.strftime('%Y-%m-%d')}] 매수: {quantity}주 @ ${price}")
        elif i == 3:
            # 3일 후 50주 매도
            quantity = 50
            portfolio.sell("AAPL", quantity, price, date)
            logger.info(f"[{date.strftime('%Y-%m-%d')}] 매도: {quantity}주 @ ${price}")
        
        # 스냅샷
        portfolio.snapshot(date)
        
        logger.info(f"일자: {date.strftime('%Y-%m-%d')}, "
                   f"가격: ${price}, "
                   f"총 자산: ${portfolio.total_value:,.2f}, "
                   f"수익률: {portfolio.total_profit_loss_pct:.2f}%")
    
    # 최종 결과
    logger.info("\n=== 최종 결과 ===")
    logger.info(f"총 자산: ${portfolio.total_value:,.2f}")
    logger.info(f"현금: ${portfolio.cash:,.2f}")
    logger.info(f"총 수익률: {portfolio.total_profit_loss_pct:.2f}%")
    logger.info(f"총 거래 횟수: {len(portfolio.trades)}")
    
    # 보유 종목
    holdings = portfolio.get_holdings_summary()
    if not holdings.empty:
        logger.info("\n보유 종목:")
        print(holdings)

if __name__ == "__main__":
    portfolio_demo()
```

### 예제 3: 설정 파일 사용

```python
#!/usr/bin/env python3
"""설정 파일 사용 예제"""

from src.config.loader import load_config
from pathlib import Path

def config_demo():
    """설정 파일 데모"""
    # 설정 로드
    config = load_config(Path("config.yml"))
    
    print("=== 백테스팅 설정 ===")
    print(f"기간: {config.backtest.start_date} ~ {config.backtest.end_date}")
    print(f"초기 자본금: ${config.backtest.initial_cash:,.0f}")
    print(f"수수료율: {config.backtest.commission_rate*100:.2f}%")
    
    print("\n=== 거래 종목 ===")
    print(f"종목: {', '.join(config.assets.tickers)}")
    
    print("\n=== 전략 설정 ===")
    for strategy in config.portfolio.strategies:
        if strategy.enabled:
            print(f"전략: {strategy.name}")
            if strategy.params:
                print(f"  파라미터: {strategy.params}")
    
    print("\n=== 리스크 관리 ===")
    print(f"최대 보유 종목: {config.risk.max_positions}")
    print(f"손절: {'ON' if config.risk.stop_loss.enabled else 'OFF'}")

if __name__ == "__main__":
    config_demo()
```

## 🛠 설정

환경 변수 설정 (선택사항):

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집
DEFAULT_INITIAL_CASH=100000
DEFAULT_COMMISSION=0.001
MARKET=US
```

## 📝 로그 확인

로그 파일은 `logs/` 디렉토리에 저장됩니다:

```bash
tail -f logs/backtest_$(date +%Y-%m-%d).log
```

## 🐛 문제 해결

### 데이터 수집 실패

```python
# 에러 발생 시 재시도
try:
    df = collector.collect_ohlcv("TICKER", "2024-01-01")
except Exception as e:
    logger.error(f"수집 실패: {e}")
    # 재시도 또는 다른 티커 사용
```

### 자금 부족 에러

```python
# 포지션 사이징 확인
position_value = quantity * price
commission = position_value * commission_rate
total_needed = position_value + commission

if portfolio.cash < total_needed:
    logger.warning("자금 부족 - 주문 수량 조정 필요")
```

## 📚 추가 자료

- [yfinance 공식 문서](https://github.com/ranaroussi/yfinance)
- [pandas 공식 문서](https://pandas.pydata.org/)
- [프로젝트 계획서](PROJECT_PLAN.md)

## 💡 다음 단계

전략 구현이 완료되면 다음과 같이 사용할 수 있습니다:

```python
# (구현 예정)
from src.strategy.shannon import ShannonStrategy

strategy = ShannonStrategy(name="Shannon", params={"rebalance_freq": 30})
engine.set_strategy(strategy)
results = engine.run(df)
```

---

**문의사항이나 버그 발견 시**: Issue를 생성해주세요!

