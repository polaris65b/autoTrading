"""
설정 파일 로더
YAML 기반 설정 파일 로딩 및 검증
"""

from pathlib import Path
from typing import Dict, List, Optional
import yaml
from pydantic import BaseModel, Field, field_validator
from loguru import logger

from src.utils.exceptions import DataCollectionError


class StopLossConfig(BaseModel):
    """손절 설정"""
    enabled: bool = True
    threshold: float = Field(default=-0.10, ge=-1.0, le=0.0, description="손절 기준")


class TakeProfitConfig(BaseModel):
    """익절 설정"""
    enabled: bool = False
    threshold: float = Field(default=0.20, ge=0.0, le=10.0, description="익절 기준")


class RiskConfig(BaseModel):
    """리스크 관리 설정"""
    max_positions: int = Field(default=10, ge=1, le=50, description="최대 보유 종목 수")
    max_position_weight: float = Field(default=0.25, gt=0.0, le=1.0, description="종목당 최대 비중")
    stop_loss: StopLossConfig = Field(default_factory=StopLossConfig)
    take_profit: TakeProfitConfig = Field(default_factory=TakeProfitConfig)


class AssetTargetWeight(BaseModel):
    """종목별 목표 비중"""
    ticker: str
    weight: float = Field(gt=0.0, le=1.0)


class StrategyParams(BaseModel):
    """전략 파라미터"""
    position_pct: Optional[float] = None  # Buy & Hold 전략용 (투자 비율)
    stock_pct: Optional[float] = None  # 섀넌 전략용 (주식 비율)
    stock_ticker: Optional[str] = None  # 주식 종목 티커 (BuyHold, MovingAverage, Shannon 전략용)
    bond_ticker: Optional[str] = None  # 채권 종목 티커 (MovingAverage, Shannon 전략용)
    ma_period: Optional[int] = None  # 이동평균 기간 (MovingAverage 전략용)
    base_ticker: Optional[str] = None  # 기준 종목 티커 (MovingAverageBreakout 전략용)
    conservative_ticker: Optional[str] = None  # 보수적 종목 티커 (MovingAverageBreakout 전략용)
    aggressive_ticker: Optional[str] = None  # 공격적 종목 티커 (MovingAverageBreakout 전략용)
    lookback_period: Optional[int] = None  # 전 고점 계산 기간 (MovingAverageBreakout 전략용)
    stock_ticker1: Optional[str] = None  # 주식 종목 1 티커 (MovingAverageRebalance 전략용)
    stock_ticker2: Optional[str] = None  # 주식 종목 2 티커 (MovingAverageRebalance 전략용)
    stock1_pct: Optional[float] = None  # 주식 종목 1 목표 비율 (MovingAverageRebalance 전략용)
    stock2_pct: Optional[float] = None  # 주식 종목 2 목표 비율 (MovingAverageRebalance 전략용)
    rebalance_mode: Optional[str] = None  # 리밸런싱 방식 ("time_based" 또는 "banding")
    rebalance_freq: Optional[int] = None  # 리밸런싱 주기 (일 단위, time_based 모드)
    band_threshold: Optional[float] = None  # 밴딩 임계값 (0.05 = 5%, banding 모드)
    fast_period: Optional[int] = None  # 이동평균선 전략용
    slow_period: Optional[int] = None  # 이동평균선 전략용
    target_weights: Optional[List[AssetTargetWeight]] = None  # 리밸런싱 전략용


class StrategyConfig(BaseModel):
    """전략 설정"""
    name: str
    enabled: bool = True
    params: Optional[StrategyParams] = Field(default_factory=StrategyParams)


class PortfolioConfig(BaseModel):
    """포트폴리오 설정"""
    strategies: List[StrategyConfig] = Field(default_factory=list)


class BacktestConfig(BaseModel):
    """백테스팅 기본 설정"""
    start_date: str
    end_date: str
    initial_cash: float = Field(default=100_000, gt=0, description="초기 자본금")
    commission_rate: float = Field(default=0.001, ge=0, le=0.01, description="수수료율")
    monthly_addition: Optional[float] = Field(default=0, ge=0, description="매월 추가 투자금")
    exchange_rate: Optional[float] = Field(default=1.0, gt=0, description="환율 (예: 1450 = 1달러당 1450원)")

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        """날짜 형식 검증"""
        try:
            from datetime import datetime
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError(f"날짜 형식이 올바르지 않습니다: {v} (예상: YYYY-MM-DD)")


class AssetsConfig(BaseModel):
    """자산 설정"""
    tickers: List[str] = Field(default_factory=list, description="거래할 종목 목록")
    auto_select: bool = False
    market_cap_min: Optional[int] = None
    sectors: List[str] = Field(default_factory=list)


class ReportConfig(BaseModel):
    """리포트 설정"""
    save_results: bool = True
    generate_charts: bool = True
    verbose: bool = False


class ConfigModel(BaseModel):
    """전체 설정 모델"""
    backtest: BacktestConfig
    portfolio: PortfolioConfig
    assets: AssetsConfig
    risk: RiskConfig = Field(default_factory=RiskConfig)
    report: ReportConfig = Field(default_factory=ReportConfig)

    @field_validator("assets")
    @classmethod
    def validate_assets(cls, v: AssetsConfig, info) -> AssetsConfig:
        """자산 설정 검증"""
        if not v.tickers and not v.auto_select:
            raise ValueError("최소 하나의 종목 또는 auto_select가 설정되어야 합니다")
        return v


class ConfigLoader:
    """설정 로더"""

    def __init__(self, config_path: Path):
        """
        초기화
        
        Args:
            config_path: 설정 파일 경로
        """
        self.config_path = Path(config_path)
        if not self.config_path.exists():
            raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {self.config_path}")

    def load(self) -> ConfigModel:
        """
        설정 파일 로드 및 검증
        
        Returns:
            설정 모델 인스턴스
        """
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config_dict = yaml.safe_load(f)
            
            if config_dict is None:
                raise ValueError("설정 파일이 비어있습니다")
            
            config = ConfigModel.model_validate(config_dict)
            logger.info(f"설정 파일 로드 완료: {self.config_path}")
            
            return config
            
        except yaml.YAMLError as e:
            logger.error(f"YAML 파싱 오류: {e}")
            raise DataCollectionError(f"설정 파일 파싱 실패: {e}") from e
        except Exception as e:
            logger.error(f"설정 로드 실패: {e}")
            raise

    def load_raw(self) -> Dict:
        """
        원본 딕셔너리로 로드 (검증 없이)
        
        Returns:
            설정 딕셔너리
        """
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    @staticmethod
    def validate_config(config_dict: Dict) -> bool:
        """
        설정 검증
        
        Args:
            config_dict: 설정 딕셔너리
        
        Returns:
            유효 여부
        """
        try:
            ConfigModel.model_validate(config_dict)
            return True
        except Exception as e:
            logger.error(f"설정 검증 실패: {e}")
            return False


def load_config(config_path: Path = Path("config.yml")) -> ConfigModel:
    """
    설정 파일 로드 헬퍼 함수
    
    Args:
        config_path: 설정 파일 경로
    
    Returns:
        설정 모델 인스턴스
    """
    loader = ConfigLoader(config_path)
    return loader.load()

