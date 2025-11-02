# 🚀 빠른 시작 가이드 (초보자용)

## ⚡ 30초 안에 시작하기

### 방법 1: 제공된 설정 파일 사용 (가장 쉬움!)

```bash
# 1. 가상환경 활성화
source venv/bin/activate

# 2. 백테스팅 실행 (원하는 종목 선택)
python backtest.py -c config_qqq.yaml   # QQQ 테스트
python backtest.py -c config_aapl.yaml  # 애플 테스트
python backtest.py -c config_spy.yaml   # S&P 500 테스트
```

**끝!** 이게 전부입니다! 🎉

---

### 방법 2: 다른 종목으로 테스트하기

#### 📝 1단계: 설정 파일 복사

```bash
# 예제 파일 복사
cp config_qqq.yaml my_stock.yaml
```

#### 📝 2단계: 종목만 바꾸기

`my_stock.yaml` 파일을 열어서 **한 곳만** 수정하세요:

```yaml
# 📈 백테스팅할 종목
assets:
  tickers:
    - "QQQ"  # ⬅️ 여기를 원하는 종목으로 바꾸세요!
```

**예시:**
- `"QQQ"` → `"AAPL"`  (애플로 변경)
- `"QQQ"` → `"GOOGL"` (구글로 변경)
- `"QQQ"` → `"TSLA"`  (테슬라로 변경)

#### 📝 3단계: 실행

```bash
python backtest.py -c my_stock.yaml
```

---

## 📖 상세 가이드

### 어떤 종목을 사용할 수 있나요?

미국 주식 티커 심볼을 사용합니다. 예시:

| 티커 | 회사명 |
|------|--------|
| `QQQ` | 나스닥 100 ETF |
| `SPY` | S&P 500 ETF |
| `AAPL` | 애플 |
| `GOOGL` | 구글 (알파벳) |
| `MSFT` | 마이크로소프트 |
| `TSLA` | 테슬라 |
| `NVDA` | 엔비디아 |
| `AMZN` | 아마존 |
| `META` | 메타 (페이스북) |

**💡 팁:** 티커 심볼을 모르면 구글이나 야후 파이낸스에서 검색해보세요!

### 기간은 어떻게 바꾸나요?

설정 파일에서 이 부분만 수정하세요:

```yaml
backtest:
  start_date: "2010-01-01"  # ⬅️ 시작일 변경
  end_date: "2024-12-31"    # ⬅️ 종료일 변경
```

**예시:**
- 최근 5년: `start_date: "2020-01-01"`
- 최근 1년: `start_date: "2024-01-01"`
- 특정 기간: `start_date: "2015-01-01"`, `end_date: "2020-12-31"`

### 초기 투자금은 어떻게 바꾸나요?

```yaml
backtest:
  initial_cash: 100000  # ⬅️ 이 숫자만 바꾸세요
```

**예시:**
- $10,000: `initial_cash: 10000`
- $50,000: `initial_cash: 50000`
- $1,000,000: `initial_cash: 1000000`

---

## 🎯 실제 예시

### 예시 1: 테슬라(TSLA) 백테스팅

```bash
# 1. 설정 파일 복사
cp config_qqq.yaml config_tsla.yaml

# 2. 파일 열어서 "QQQ" → "TSLA"로 변경

# 3. 실행
python backtest.py -c config_tsla.yaml
```

### 예시 2: 애플 최근 3년 백테스팅

```bash
# 1. 설정 파일 복사
cp config_aapl.yaml aapl_3years.yaml

# 2. 파일 열어서 수정:
#    tickers: ["AAPL"]  (이미 되어있음)
#    start_date: "2022-01-01"  (3년 전으로 변경)

# 3. 실행
python backtest.py -c aapl_3years.yaml
```

### 예시 3: 나만의 설정 파일 만들기

1. `config.yaml.example` 파일 복사:
   ```bash
   cp config.yaml.example my_first_test.yaml
   ```

2. 파일 열어서 수정:
   - 종목 변경: `tickers: ["원하는종목"]`
   - 기간 변경: `start_date`, `end_date`
   - 투자금 변경: `initial_cash`

3. 실행:
   ```bash
   python backtest.py -c my_first_test.yaml
   ```

---

## ✅ 결과 확인하기

백테스팅이 완료되면 이런 정보를 볼 수 있습니다:

```
======================================================================
결과 요약
----------------------------------------------------------------------
Strategy: buyhold
Ticker: QQQ
Period: 2010-01-04 ~ 2024-12-30
Days: 3773
Initial Cash: $100,000.00
Final Value: $1,109,596.96          ← 최종 자산
Total Return: 1009.60%               ← 총 수익률
Annualized Return: 26.23%            ← 연간 수익률
Total Trades: 1                       ← 거래 횟수
======================================================================
```

**중요한 지표:**
- **Final Value**: 최종 자산 (얼마나 돈이 생겼나)
- **Total Return**: 총 수익률 (%)
- **Annualized Return**: 연간 평균 수익률 (매년 평균)

---

## ❓ 자주 묻는 질문

### Q1: 어떤 종목 티커를 사용해야 하나요?
**A:** 미국 주식 티커 심볼이면 모두 사용 가능합니다. 티커를 모르면 구글에서 "[회사명] stock ticker"로 검색하세요.

### Q2: 오류가 발생했어요
**A:** 다음을 확인하세요:
1. 종목 티커가 맞는지 확인 (대문자로 입력)
2. 날짜 형식이 `"YYYY-MM-DD"`인지 확인
3. 가상환경이 활성화되어 있는지 확인

### Q3: 여러 종목을 동시에 테스트할 수 있나요?
**A:** 현재는 단일 종목만 지원합니다. 여러 종목을 테스트하려면 각각 설정 파일을 만들어 실행하세요.

### Q4: 결과를 파일로 저장할 수 있나요?
**A:** 추후 구현 예정입니다. 현재는 화면에 결과가 표시됩니다.

---

## 🎓 다음 단계

1. ✅ 다양한 종목으로 테스트해보기
2. ✅ 기간을 바꿔가며 성과 비교하기
3. ✅ 다른 전략 시도해보기 (추후 구현)
4. ✅ [USAGE.md](USAGE.md) 읽어보기 (더 자세한 내용)

---

## 💡 활용 팁

1. **비교하기**: 같은 기간에 여러 종목 테스트해서 비교
2. **기간 실험**: 1년, 5년, 10년 등 다른 기간으로 테스트
3. **시장 상황 분석**: 2008년 금융위기, 2020년 코로나 등 특정 시기 분석
4. **저장하기**: 좋은 설정 파일은 이름을 기억하기 쉽게 저장

---

**🎉 이제 시작하세요!**

```bash
python backtest.py -c config_qqq.yaml
```

**궁금한 점이 있으면 [USAGE.md](USAGE.md)를 참고하세요!**
