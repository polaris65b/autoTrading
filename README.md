# 📈 Stock Backtesting & Auto Trading System

주식 백테스팅 및 자동 트레이딩 시스템

## 🎯 프로젝트 목표

### Phase 1: 백테스팅 시스템 (진행 중)
- **미국** 주식 데이터 수집 및 관리
- 트레이딩 전략 구현 및 검증
- 백테스팅 엔진 개발
- 성과 분석 및 시각화

### Phase 2: 자동 트레이딩 시스템 (예정)
- Spring Boot API 서버 구축
- 실시간 주문 실행
- 모니터링 및 알림

## 🛠 기술 스택

### Phase 1: 백테스팅 (Python)
- **언어**: Python 3.12.8
- **패키지 관리**: pip, venv
- **데이터 처리**: pandas 2.3+, numpy 2.3+
- **데이터 수집**: yfinance (미국 주식)
- **시각화**: matplotlib, seaborn, plotly
- **테스팅**: pytest
- **코드 품질**: black, flake8, mypy, isort
- **로깅**: loguru

### Phase 2: 자동 트레이딩 (Spring Boot)
- **프레임워크**: Spring Boot 3.5.7
- **언어**: Java 17+
- **빌드 도구**: Maven / Gradle
- **데이터베이스**: H2 (개발), PostgreSQL (운영)
- **인증**: JWT
- **스케줄링**: Spring Scheduler
- **모니터링**: Spring Boot Actuator

## 📁 프로젝트 구조

```
autoTrading/
├── README.md                  # 프로젝트 소개
├── USAGE.md                   # 사용법 가이드
├── PROJECT_PLAN.md            # 프로젝트 계획
├── requirements.txt           # Python 패키지 목록
├── .env.example               # 환경 변수 예제
├── .tool-versions             # asdf 버전 고정
│
├── data/                      # 데이터 저장
│   ├── raw/                   # 원본 데이터
│   ├── processed/             # 전처리된 데이터
│   └── backtest/              # 백테스팅 결과
│
├── config.yml.example        # 설정 파일 예제
│
├── src/                       # 소스 코드
│   ├── config/                # 설정 관리
│   │   ├── loader.py         # 설정 로더
│   │   └── settings.py       # 기본 설정
│   ├── data/                  # 데이터 수집 및 처리
│   ├── strategy/              # 트레이딩 전략
│   ├── backtest/              # 백테스팅 엔진
│   ├── risk/                  # 리스크 관리
│   └── utils/                 # 유틸리티
│
├── examples/                  # 예제 스크립트
│   ├── collect_data.py        # 데이터 수집 예제
│   ├── portfolio_demo.py      # 포트폴리오 데모
│   ├── config_demo.py         # 설정 파일 데모
│   └── config_generator.py    # 설정 파일 생성기
│
├── tests/                     # 테스트 코드
├── notebooks/                 # Jupyter 노트북
└── logs/                      # 로그 파일
```

## 📖 사용법

- **빠른 시작**: [GETTING_STARTED.md](GETTING_STARTED.md) - 5분 안에 시작하기
- **상세 가이드**: [USAGE.md](USAGE.md) - 전체 사용법

### ⚡ 가장 간단한 사용법 (초보자용)

**설정 파일에서 종목만 바꾸면 바로 사용할 수 있습니다!**

```bash
# 1. 가상환경 활성화
source venv/bin/activate

# 2. 백테스팅 실행 (제공된 설정 파일 사용)
python backtest.py -c config_qqq.yaml   # QQQ 백테스팅
python backtest.py -c config_aapl.yaml  # AAPL 백테스팅
python backtest.py -c config_spy.yaml   # SPY 백테스팅
```

**다른 종목으로 테스트하려면:**
1. `config_qqq.yaml` 파일을 열어서
2. `"QQQ"` 부분만 원하는 종목으로 바꾸기 (예: `"TSLA"`, `"GOOGL"`)
3. 저장하고 실행

**더 자세한 설명:** [GETTING_STARTED.md](GETTING_STARTED.md) 참고

---

### 🛠️ 개발자용 도구

```bash
# 대화형 설정 파일 생성
python examples/config_generator.py

# 설정 파일 확인
python examples/config_demo.py

# 포트폴리오 관리 데모
python examples/portfolio_demo.py

# 데이터 수집
python examples/collect_data.py
```

## 🚀 시작하기

### 1. 저장소 클론
```bash
git clone <repository-url>
cd autoTrading
```

### 2. Python 환경 설정
```bash
# asdf를 사용하는 경우
asdf install
asdf set python 3.12.8

# 가상환경 생성 및 활성화
python3.12 -m venv venv
source venv/bin/activate  # macOS/Linux
# 또는
venv\Scripts\activate     # Windows
```

### 3. 의존성 설치
```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### 4. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일 편집 (필요시)
```

### 5. 개발 환경 설정
```bash
# 코드 포맷터 설치 (선택사항)
pip install black flake8 mypy isort

# 테스트 실행
pytest tests/
```

## 📝 개발 원칙

- **Clean Code**: 가독성과 유지보수성 우선
- **SOLID 원칙**: 객체지향 설계 원칙 준수
- **DRY**: 코드 중복 지양
- **테스트**: 단위 테스트 필수
- **문서화**: 공식 문서 형태 코드 작성
- **하드코딩 지양**: 설정 기반 관리
- **글로벌 에러 처리**: 중앙화된 예외 관리

## 📊 개발 단계

- [x] 프로젝트 구조 설계
- [x] 개발 환경 설정
- [x] 데이터 수집 시스템 (yfinance)
- [x] Buy & Hold 전략 구현
- [x] 백테스팅 엔진 개발 (단일 종목)
- [x] 설정 파일 시스템
- [ ] 다중 종목 전략 (섀넌, 이동평균, 리밸런싱)
- [ ] 리스크 관리 시스템
- [ ] 시각화 및 분석
- [ ] API 서버 구축 (Phase 2)
- [ ] 자동 주문 시스템 (Phase 2)

## 📚 참고 문서

### Python
- [pandas 공식 문서](https://pandas.pydata.org/)
- [yfinance GitHub](https://github.com/ranaroussi/yfinance)
- [matplotlib 공식 문서](https://matplotlib.org/)

### Spring Boot
- [Spring Boot 공식 문서](https://spring.io/projects/spring-boot)
- [Spring Boot 3.5.7 릴리즈 노트](https://spring.io/blog/2025/10/23/spring-boot-3-5-7-available-now)

## ⚠️ 주의사항

- 본 프로젝트는 교육 및 개인 투자용입니다
- 실제 투자에 사용하기 전 충분한 검증이 필요합니다
- 투자 손실에 대한 책임은 사용자에게 있습니다

## 📄 라이선스

MIT License
