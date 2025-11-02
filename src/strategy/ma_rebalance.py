"""
이동평균선 기반 다중 자산 리밸런싱 전략
n일선 위: QQQM:TQQQ 5:5 비율, 밴딩 리밸런싱
n일선 아래: BIL 보유
"""

from typing import Dict, Optional
import pandas as pd
from loguru import logger

from src.strategy.base import BaseStrategy


class MovingAverageRebalanceStrategy(BaseStrategy):
    """
    이동평균선 기반 다중 자산 리밸런싱 전략
    
    로직:
    - n일선 위: stock_ticker1과 stock_ticker2를 목표 비율로 유지 (밴딩 리밸런싱)
    - n일선 아래: bond_ticker 보유
    """
    
    def __init__(self, name: str = "MovingAverageRebalance", params: Optional[Dict] = None):
        """
        초기화
        
        Args:
            name: 전략 이름
            params: 전략 파라미터
                - base_ticker: 이동평균선 계산 기준 종목 (기본: 첫 번째 stock_ticker)
                - stock_ticker1: 주식 종목 1 (기본: "QQQM")
                - stock_ticker2: 주식 종목 2 (기본: "TQQQ")
                - bond_ticker: 채권 종목 (n일선 아래 시, 기본: "BIL")
                - ma_period: 이동평균 기간 (기본: 200)
                - stock1_pct: stock_ticker1 목표 비율 (기본: 0.5 = 50%)
                - stock2_pct: stock_ticker2 목표 비율 (기본: 0.5 = 50%, stock1_pct와 합쳐서 1.0이 되어야 함)
                - band_threshold: 밴딩 임계값 (기본: 0.05 = 5%)
        """
        super().__init__(name, params or {})
        self.base_ticker = self.params.get("base_ticker", None)  # 이동평균선 계산 기준 종목
        self.stock_ticker1 = self.params.get("stock_ticker1", "QQQM")  # 주식 종목 1
        self.stock_ticker2 = self.params.get("stock_ticker2", "TQQQ")  # 주식 종목 2
        self.bond_ticker = self.params.get("bond_ticker", "BIL")  # 채권 종목
        self.ma_period = self.params.get("ma_period", 200)
        self.stock1_pct = self.params.get("stock1_pct", 0.5)  # stock_ticker1 목표 비율
        self.stock2_pct = self.params.get("stock2_pct", 0.5)  # stock_ticker2 목표 비율
        self.band_threshold = self.params.get("band_threshold", 0.05)  # 밴딩 임계값 (5%)
        self.current_mode = None  # "above" (n일선 위) 또는 "below" (n일선 아래)
        
        # base_ticker가 설정되지 않으면 stock_ticker1 사용
        if self.base_ticker is None:
            self.base_ticker = self.stock_ticker1
        
        # 백테스팅 엔진 호환성
        self.stock_ticker = self.base_ticker
        
        # 비율 검증
        total_pct = self.stock1_pct + self.stock2_pct
        if abs(total_pct - 1.0) > 0.01:
            logger.warning(f"목표 비율의 합이 1.0이 아닙니다: {total_pct} (자동 조정)")
            # 자동 조정
            self.stock1_pct = self.stock1_pct / total_pct
            self.stock2_pct = self.stock2_pct / total_pct
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        거래 신호 생성
        
        기준 종목의 데이터를 기준으로:
        1. n일 이동평균선 계산
        2. n일선 위/아래 판단
        3. 신호 생성:
           - n일선 위: stock_ticker1과 stock_ticker2 리밸런싱 모드 (Signal=3)
           - n일선 아래: bond_ticker 보유 (Signal=1)
        
        Args:
            data: OHLCV 데이터프레임 (기준 종목 데이터)
        
        Returns:
            신호가 추가된 데이터프레임
            - Signal = 1: n일선 아래로 전환 (BIL로 전환)
            - Signal = 3: n일선 위 모드 유지 (리밸런싱 체크)
            - TargetTicker: 목표 종목 ("ABOVE" 또는 bond_ticker)
        """
        if not self.validate_data(data):
            raise ValueError("데이터 유효성 검증 실패")
        
        df = data.copy()
        df["Signal"] = 0
        df["TargetTicker"] = None
        
        # 이동평균선 계산
        ma_column = f"MA{self.ma_period}"
        df[ma_column] = df["Close"].rolling(window=self.ma_period, min_periods=1).mean()
        
        # 첫날 처리
        first_close = df.iloc[0]["Close"]
        first_ma = df.iloc[0][ma_column]
        
        if first_close >= first_ma:
            # n일선 위: 리밸런싱 모드
            df.iloc[0, df.columns.get_loc("Signal")] = 3
            df.iloc[0, df.columns.get_loc("TargetTicker")] = "ABOVE"
            self.current_mode = "above"
        else:
            # n일선 아래: 채권 보유
            df.iloc[0, df.columns.get_loc("Signal")] = 1
            df.iloc[0, df.columns.get_loc("TargetTicker")] = self.bond_ticker
            self.current_mode = "below"
        
        # 나머지 날짜 처리
        for idx in range(1, len(df)):
            curr_close = df.iloc[idx]["Close"]
            curr_ma = df.iloc[idx][ma_column]
            prev_close = df.iloc[idx - 1]["Close"]
            prev_ma = df.iloc[idx - 1][ma_column]
            
            # n일선 위치 변화 감지
            prev_below_ma = prev_close < prev_ma
            curr_above_ma = curr_close >= curr_ma
            prev_above_ma = prev_close >= prev_ma
            curr_below_ma = curr_close < curr_ma
            
            # 전환 신호 생성
            if prev_below_ma and curr_above_ma:
                # n일선 아래 → 위로 전환: 리밸런싱 모드
                df.iloc[idx, df.columns.get_loc("Signal")] = 3
                df.iloc[idx, df.columns.get_loc("TargetTicker")] = "ABOVE"
                self.current_mode = "above"
            elif prev_above_ma and curr_below_ma:
                # n일선 위 → 아래로 전환: 채권으로 전환
                df.iloc[idx, df.columns.get_loc("Signal")] = 1
                df.iloc[idx, df.columns.get_loc("TargetTicker")] = self.bond_ticker
                self.current_mode = "below"
            elif curr_above_ma:
                # n일선 위 유지: 리밸런싱 체크 (Signal=3)
                df.iloc[idx, df.columns.get_loc("Signal")] = 3
                df.iloc[idx, df.columns.get_loc("TargetTicker")] = "ABOVE"
                self.current_mode = "above"
            else:
                # n일선 아래 유지: 보유
                df.iloc[idx, df.columns.get_loc("Signal")] = 0
                df.iloc[idx, df.columns.get_loc("TargetTicker")] = self.bond_ticker
                self.current_mode = "below"
        
        signal_count = (df["Signal"] == 1).sum()  # 전환 신호
        rebalance_signals = (df["Signal"] == 3).sum()  # 리밸런싱 체크 신호
        
        logger.info(
            f"MA Rebalance 전략 신호 생성 완료: {len(df)}개 일봉, "
            f"전환 신호 {signal_count}회, 리밸런싱 체크 {rebalance_signals}회 "
            f"(MA={self.ma_period}일)"
        )
        
        return df
    
    def check_banding_rebalance(
        self,
        portfolio_value: float,
        current_stock1_value: float,
        current_stock2_value: float,
        stock1_price: float,
        stock2_price: float,
        stock1_quantity: int,
        stock2_quantity: int
    ) -> tuple[bool, Optional[str]]:
        """
        밴딩 리밸런싱 필요 여부 체크 (n일선 위 모드)
        
        Args:
            portfolio_value: 전체 포트폴리오 가치
            current_stock1_value: stock_ticker1 현재 가치
            current_stock2_value: stock_ticker2 현재 가치
            stock1_price: stock_ticker1 현재가
            stock2_price: stock_ticker2 현재가
            stock1_quantity: stock_ticker1 보유 수량
            stock2_quantity: stock_ticker2 보유 수량
        
        Returns:
            (리밸런싱 필요 여부, 리밸런싱이 필요한 티커)
        """
        if portfolio_value == 0:
            return False, None
        
        # 현재 비율 계산
        current_stock1_pct = current_stock1_value / portfolio_value if portfolio_value > 0 else 0
        current_stock2_pct = current_stock2_value / portfolio_value if portfolio_value > 0 else 0
        
        # 목표 비율과의 차이
        diff1 = abs(current_stock1_pct - self.stock1_pct)
        diff2 = abs(current_stock2_pct - self.stock2_pct)
        
        # 임계값을 넘으면 리밸런싱 필요
        if diff1 >= self.band_threshold or diff2 >= self.band_threshold:
            # 더 많이 벗어난 종목을 우선 리밸런싱
            if diff1 >= diff2:
                return True, self.stock_ticker1
            else:
                return True, self.stock_ticker2
        
        return False, None
    
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
            portfolio_value: 포트폴리오 가치
            price: 현재가
            signal: 신호 (1=전환, 3=리밸런싱 체크, 0=보유)
            **kwargs: 추가 파라미터
                - ticker: 현재 거래하는 종목
                - current_quantity: 현재 보유 수량
                - commission_rate: 수수료율
                - current_stock1_value: stock_ticker1 현재 가치
                - current_stock2_value: stock_ticker2 현재 가치
                - current_bond_value: bond_ticker 현재 가치
        
        Returns:
            거래 수량 (양수=매수, 음수=매도, 0=보유)
        """
        if signal == 0:
            return 0
        
        # 가격이 0이거나 유효하지 않으면 거래 불가
        if price <= 0 or pd.isna(price):
            return 0
        
        ticker = kwargs.get("ticker", None)
        current_quantity = kwargs.get("current_quantity", 0)
        commission_rate = kwargs.get("commission_rate", 0.001)
        current_stock1_value = kwargs.get("current_stock1_value", 0.0)
        current_stock2_value = kwargs.get("current_stock2_value", 0.0)
        current_bond_value = kwargs.get("current_bond_value", 0.0)
        
        if ticker is None or self.current_mode is None:
            return 0
        
        if signal == 1:
            # n일선 아래로 전환: bond_ticker로 전환
            if ticker == self.bond_ticker:
                # BIL 100% 매수
                target_value = portfolio_value * (1 - commission_rate)
                target_quantity = int(target_value / price) if price > 0 else 0
                quantity_diff = target_quantity - current_quantity
                return quantity_diff
            else:
                # 다른 종목 전량 매도
                if current_quantity > 0:
                    return -current_quantity
        
        elif signal == 3:
            # n일선 위 모드: 리밸런싱 체크
            if ticker == self.stock_ticker1:
                # stock_ticker1 목표 비율로 조정
                target_value = portfolio_value * self.stock1_pct * (1 - commission_rate)
                target_quantity = int(target_value / price) if price > 0 else 0
                quantity_diff = target_quantity - current_quantity
                return quantity_diff
            elif ticker == self.stock_ticker2:
                # stock_ticker2 목표 비율로 조정
                target_value = portfolio_value * self.stock2_pct * (1 - commission_rate)
                target_quantity = int(target_value / price) if price > 0 else 0
                quantity_diff = target_quantity - current_quantity
                return quantity_diff
            else:
                # 다른 종목 전량 매도
                if current_quantity > 0:
                    return -current_quantity
        
        return 0

