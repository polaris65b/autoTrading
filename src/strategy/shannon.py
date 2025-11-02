"""
섀넌 전략 (Shannon Strategy)
현금과 주식을 일정 비율로 유지하며 주기적으로 리밸런싱
"""

from typing import Dict, Optional
import pandas as pd
from loguru import logger

from src.strategy.base import BaseStrategy


class ShannonStrategy(BaseStrategy):
    """
    섀넌 전략
    
    현금과 주식을 일정 비율(기본 50:50)로 유지하며 리밸런싱
    또는 채권 ETF와 주식을 일정 비율로 유지 (bond_ticker 설정 시)
    
    리밸런싱 방식:
    - time_based: 주기 기반 (특정 주기마다 리밸런싱)
    - banding: 밴딩 기반 (목표 비율에서 일정 범위 벗어날 때만 리밸런싱)
    """

    def __init__(self, name: str = "Shannon", params: Optional[Dict] = None):
        """
        초기화
        
        Args:
            name: 전략 이름
            params: 전략 파라미터
                - stock_pct: 주식 비율 (기본: 0.5 = 50%)
                - stock_ticker: 주식 종목 티커 (기본: None, 엔진에서 설정)
                - bond_ticker: 채권 종목 티커 (기본: None = 현금 사용)
                - rebalance_mode: 리밸런싱 방식 ("time_based" 또는 "banding", 기본: "banding")
                - rebalance_freq: 리밸런싱 주기 (일 단위, time_based 모드에서만 사용)
                - band_threshold: 밴딩 임계값 (기본: 0.05 = 5%, banding 모드에서만 사용)
        """
        super().__init__(name, params or {})
        self.stock_pct = self.params.get("stock_pct", 0.5)  # 주식 비율 (50%)
        self.stock_ticker = self.params.get("stock_ticker", None)  # 주식 종목
        self.bond_ticker = self.params.get("bond_ticker", None)  # 채권 종목 (None이면 현금)
        self.rebalance_mode = self.params.get("rebalance_mode", "banding")  # 리밸런싱 방식
        self.rebalance_freq = self.params.get("rebalance_freq", 30)  # 리밸런싱 주기 (30일)
        self.band_threshold = self.params.get("band_threshold", 0.1)  # 밴딩 임계값 (10%)
        self.last_rebalance_date = None
        
        # 채권 사용 여부 확인
        self.use_bond = self.bond_ticker is not None

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        거래 신호 생성
        
        Args:
            data: OHLCV 데이터프레임
        
        Returns:
            신호가 추가된 데이터프레임
            - Signal = 1: 초기 매수
            - Signal = 2: 리밸런싱 (time_based 모드에서만)
            - Signal = 3: 밴딩 리밸런싱 체크 필요 (banding 모드)
            - Signal = 0: 보유
        """
        if not self.validate_data(data):
            raise ValueError("데이터 유효성 검증 실패")
        
        df = data.copy()
        df["Signal"] = 0
        
        # 첫날 매수 신호 (초기 포지션 진입)
        df.iloc[0, df.columns.get_loc("Signal")] = 1
        
        if self.rebalance_mode == "time_based":
            # 주기 기반 리밸런싱
            last_date = None
            for idx, date in enumerate(df.index):
                if idx == 0:
                    last_date = date
                    continue
                
                # 리밸런싱 주기 체크
                days_diff = (date - last_date).days if last_date else self.rebalance_freq
                
                if days_diff >= self.rebalance_freq:
                    # 리밸런싱 신호 (2 = 리밸런싱)
                    df.iloc[idx, df.columns.get_loc("Signal")] = 2
                    last_date = date
                    self.last_rebalance_date = date
            
            rebalance_count = (df["Signal"] == 2).sum()
            logger.info(
                f"섀넌 전략 (주기 기반) 신호 생성 완료: {len(df)}개 일봉, "
                f"초기 매수 1회, 리밸런싱 {rebalance_count}회"
            )
        
        elif self.rebalance_mode == "banding":
            # 밴딩 기반 리밸런싱 - 매일 체크 필요
            # 실제 밴딩 체크는 엔진에서 포트폴리오 상태를 보고 결정
            for idx in range(1, len(df)):
                df.iloc[idx, df.columns.get_loc("Signal")] = 3  # 밴딩 체크 신호
            
            logger.info(
                f"섀넌 전략 (밴딩 기반) 신호 생성 완료: {len(df)}개 일봉, "
                f"초기 매수 1회, 매일 밴딩 체크 ({self.band_threshold*100:.1f}% 임계값)"
            )
        
        return df

    def check_banding_rebalance(
        self,
        portfolio_value: float,
        current_stock_value: float,
        price: float,
        current_quantity: int,
        cash: float,
        current_bond_value: float = 0.0
    ) -> bool:
        """
        밴딩 리밸런싱 필요 여부 체크
        
        Args:
            portfolio_value: 전체 포트폴리오 가치
            current_stock_value: 현재 주식 가치
            price: 현재가
            current_quantity: 현재 보유 수량
            cash: 현재 현금
            current_bond_value: 현재 채권 가치 (bond_ticker 사용 시)
        
        Returns:
            리밸런싱 필요 여부
        """
        if portfolio_value == 0:
            return False
        
        # 현재 주식 비율
        current_stock_pct = current_stock_value / portfolio_value
        
        # 목표 비율과의 차이
        diff = abs(current_stock_pct - self.stock_pct)
        
        # 임계값을 넘으면 리밸런싱 필요
        return diff >= self.band_threshold

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
            portfolio_value: 포트폴리오 가치 (현금 + 보유 종목 평가금)
            price: 현재가
            signal: 신호 (1=초기 매수, 2=주기 리밸런싱, 3=밴딩 체크, 0=보유)
            **kwargs: 추가 파라미터
                - current_quantity: 현재 보유 수량
                - cash: 현재 현금
                - current_bond_value: 현재 채권 가치 (bond_ticker 사용 시)
                - commission_rate: 수수료율
                - ticker: 현재 거래하는 종목 (stock_ticker 또는 bond_ticker)
        
        Returns:
            거래 수량 (양수=매수, 음수=매도, 0=보유)
        """
        if signal == 0:
            return 0
        
        current_quantity = kwargs.get("current_quantity", 0)
        cash = kwargs.get("cash", portfolio_value)
        current_bond_value = kwargs.get("current_bond_value", 0.0)
        commission_rate = kwargs.get("commission_rate", 0.001)
        ticker = kwargs.get("ticker", None)
        
        # 거래하는 종목이 주식인지 채권인지 확인
        is_stock = ticker == self.stock_ticker or (self.stock_ticker is None and ticker is not None and ticker != self.bond_ticker)
        
        if is_stock:
            # 주식 포지션 계산
            current_stock_value = current_quantity * price
            target_stock_value = portfolio_value * self.stock_pct
            target_quantity = int(target_stock_value / price)
        else:
            # 채권 포지션 계산 (채권 사용 시)
            if not self.use_bond:
                return 0
            current_bond_value_calc = current_quantity * price
            target_bond_value = portfolio_value * (1 - self.stock_pct)
            target_quantity = int(target_bond_value / price)
            current_stock_value = kwargs.get("current_stock_value", 0.0)
        
        if signal == 1:  # 초기 매수
            if is_stock:
                adjusted_target = target_stock_value * (1 - commission_rate)
                target_quantity = int(adjusted_target / price)
            else:
                adjusted_target = target_bond_value * (1 - commission_rate)
                target_quantity = int(adjusted_target / price)
            return target_quantity
        
        elif signal == 2:  # 주기 기반 리밸런싱
            quantity_diff = target_quantity - current_quantity
            
            if abs(quantity_diff) > 0:
                if quantity_diff > 0:
                    required_cash = quantity_diff * price * (1 + commission_rate)
                    available_cash = cash if is_stock else (cash + current_bond_value if self.use_bond else cash)
                    if available_cash < required_cash:
                        available_quantity = int(available_cash / (price * (1 + commission_rate)))
                        quantity_diff = min(quantity_diff, available_quantity)
                
                return quantity_diff
        
        elif signal == 3:  # 밴딩 체크
            if is_stock:
                current_stock_value_for_check = current_quantity * price
            else:
                current_stock_value_for_check = kwargs.get("current_stock_value", 0.0)
            
            if self.check_banding_rebalance(
                portfolio_value=portfolio_value,
                current_stock_value=current_stock_value_for_check,
                price=price,
                current_quantity=current_quantity,
                cash=cash,
                current_bond_value=current_bond_value
            ):
                quantity_diff = target_quantity - current_quantity
                
                if abs(quantity_diff) > 0:
                    if quantity_diff > 0:
                        required_cash = quantity_diff * price * (1 + commission_rate)
                        available_cash = cash if is_stock else (cash + current_bond_value if self.use_bond else cash)
                        if available_cash < required_cash:
                            available_quantity = int(available_cash / (price * (1 + commission_rate)))
                            quantity_diff = min(quantity_diff, available_quantity)
                    
                    return quantity_diff
        
        return 0

