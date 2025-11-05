"""
이동평균선 기반 섀넌 하이브리드 전략
200일선 위: TQQQ 100% (BuyHold)
200일선 아래: 섀넌 전략 (TQQQ 50% + 현금 50%, 밴딩 방식)
"""

from typing import Dict, Optional
import pandas as pd
from loguru import logger

from src.strategy.base import BaseStrategy


class MovingAverageShannonHybridStrategy(BaseStrategy):
    """
    이동평균선 기반 섀넌 하이브리드 전략
    
    주식 종목의 n일 이동평균선을 기준으로:
    - n일선 위: 주식 100% 보유 (BuyHold)
    - n일선 아래: 섀넌 전략 (주식 50% + 현금 50%, 밴딩 방식)
    
    기본값은 200일선이며, config에서 ma_period로 변경 가능
    """

    def __init__(self, name: str = "MovingAverageShannonHybrid", params: Optional[Dict] = None):
        """
        초기화
        
        Args:
            name: 전략 이름
            params: 전략 파라미터
                - stock_ticker: 주식 종목 (기본: "TQQQ")
                - bond_ticker: 채권/대체 자산 (기본: None = 현금 사용)
                - ma_period: 이동평균 기간 (기본: 200)
                - stock_pct: 섀넌 모드에서 주식 비율 (기본: 0.5 = 50%)
                - band_threshold: 밴딩 임계값 (기본: 0.1 = 10%)
        """
        super().__init__(name, params or {})
        self.stock_ticker = self.params.get("stock_ticker", "TQQQ")
        self.bond_ticker = self.params.get("bond_ticker", None)
        self.ma_period = self.params.get("ma_period", 200)
        self.stock_pct = self.params.get("stock_pct", 0.5)
        self.band_threshold = self.params.get("band_threshold", 0.1)
        
        self.use_bond = self.bond_ticker is not None
        
        self.current_mode = None  # "ABOVE" 또는 "BELOW"
        self.current_holding = None

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        거래 신호 생성
        
        주식 데이터를 기준으로 n일선을 계산하고,
        현재가와 이동평균선 위치에 따라 모드 결정 및 신호 생성
        
        Args:
            data: OHLCV 데이터프레임 (주식 종목 데이터)
        
        Returns:
            신호가 추가된 데이터프레임
            - Signal = 1: 모드 전환 필요 (초기 진입 포함)
            - Signal = 3: 밴딩 체크 필요 (200일선 아래 모드일 때)
            - Signal = 0: 보유
            - Mode: "ABOVE" 또는 "BELOW" (각 날짜의 모드)
        """
        if not self.validate_data(data):
            raise ValueError("데이터 유효성 검증 실패")
        
        df = data.copy()
        df["Signal"] = 0
        df["Mode"] = None
        
        ma_column = f"MA{self.ma_period}"
        df[ma_column] = df["Close"].rolling(window=self.ma_period, min_periods=1).mean()
        
        # 첫날 모드 결정 및 초기 매수 신호
        first_close = df.iloc[0]["Close"]
        first_ma = df.iloc[0][ma_column]
        
        if first_close >= first_ma:
            df.iloc[0, df.columns.get_loc("Signal")] = 1
            df.iloc[0, df.columns.get_loc("Mode")] = "ABOVE"
            self.current_mode = "ABOVE"
            self.current_holding = self.stock_ticker
        else:
            df.iloc[0, df.columns.get_loc("Signal")] = 1
            df.iloc[0, df.columns.get_loc("Mode")] = "BELOW"
            self.current_mode = "BELOW"
            self.current_holding = self.stock_ticker
        
        # 이후 날짜들 처리
        for idx in range(1, len(df)):
            prev_close = df.iloc[idx - 1]["Close"]
            prev_ma = df.iloc[idx - 1][ma_column]
            curr_close = df.iloc[idx]["Close"]
            curr_ma = df.iloc[idx][ma_column]
            
            prev_below = prev_close < prev_ma
            curr_above = curr_close >= curr_ma
            
            prev_above = prev_close >= prev_ma
            curr_below = curr_close < curr_ma
            
            # 모드 전환 체크
            if (prev_below and curr_above) or (prev_above and curr_below):
                df.iloc[idx, df.columns.get_loc("Signal")] = 1
                if curr_above:
                    df.iloc[idx, df.columns.get_loc("Mode")] = "ABOVE"
                    self.current_mode = "ABOVE"
                else:
                    df.iloc[idx, df.columns.get_loc("Mode")] = "BELOW"
                    self.current_mode = "BELOW"
            else:
                # 모드 유지
                prev_mode = df.iloc[idx - 1, df.columns.get_loc("Mode")]
                df.iloc[idx, df.columns.get_loc("Mode")] = prev_mode
                self.current_mode = prev_mode
                
                # 200일선 아래 모드일 때는 밴딩 체크 필요
                if prev_mode == "BELOW":
                    df.iloc[idx, df.columns.get_loc("Signal")] = 3
        
        signal_count = (df["Signal"] == 1).sum()
        banding_count = (df["Signal"] == 3).sum()
        logger.info(
            f"{self.ma_period}일선 하이브리드 전략 신호 생성 완료: {len(df)}개 일봉, "
            f"모드 전환 {signal_count}회, 밴딩 체크 {banding_count}회"
        )
        
        return df

    def check_banding_rebalance(
        self,
        portfolio_value: float,
        current_stock_value: float,
        price: float,
        current_quantity: int
    ) -> bool:
        """
        밴딩 리밸런싱 필요 여부 체크 (200일선 아래 모드에서만 사용)
        
        Args:
            portfolio_value: 전체 포트폴리오 가치
            current_stock_value: 현재 주식 가치
            price: 현재가
            current_quantity: 현재 보유 수량
        
        Returns:
            리밸런싱 필요 여부
        """
        if portfolio_value == 0:
            return False
        
        current_stock_pct = current_stock_value / portfolio_value
        
        # 현금 버전: TQQQ 비율 상한선을 더 엄격하게 적용
        if not self.use_bond:
            # 현금 버전: TQQQ 비율이 목표 비율(stock_pct)을 초과하면 무조건 리밸런싱
            if current_stock_pct > self.stock_pct:
                return True
            # 하한선은 밴딩 임계값 적용 (40% 이하일 때 매수)
            diff = self.stock_pct - current_stock_pct
            return diff >= self.band_threshold
        else:
            # BIL/QYLD 버전: 양방향 밴딩 (기존 로직)
            diff = abs(current_stock_pct - self.stock_pct)
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
        
        200일선 위 모드:
        - TQQQ 100% 보유 (BuyHold 방식)
        - bond_ticker 사용 시: bond_ticker 전량 매도
        
        200일선 아래 모드:
        - TQQQ 50% + (현금/bond_ticker) 50% (섀넌 전략, 밴딩 방식)
        
        Args:
            portfolio_value: 포트폴리오 가치
            price: 현재가
            signal: 신호 (1=모드 전환, 3=밴딩 체크, 0=보유)
            **kwargs: 추가 파라미터
                - current_quantity: 현재 보유 수량
                - cash: 현재 현금
                - commission_rate: 수수료율
                - ticker: 현재 거래하는 종목
                - mode: 현재 모드 ("ABOVE" 또는 "BELOW")
                - current_stock_value: 현재 주식 가치 (bond_ticker 처리 시 필요)
                - current_bond_value: 현재 채권 가치 (stock_ticker 처리 시 필요)
        
        Returns:
            거래 수량 (양수=매수, 음수=매도, 0=보유)
        """
        if signal == 0:
            return 0
        
        current_quantity = kwargs.get("current_quantity", 0)
        cash = kwargs.get("cash", portfolio_value)
        commission_rate = kwargs.get("commission_rate", 0.001)
        ticker = kwargs.get("ticker", None)
        mode = kwargs.get("mode", self.current_mode)
        current_stock_value = kwargs.get("current_stock_value", 0.0)
        current_bond_value = kwargs.get("current_bond_value", 0.0)
        
        if ticker == self.stock_ticker:
            return self._calculate_stock_position_size(
                portfolio_value, price, signal, current_quantity, cash, commission_rate, mode, current_bond_value
            )
        elif self.use_bond and ticker == self.bond_ticker:
            return self._calculate_bond_position_size(
                portfolio_value, price, signal, current_quantity, cash, commission_rate,
                mode, current_stock_value, current_bond_value
            )
        
        return 0
    
    def _calculate_stock_position_size(
        self,
        portfolio_value: float,
        price: float,
        signal: float,
        current_quantity: int,
        cash: float,
        commission_rate: float,
        mode: str,
        current_bond_value: float = 0.0
    ) -> int:
        if signal == 1:
            if mode == "ABOVE":
                target_value = portfolio_value * (1 - commission_rate)
                target_quantity = int(target_value / price)
                quantity_diff = target_quantity - current_quantity
                return quantity_diff
            else:  # BELOW 모드 진입
                target_value = portfolio_value * self.stock_pct * (1 - commission_rate)
                target_quantity = int(target_value / price)
                quantity_diff = target_quantity - current_quantity
                
                # 매수 케이스 (quantity_diff > 0): 현금 한도 내에서만 매수
                if quantity_diff > 0:
                    required_cash = quantity_diff * price * (1 + commission_rate)
                    available_cash = cash
                    if self.use_bond:
                        # bond_ticker를 팔아서 매수 자금 확보 가능
                        available_cash = cash
                    if available_cash < required_cash:
                        available_quantity = int(available_cash / (price * (1 + commission_rate)))
                        quantity_diff = min(quantity_diff, available_quantity)
                
                # 매도 케이스 (quantity_diff < 0): TQQQ를 50%로 맞추기 위해 매도
                # quantity_diff < 0이면 이미 계산된 매도 수량을 반환
                
                return quantity_diff
        
        elif signal == 3:
            if mode != "BELOW":
                return 0
            
            current_stock_value = current_quantity * price
            current_stock_pct = current_stock_value / portfolio_value if portfolio_value > 0 else 0
            
            # 현금 버전: TQQQ 비율이 50%를 초과하면 무조건 매도 (체크 조건 무시)
            if not self.use_bond and current_stock_pct > self.stock_pct:
                target_value = portfolio_value * self.stock_pct
                target_quantity = int(target_value / price)
                quantity_diff = target_quantity - current_quantity
                # 매도만 허용 (quantity_diff < 0)
                if quantity_diff < 0:
                    logger.warning(
                        f"🔴 [전략 로직] 현금버전 TQQQ > 50% 감지 - 매도 실행: "
                        f"현재={current_stock_pct:.2%} 목표={self.stock_pct:.2%} "
                        f"현재수량={current_quantity} 목표수량={target_quantity} "
                        f"매도 필요: {abs(quantity_diff)}주"
                    )
                    return quantity_diff
                logger.warning(
                    f"🟡 [전략 로직] 현금버전 TQQQ > 50%지만 quantity_diff >= 0 (매도 안 됨!): "
                    f"현재={current_stock_pct:.2%} 현재수량={current_quantity} 목표수량={target_quantity} "
                    f"quantity_diff={quantity_diff}"
                )
                return 0
            
            # BIL/QYLD 버전 또는 현금 버전(하한선 체크): 기존 밴딩 로직
            needs_rebalance = self.check_banding_rebalance(
                portfolio_value=portfolio_value,
                current_stock_value=current_stock_value,
                price=price,
                current_quantity=current_quantity
            )
            
            if not self.use_bond:
                logger.debug(
                    f"[전략 로직] 현금버전 check_banding_rebalance: "
                    f"결과={needs_rebalance} 현재비율={current_stock_pct:.2%}"
                )
            
            if needs_rebalance:
                target_value = portfolio_value * self.stock_pct
                target_quantity = int(target_value / price)
                quantity_diff = target_quantity - current_quantity
                
                if not self.use_bond:
                    logger.debug(
                        f"[전략 로직] 현금버전 리밸런싱 필요: "
                        f"목표={self.stock_pct:.2%} quantity_diff={quantity_diff}"
                    )
                
                # 매수 케이스 (quantity_diff > 0)
                if quantity_diff > 0:
                    required_cash = quantity_diff * price * (1 + commission_rate)
                    available_cash = cash
                    if self.use_bond:
                        # bond_ticker를 팔아서 매수 자금 확보 가능
                        available_cash = cash
                    if available_cash < required_cash:
                        available_quantity = int(available_cash / (price * (1 + commission_rate)))
                        quantity_diff = min(quantity_diff, available_quantity)
                        if not self.use_bond:
                            logger.debug(
                                f"[전략 로직] 현금버전 현금부족: "
                                f"필요=${required_cash:.2f} 보유=${available_cash:.2f} "
                                f"조정량={quantity_diff}"
                            )
                
                # 매도 케이스 (quantity_diff < 0): 현금 버전에서는 명시적으로 처리
                # 매도는 허용하되, 목표 비율(50%)로 조정
                # quantity_diff < 0이면 이미 매도 필요량이 계산됨
                
                return quantity_diff
        
        return 0
    
    def _calculate_bond_position_size(
        self,
        portfolio_value: float,
        price: float,
        signal: float,
        current_quantity: int,
        cash: float,
        commission_rate: float,
        mode: str,
        current_stock_value: float,
        current_bond_value: float
    ) -> int:
        if signal == 1:
            if mode == "ABOVE":
                return -current_quantity
            else:
                target_value = portfolio_value * (1 - self.stock_pct) * (1 - commission_rate)
                target_quantity = int(target_value / price)
                quantity_diff = target_quantity - current_quantity
                return quantity_diff
        
        elif signal == 3:
            if mode != "BELOW":
                return 0
            
            current_stock_pct = current_stock_value / portfolio_value if portfolio_value > 0 else 0
            diff = abs(current_stock_pct - self.stock_pct)
            
            if diff >= self.band_threshold:
                target_value = portfolio_value * (1 - self.stock_pct)
                target_quantity = int(target_value / price)
                quantity_diff = target_quantity - current_quantity
                return quantity_diff
        
        return 0
