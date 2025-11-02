"""
트레이딩 전략 인터페이스
모든 전략이 상속받을 추상 베이스 클래스
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
from loguru import logger


class BaseStrategy(ABC):
    """전략 추상 베이스 클래스"""

    def __init__(self, name: str, params: Optional[Dict] = None):
        """
        초기화
        
        Args:
            name: 전략 이름
            params: 전략 파라미터
        """
        self.name = name
        self.params = params or {}
        self.signals = []

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        거래 신호 생성
        
        Args:
            data: OHLCV 데이터프레임
        
        Returns:
            신호가 추가된 데이터프레임 (Signal 컬럼 추가: 1=매수, -1=매도, 0=보유)
        """
        pass

    @abstractmethod
    def calculate_position_size(
        self,
        portfolio_value: float,
        price: float,
        signal: float,
        **kwargs
    ) -> int:
        """
        포지션 사이징 계산
        
        Args:
            portfolio_value: 현재 포트폴리오 가치
            price: 현재가
            signal: 신호 (1=매수, -1=매도, 0=보유)
            **kwargs: 추가 파라미터
        
        Returns:
            거래 수량 (음수면 매도, 양수면 매수)
        """
        pass

    def validate_data(self, data: pd.DataFrame) -> bool:
        """
        데이터 유효성 검증
        
        Args:
            data: OHLCV 데이터프레임
        
        Returns:
            유효 여부
        """
        required_columns = ["Open", "High", "Low", "Close", "Volume"]
        if not all(col in data.columns for col in required_columns):
            logger.error(f"필수 컬럼 누락: {required_columns}")
            return False
        return True

    def get_signals(self) -> List[Dict]:
        """생성된 신호 리스트 반환"""
        return self.signals

    def reset(self):
        """전략 상태 초기화"""
        self.signals = []


class EqualWeightStrategy(BaseStrategy):
    """동일 비중 포지셔닝 전략"""

    def __init__(self, name: str, params: Optional[Dict] = None):
        super().__init__(name, params)
        self.position_pct = self.params.get("position_pct", 0.1)

    def calculate_position_size(
        self,
        portfolio_value: float,
        price: float,
        signal: float,
        **kwargs
    ) -> int:
        """
        동일 비중 포지션 사이징
        
        Args:
            portfolio_value: 포트폴리오 가치
            price: 현재가
            signal: 신호
            position_pct: 비중
        
        Returns:
            거래 수량
        """
        if signal == 0:
            return 0
        
        target_value = portfolio_value * self.position_pct
        quantity = int(target_value / price)
        
        return quantity if signal > 0 else -quantity

