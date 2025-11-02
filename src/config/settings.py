"""
프로젝트 설정 모듈
환경 변수를 통한 설정 관리
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pathlib import Path


class Settings(BaseSettings):
    """애플리케이션 설정"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # 프로젝트 루트 경로
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent
    
    # 데이터 경로
    DATA_RAW_DIR: Path = PROJECT_ROOT / "data" / "raw"
    DATA_PROCESSED_DIR: Path = PROJECT_ROOT / "data" / "processed"
    DATA_BACKTEST_DIR: Path = PROJECT_ROOT / "data" / "backtest"
    
    # 로그 경로
    LOG_DIR: Path = PROJECT_ROOT / "logs"
    
    # 백테스팅 기본 설정
    DEFAULT_INITIAL_CASH: float = Field(default=100_000, description="초기 자본금 (USD)")
    DEFAULT_COMMISSION: float = Field(default=0.001, description="수수료율 (0.1%)")
    
    # 데이터 수집 설정 (미국 주식)
    MARKET: str = Field(default="US", description="거래 시장")


settings = Settings()


def get_settings() -> Settings:
    """설정 인스턴스 반환"""
    return settings

