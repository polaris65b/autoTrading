# 주식 백테스팅 & 자동 트레이딩 프로젝트 계획

## 프로젝트 목표
1. 주식 백테스팅 시스템 구축 (Phase 1)
2. 자동 트레이딩 시스템 구축 (Phase 2)

## 기술 스택 결정

### Phase 1: 백테스팅 MVP (Python)
- **언어**: Python 3.12.8
- **주요 라이브러리**:
  - `pandas`: 데이터 처리
  - `numpy`: 수치 계산
  - `yfinance` or `pykrx`: 주가 데이터 수집
  - `matplotlib`, `seaborn`: 시각화
  - (선택) `backtrader`: 백테스팅 프레임워크

### Phase 2: 자동 트레이딩 시스템 (Python + Spring Boot)
- **백엔드**: Spring Boot 3.5.7
  - API 서버
  - 스케줄러
  - 로깅 및 모니터링
- **백테스팅 엔진**: Python (Phase 1에서 구축)
- **주문**: API 연동 (키움/대신/이베스트 등)
- **Java**: 17 이상 필요

## 프로젝트 구조 (Phase 1)

```
autoTrading/
├── README.md
├── requirements.txt
├── .env.example
├── pyproject.toml          # Poetry 또는 pyproject 설정
├── .gitignore
│
├── data/                   # 주가 데이터 저장
│   ├── raw/               # 원본 데이터
│   ├── processed/         # 전처리된 데이터
│   └── backtest/          # 백테스팅 결과
│
├── src/
│   ├── config/            # 설정 관리
│   │   └── settings.py
│   │
│   ├── data/              # 데이터 수집 및 처리
│   │   ├── collector.py   # 주가 데이터 수집
│   │   ├── processor.py   # 데이터 전처리
│   │   └── validator.py   # 데이터 검증
│   │
│   ├── strategy/          # 트레이딩 전략
│   │   ├── base.py        # 전략 인터페이스
│   │   ├── moving_average.py
│   │   ├── momentum.py
│   │   └── rsi.py
│   │
│   ├── backtest/          # 백테스팅 엔진
│   │   ├── engine.py      # 백테스팅 메인 로직
│   │   ├── portfolio.py   # 포트폴리오 관리
│   │   └── metrics.py     # 성과 지표 계산
│   │
│   ├── risk/              # 리스크 관리
│   │   ├── position_sizing.py
│   │   └── stop_loss.py
│   │
│   └── utils/             # 유틸리티
│       ├── logger.py
│       └── exceptions.py  # 커스텀 에러
│
├── tests/                 # 테스트 코드
│   ├── test_strategy.py
│   ├── test_backtest.py
│   └── test_data.py
│
└── notebooks/             # Jupyter 노트북 (연구용)
    └── analysis.ipynb
```

## Phase 1: 백테스팅 구현 단계

### Step 1: 데이터 수집 시스템 (1주)
- [ ] 한국 주식 데이터 수집 구현 (pykrx)
- [ ] 데이터 저장 및 관리
- [ ] 데이터 품질 검증

### Step 2: 트레이딩 전략 구현 (1주)
- [ ] 전략 인터페이스 설계
- [ ] 단순 이동평균 전략 구현
- [ ] RSI 전략 구현

### Step 3: 백테스팅 엔진 (2주)
- [ ] 백테스팅 엔진 코어 구현
- [ ] 포트폴리오 관리
- [ ] 성과 지표 계산 (Sharpe Ratio, Max Drawdown 등)

### Step 4: 리스크 관리 (1주)
- [ ] 포지션 사이징
- [ ] 손절/익절 로직
- [ ] 포트폴리오 리밸런싱

### Step 5: 시각화 & 결과 분석 (1주)
- [ ] 백테스팅 결과 시각화
- [ ] 성과 리포트 생성
- [ ] 전략 비교 분석

## 프로젝트 구조 (Phase 2)

```
autoTrading/
├── backend/                 # Spring Boot 애플리케이션
│   ├── src/
│   │   ├── main/
│   │   │   ├── java/
│   │   │   │   └── com/autotrading/
│   │   │   │       ├── controller/     # REST API
│   │   │   │       ├── service/        # 비즈니스 로직
│   │   │   │       ├── repository/     # 데이터 접근
│   │   │   │       ├── entity/         # 도메인 모델
│   │   │   │       ├── dto/            # DTO
│   │   │   │       ├── config/         # 설정
│   │   │   │       ├── scheduler/      # 스케줄러
│   │   │   │       ├── exception/      # 예외 처리
│   │   │   │       └── AutoTradingApplication.java
│   │   │   └── resources/
│   │   │       ├── application.yml
│   │   │       └── application-dev.yml
│   │   └── test/                       # 테스트
│   ├── pom.xml                         # Maven 설정 (또는 build.gradle)
│   └── Dockerfile
│
└── (기존 Python 구조 유지)
```

## Phase 2: 자동 트레이딩 시스템 (추후 계획)

### Step 1: Spring Boot 3.5.7 프로젝트 초기화
- [ ] Spring Boot 프로젝트 생성
- [ ] Java 17 설정
- [ ] 필수 의존성 추가 (Web, Data JPA, Schedule, Validation 등)

### Step 2: RESTful API 설계
- [ ] 백테스팅 실행 API
- [ ] 전략 관리 API
- [ ] 결과 조회 API
- [ ] JWT 인증 구현

### Step 3: Python 엔진 연동
- [ ] REST API로 Python 백테스팅 엔진 호출
- [ ] 비동기 작업 처리 (CompletableFuture)
- [ ] 작업 큐 구현

### Step 4: 모니터링 & 알림
- [ ] 로깅 시스템 (Logback)
- [ ] Slack/Discord 알림
- [ ] 대시보드 구현 (Spring Boot Actuator)

### Step 5: 자동 주문 시스템
- [ ] API 키 관리 (암호화)
- [ ] 주문 실행 로직
- [ ] 에러 핸들링 및 재시도

## 리스크 관리
- 실제 투자 전 충분한 백테스팅 검증 필수
- 소액으로 시작
- 손실 리스크 인지

