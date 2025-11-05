"""
다중 종목 백테스팅 엔진
두 종목 이상을 동시에 거래하는 전략용 (예: TQQQ + TMF)
"""

from datetime import datetime
from typing import Optional, Dict, List
import pandas as pd
import numpy as np
from loguru import logger

from src.backtest.portfolio import Portfolio
from src.strategy.base import BaseStrategy
from src.config.settings import get_settings
from src.utils.metrics import calculate_all_metrics


class MultiAssetBacktestEngine:
    """다중 종목 백테스팅 엔진"""

    def __init__(
        self,
        tickers: List[str],
        initial_cash: Optional[float] = None,
        commission_rate: Optional[float] = None,
        monthly_addition: Optional[float] = None
    ):
        """
        초기화
        
        Args:
            tickers: 거래할 종목 리스트 (예: ["TQQQ", "TMF"])
            initial_cash: 초기 자본금
            commission_rate: 수수료율
            monthly_addition: 매월 추가 투자금
        """
        settings = get_settings()
        
        self.tickers = tickers
        self.initial_cash = initial_cash or settings.DEFAULT_INITIAL_CASH
        self.commission_rate = commission_rate or settings.DEFAULT_COMMISSION
        self.monthly_addition = monthly_addition or 0
        
        self.portfolio = Portfolio(
            initial_cash=self.initial_cash,
            commission_rate=self.commission_rate
        )
        
        self.strategy: Optional[BaseStrategy] = None
        self.results: pd.DataFrame = pd.DataFrame()
        self.data_dict: Dict[str, pd.DataFrame] = {}
        self.last_month = None  # 매월 추가 투자 추적
        
        # 통계 추적 (현금 버전 분석용)
        self.stock_pct_history: List[float] = []  # TQQQ 비율 기록
        self.below_ma_stock_pct: List[float] = []  # 200일선 아래에서의 TQQQ 비율
        self.above_ma_stock_pct: List[float] = []  # 200일선 위에서의 TQQQ 비율
        self.below_ma_days = 0  # 200일선 아래 일수
        self.above_ma_days = 0  # 200일선 위 일수
        self.total_days = 0  # 전체 일수

    def set_strategy(self, strategy: BaseStrategy):
        """전략 설정"""
        self.strategy = strategy
        logger.info(f"전략 설정: {strategy.name}")

    def set_data(self, data_dict: Dict[str, pd.DataFrame]):
        """
        종목별 데이터 설정
        
        Args:
            data_dict: {ticker: DataFrame} 형식의 딕셔너리
        """
        self.data_dict = {}
        # 타임존 제거하여 통일
        for ticker, df in data_dict.items():
            df_copy = df.copy()
            # 인덱스 타임존 제거
            if isinstance(df_copy.index, pd.DatetimeIndex) and df_copy.index.tz is not None:
                df_copy.index = df_copy.index.tz_localize(None)
            self.data_dict[ticker] = df_copy
            logger.info(f"{ticker} 데이터 설정: {len(df_copy)}개 일봉")

    def run(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        백테스팅 실행
        
        Args:
            start_date: 시작일
            end_date: 종료일
        
        Returns:
            백테스팅 결과 데이터프레임
        """
        if self.strategy is None:
            raise ValueError("전략이 설정되지 않았습니다")
        
        if not self.data_dict:
            raise ValueError("데이터가 설정되지 않았습니다")
        
        # 모든 종목의 날짜를 통합 (타임존 통일)
        all_dates = set()
        for df in self.data_dict.values():
            dates = df.index
            # DatetimeIndex의 타임존 제거
            if isinstance(dates, pd.DatetimeIndex) and dates.tz is not None:
                dates = dates.tz_localize(None)
            all_dates.update(dates)
        
        # 개별 타임스탬프의 타임존 제거 (혹시 남아있는 경우 대비)
        normalized_dates = []
        for d in all_dates:
            if isinstance(d, pd.Timestamp) and d.tz is not None:
                normalized_dates.append(d.tz_localize(None))
            else:
                normalized_dates.append(d)
        
        all_dates = sorted(set(normalized_dates))
        
        # 날짜 필터링
        if start_date:
            start_ts = pd.Timestamp(start_date)
            if start_ts.tz is not None:
                start_ts = start_ts.tz_localize(None)
            all_dates = [d for d in all_dates if d >= start_ts]
        if end_date:
            end_ts = pd.Timestamp(end_date)
            if end_ts.tz is not None:
                end_ts = end_ts.tz_localize(None)
            all_dates = [d for d in all_dates if d <= end_ts]
        
        logger.info(f"백테스팅 시작: {len(all_dates)}개 거래일")
        
        # 전략 초기화
        self.strategy.reset()
        
        # 전략에 종목 정보 전달 (Shannon 전략 등에서 사용)
        if hasattr(self.strategy, 'stock_ticker') and self.strategy.stock_ticker is None:
            # 첫 번째 종목을 주식으로 설정
            if len(self.tickers) >= 1:
                self.strategy.stock_ticker = self.tickers[0]
        if hasattr(self.strategy, 'bond_ticker') and len(self.tickers) >= 2:
            # 두 번째 종목을 채권으로 설정
            if self.strategy.bond_ticker is None and self.strategy.use_bond:
                self.strategy.bond_ticker = self.tickers[1]
        
        # 백테스팅 실행
        for date in all_dates:
            # 매월 추가 투자 처리
            if self.monthly_addition > 0:
                # Period 변환 시 타임존 정보 손실 경고 회피
                if isinstance(date, pd.Timestamp):
                    current_month = date.strftime('%Y-%m')
                else:
                    current_month = date.strftime('%Y-%m')
                if self.last_month != current_month:
                    self.portfolio.cash += self.monthly_addition
                    self.last_month = current_month
                    logger.debug(f"매월 추가 투자: ${self.monthly_addition:,.2f} (날짜: {date.date()})")
            
            # 모든 종목의 현재가 업데이트 및 배당금 처리
            prices = {}
            for ticker in self.tickers:
                if ticker in self.data_dict:
                    df = self.data_dict[ticker]
                    if date in df.index:
                        price = df.loc[date, "Close"]
                        prices[ticker] = price
                        
                        # 포트폴리오 가격 업데이트
                        if ticker in self.portfolio.positions:
                            self.portfolio.update_price(ticker, price)
                            
                            # 배당금 처리
                            if "Dividends" in df.columns:
                                dividend = df.loc[date, "Dividends"]
                                if pd.notna(dividend) and dividend > 0:
                                    self.portfolio.receive_dividend(ticker, dividend, date)
            
            # MovingAverage 전략 특별 처리: 주식 종목 신호 발생 시 모든 종목 처리
            processed_tickers = set()
            
            # MovingAverage/MovingAverageBreakout 전략의 경우: 기준 종목에서 신호나 목표 종목 정보 확인
            if hasattr(self.strategy, 'stock_ticker') or hasattr(self.strategy, 'base_ticker'):
                # MovingAverageBreakout은 base_ticker 사용, MovingAverage는 stock_ticker 사용
                if hasattr(self.strategy, 'base_ticker'):
                    stock_ticker = self.strategy.base_ticker
                else:
                    stock_ticker = self.strategy.stock_ticker
                # prices에 없으면 data_dict에서 직접 가격 가져오기
                if stock_ticker not in prices and stock_ticker in self.data_dict:
                    if date in self.data_dict[stock_ticker].index:
                        prices[stock_ticker] = self.data_dict[stock_ticker].loc[date, "Close"]
                
                if stock_ticker in prices and stock_ticker in self.data_dict and date in self.data_dict[stock_ticker].index:
                    stock_df = self.data_dict[stock_ticker]
                    
                    # Signal과 TargetTicker, Mode 직접 접근
                    if "Signal" in stock_df.columns and date in stock_df.index:
                        stock_signal = stock_df.loc[date, "Signal"]
                    else:
                        stock_signal = 0
                    
                    if "TargetTicker" in stock_df.columns and date in stock_df.index:
                        target_ticker = stock_df.loc[date, "TargetTicker"]
                        # NaN 값 처리
                        if pd.isna(target_ticker):
                            target_ticker = None
                    else:
                        target_ticker = None
                    
                    if "Mode" in stock_df.columns and date in stock_df.index:
                        current_mode = stock_df.loc[date, "Mode"]
                        if pd.isna(current_mode):
                            current_mode = None
                    else:
                        current_mode = None
                    
                    # 신호가 있는 경우에만 거래 처리 (신호 없이는 보유 유지)
                    if stock_signal != 0:
                        if target_ticker is None or pd.isna(target_ticker):
                            # TargetTicker가 없으면 current_holding 사용 (하위 호환)
                            target_ticker = getattr(self.strategy, 'current_holding', None)
                        
                        # Shannon/DailyShannon 전략: stock_ticker와 (bond_ticker 또는 현금)을 가진 전략
                        # 현금 버전(bond_ticker=None)도 처리
                        if hasattr(self.strategy, 'stock_ticker') and hasattr(self.strategy, 'use_bond') and not hasattr(self.strategy, 'stock_ticker1'):
                            # DailyShannon 여부 확인
                            is_daily_shannon = hasattr(self.strategy, '__class__') and 'DailyShannon' in self.strategy.__class__.__name__
                            
                            # DailyShannon은 Signal=3일 때 무조건 리밸런싱, Shannon은 Signal=3일 때 밴딩 체크
                            should_rebalance = False
                            if is_daily_shannon:
                                # DailyShannon: Signal=1 또는 Signal=3일 때 리밸런싱
                                should_rebalance = stock_signal in [1, 3]
                            else:
                                # Shannon: Signal=1 또는 Signal=3일 때 리밸런싱 (밴딩 체크는 calculate_position_size에서)
                                should_rebalance = stock_signal in [1, 3]
                            
                            if should_rebalance:
                                portfolio_value = self.portfolio.total_value
                                
                                # stock_ticker와 bond_ticker(또는 현금)의 현재 가치 계산
                                stock_value = 0.0
                                bond_value = 0.0
                                stock_quantity = 0
                                bond_quantity = 0
                                stock_price = 0.0
                                bond_price = 0.0
                                
                                # 가격 먼저 읽기
                                if self.strategy.stock_ticker in prices:
                                    stock_price = prices[self.strategy.stock_ticker]
                                if self.strategy.use_bond and self.strategy.bond_ticker and self.strategy.bond_ticker in prices:
                                    bond_price = prices[self.strategy.bond_ticker]
                                
                                if self.strategy.stock_ticker in self.portfolio.positions:
                                    pos = self.portfolio.get_position(self.strategy.stock_ticker)
                                    stock_quantity = pos.quantity
                                    stock_value = stock_quantity * stock_price
                                
                                if self.strategy.use_bond and self.strategy.bond_ticker:
                                    if self.strategy.bond_ticker in self.portfolio.positions:
                                        pos = self.portfolio.get_position(self.strategy.bond_ticker)
                                        bond_quantity = pos.quantity
                                        bond_value = bond_quantity * bond_price
                                else:
                                    # 현금 버전: bond_value는 현금으로 계산
                                    bond_value = self.portfolio.cash
                                
                                # 초기 진입: stock과 bond가 모두 없으면 초기 매수
                                if stock_quantity == 0 and bond_quantity == 0:
                                    # stock 초기 매수
                                    if self.strategy.stock_ticker in prices and stock_price > 0:
                                        stock_target_quantity = self.strategy.calculate_position_size(
                                            portfolio_value=portfolio_value,
                                            price=stock_price,
                                            signal=stock_signal if stock_signal != 0 else 1,
                                            current_quantity=0,
                                            cash=self.portfolio.cash,
                                            current_bond_value=0.0,
                                            commission_rate=self.commission_rate,
                                            ticker=self.strategy.stock_ticker,
                                            mode=current_mode if current_mode else (getattr(self.strategy, 'current_mode', None))
                                        )
                                        if stock_target_quantity > 0:
                                            try:
                                                self.portfolio.buy(self.strategy.stock_ticker, stock_target_quantity, stock_price, date)
                                                processed_tickers.add(self.strategy.stock_ticker)
                                            except Exception as e:
                                                logger.error(f"초기 매수 실패 [{self.strategy.stock_ticker}] {e}")
                                    
                                    # bond 초기 매수 (stock 매수 후 포트폴리오 가치 재계산)
                                    # 현금 버전은 bond_ticker가 없으므로 건너뜀
                                    portfolio_value = self.portfolio.total_value
                                    
                                    if self.strategy.use_bond and self.strategy.bond_ticker and self.strategy.bond_ticker in prices and bond_price > 0:
                                        bond_target_quantity = self.strategy.calculate_position_size(
                                            portfolio_value=portfolio_value,
                                            price=bond_price,
                                            signal=stock_signal if stock_signal != 0 else 1,
                                            current_quantity=0,
                                            cash=self.portfolio.cash,
                                            current_stock_value=stock_value if stock_price > 0 else 0.0,
                                            current_bond_value=0.0,
                                            commission_rate=self.commission_rate,
                                            ticker=self.strategy.bond_ticker,
                                            mode=current_mode if current_mode else (getattr(self.strategy, 'current_mode', None))
                                        )
                                        if bond_target_quantity > 0:
                                            try:
                                                self.portfolio.buy(self.strategy.bond_ticker, bond_target_quantity, bond_price, date)
                                                processed_tickers.add(self.strategy.bond_ticker)
                                            except Exception as e:
                                                logger.error(f"초기 매수 실패 [{self.strategy.bond_ticker}] {e}")
                                else:
                                    # 매일 리밸런싱: stock_ticker만 처리 (현금 버전) 또는 두 종목 모두 처리 (bond 버전)
                                    tickers_to_process = [self.strategy.stock_ticker]
                                    if self.strategy.use_bond and self.strategy.bond_ticker:
                                        tickers_to_process.append(self.strategy.bond_ticker)
                                    
                                    # 현금 버전: TQQQ 비율 추적 로그 및 통계 수집
                                    if not self.strategy.use_bond and stock_signal == 3:
                                        current_stock_pct = stock_value / portfolio_value if portfolio_value > 0 else 0
                                        current_cash_pct = self.portfolio.cash / portfolio_value if portfolio_value > 0 else 0
                                        
                                        # 통계 수집
                                        self.stock_pct_history.append(current_stock_pct)
                                        if current_mode == "BELOW":
                                            self.below_ma_days += 1
                                            self.below_ma_stock_pct.append(current_stock_pct)
                                        elif current_mode == "ABOVE":
                                            self.above_ma_days += 1
                                            self.above_ma_stock_pct.append(current_stock_pct)
                                        self.total_days += 1
                                        
                                        logger.debug(
                                            f"[현금버전 TQQQ비율 추적] {date.strftime('%Y-%m-%d')} "
                                            f"Signal={stock_signal} Mode={current_mode} "
                                            f"TQQQ={current_stock_pct:.2%} 현금={current_cash_pct:.2%} "
                                            f"portfolio=${portfolio_value:.2f} TQQQ가치=${stock_value:.2f} 현금=${self.portfolio.cash:.2f}"
                                        )
                                        if current_stock_pct > 0.55:
                                            logger.warning(
                                                f"⚠️ [현금버전] {date.strftime('%Y-%m-%d')} TQQQ 비율 초과: "
                                                f"{current_stock_pct:.2%} > 50%"
                                            )
                                    
                                    # 매도 먼저, 매수 나중 순서로 처리
                                    sell_orders = []
                                    buy_orders = []
                                    
                                    for ticker in tickers_to_process:
                                        if ticker not in prices or ticker in processed_tickers:
                                            continue
                                        
                                        portfolio_value = self.portfolio.total_value
                                        ticker_price = prices[ticker]
                                        ticker_current_quantity = 0
                                        if self.portfolio.get_position(ticker):
                                            ticker_current_quantity = self.portfolio.get_position(ticker).quantity
                                        
                                        # 다른 종목 가치 계산
                                        if ticker == self.strategy.stock_ticker:
                                            # TQQQ 처리 시: bond_ticker 또는 현금 가치
                                            other_value = bond_value if self.strategy.use_bond else self.portfolio.cash
                                        else:
                                            # bond_ticker 처리 시: TQQQ 가치
                                            other_value = stock_value
                                        
                                        # 현금 버전과 bond 버전 모두 current_bond_value 전달
                                        # 현금 버전: bond_value = portfolio.cash
                                        # bond 버전: bond_value = bond_ticker 가치
                                        current_bond_val = bond_value if self.strategy.use_bond else self.portfolio.cash
                                        
                                        # 현금 버전: calculate_position_size 호출 전 로그
                                        if not self.strategy.use_bond and ticker == self.strategy.stock_ticker and stock_signal == 3:
                                            current_ticker_value = ticker_current_quantity * ticker_price
                                            current_ticker_pct = current_ticker_value / portfolio_value if portfolio_value > 0 else 0
                                            logger.debug(
                                                f"[현금버전 계산전] {date.strftime('%Y-%m-%d')} {ticker} "
                                                f"가치=${current_ticker_value:.2f} 비율={current_ticker_pct:.2%} "
                                                f"수량={ticker_current_quantity} 가격=${ticker_price:.2f}"
                                            )
                                        
                                        quantity = self.strategy.calculate_position_size(
                                            portfolio_value=portfolio_value,
                                            price=ticker_price,
                                            signal=stock_signal,
                                            current_quantity=ticker_current_quantity,
                                            cash=self.portfolio.cash,
                                            current_bond_value=current_bond_val,
                                            current_stock_value=stock_value,
                                            commission_rate=self.commission_rate,
                                            ticker=ticker,
                                            mode=current_mode if current_mode else (getattr(self.strategy, 'current_mode', None))
                                        )
                                        
                                        # 현금 버전: calculate_position_size 결과 로그
                                        if not self.strategy.use_bond and ticker == self.strategy.stock_ticker and stock_signal == 3:
                                            logger.debug(
                                                f"[현금버전 계산후] {date.strftime('%Y-%m-%d')} {ticker} "
                                                f"quantity={quantity} "
                                                f"(양수=매수, 음수=매도, 0=보유)"
                                            )
                                        
                                        if quantity > 0:
                                            buy_orders.append((ticker, quantity, ticker_price))
                                        elif quantity < 0:
                                            sell_orders.append((ticker, abs(quantity), ticker_price))
                                        
                                        processed_tickers.add(ticker)
                                    
                                    # 먼저 모든 매도 실행
                                    for ticker, qty, price in sell_orders:
                                        try:
                                            self.portfolio.sell(ticker, qty, price, date)
                                            if not self.strategy.use_bond:
                                                logger.debug(f"[현금버전 매도] {date.strftime('%Y-%m-%d')} {ticker} {qty}주 @ ${price:.2f}")
                                        except Exception as e:
                                            logger.warning(f"리밸런싱 매도 실패 [{ticker}] {e}")
                                    
                                    # 매도 후 포트폴리오 가치 재계산
                                    portfolio_value = self.portfolio.total_value
                                    
                                    # 그 다음 모든 매수 실행
                                    for ticker, qty, price in buy_orders:
                                        try:
                                            self.portfolio.buy(ticker, qty, price, date)
                                            if not self.strategy.use_bond:
                                                logger.debug(f"[현금버전 매수] {date.strftime('%Y-%m-%d')} {ticker} {qty}주 @ ${price:.2f}")
                                        except Exception as e:
                                            logger.warning(f"리밸런싱 매수 실패 [{ticker}] {e}")
                                    
                                    # 현금 버전: 거래 후 최종 비율 로그
                                    if not self.strategy.use_bond and stock_signal == 3:
                                        final_portfolio_value = self.portfolio.total_value
                                        final_stock_value = 0.0
                                        if self.strategy.stock_ticker in self.portfolio.positions:
                                            pos = self.portfolio.get_position(self.strategy.stock_ticker)
                                            if self.strategy.stock_ticker in prices:
                                                final_stock_value = pos.quantity * prices[self.strategy.stock_ticker]
                                        final_stock_pct = final_stock_value / final_portfolio_value if final_portfolio_value > 0 else 0
                                        final_cash_pct = self.portfolio.cash / final_portfolio_value if final_portfolio_value > 0 else 0
                                        logger.debug(
                                            f"[현금버전 거래후] {date.strftime('%Y-%m-%d')} "
                                            f"최종 TQQQ={final_stock_pct:.2%} 현금={final_cash_pct:.2%}"
                                        )
                                        if final_stock_pct > 0.55:
                                            logger.warning(
                                                f"⚠️⚠️ [현금버전 거래후] {date.strftime('%Y-%m-%d')} "
                                                f"TQQQ 비율 여전히 초과: {final_stock_pct:.2%} > 50%"
                                            )
                        
                        # InverseMA 전략: Signal=1일 때 BELOW 모드 전환 (TQQQ 100%)
                        elif hasattr(self.strategy, 'qqq_ticker') and hasattr(self.strategy, 'tqqq_ticker') and stock_signal == 1:
                            # BELOW 모드: TQQQ 100% 보유 (QQQ 전고점 회복까지 매도 금지)
                            portfolio_value = self.portfolio.total_value
                            
                            # QQQ 가격 확인 (전고점 회복 체크용)
                            qqq_price = 0.0
                            if self.strategy.qqq_ticker in prices:
                                qqq_price = prices[self.strategy.qqq_ticker]
                            
                            # QQQ와 다른 종목 매도
                            for ticker in self.tickers:
                                if ticker == self.strategy.tqqq_ticker:
                                    continue
                                if ticker not in prices or ticker in processed_tickers:
                                    continue
                                if self.portfolio.get_position(ticker):
                                    pos = self.portfolio.get_position(ticker)
                                    if pos.quantity > 0:
                                        try:
                                            self.portfolio.sell(ticker, pos.quantity, prices[ticker], date)
                                            processed_tickers.add(ticker)
                                        except Exception as e:
                                            logger.warning(f"매도 실패 [{ticker}] {e}")
                            
                            # TQQQ 100% 매수
                            portfolio_value = self.portfolio.total_value
                            if self.strategy.tqqq_ticker in prices:
                                tqqq_price = prices[self.strategy.tqqq_ticker]
                                if tqqq_price > 0:
                                    tqqq_quantity = 0
                                    if self.portfolio.get_position(self.strategy.tqqq_ticker):
                                        tqqq_quantity = self.portfolio.get_position(self.strategy.tqqq_ticker).quantity
                                    
                                    quantity = self.strategy.calculate_position_size(
                                        portfolio_value=portfolio_value,
                                        price=tqqq_price,
                                        signal=1,
                                        current_quantity=tqqq_quantity,
                                        cash=self.portfolio.cash,
                                        commission_rate=self.commission_rate,
                                        ticker=self.strategy.tqqq_ticker,
                                        mode="BELOW",
                                        qqq_price=qqq_price
                                    )
                                    
                                    if quantity > 0:
                                        try:
                                            self.portfolio.buy(self.strategy.tqqq_ticker, quantity, tqqq_price, date)
                                            processed_tickers.add(self.strategy.tqqq_ticker)
                                        except Exception as e:
                                            logger.warning(f"TQQQ 매수 실패: {e}")
                        
                        # QQQTQQQIDMA 전략: Signal=1일 때 모드 전환 (TQQQ 또는 QID 100%)
                        elif (hasattr(self.strategy, 'tqqq_ticker') and hasattr(self.strategy, 'qid_ticker') and 
                              not hasattr(self.strategy, 'sgov_ticker') and stock_signal == 1):
                            # QQQTQQQIDMA 전략: 200일선 위는 TQQQ, 아래는 QID
                            portfolio_value = self.portfolio.total_value
                            
                            # 다른 종목 매도 (TQQQ, QID 제외)
                            for ticker in self.tickers:
                                if ticker in [self.strategy.tqqq_ticker, self.strategy.qid_ticker]:
                                    continue
                                if ticker not in prices or ticker in processed_tickers:
                                    continue
                                if self.portfolio.get_position(ticker):
                                    pos = self.portfolio.get_position(ticker)
                                    if pos.quantity > 0:
                                        try:
                                            self.portfolio.sell(ticker, pos.quantity, prices[ticker], date)
                                            processed_tickers.add(ticker)
                                        except Exception as e:
                                            logger.warning(f"매도 실패 [{ticker}] {e}")
                            
                            # 현재 모드에 따라 목표 종목 결정
                            if current_mode == "ABOVE":
                                # TQQQ 100% 보유
                                target_ticker = self.strategy.tqqq_ticker
                                other_ticker = self.strategy.qid_ticker
                            else:
                                # QID 100% 보유
                                target_ticker = self.strategy.qid_ticker
                                other_ticker = self.strategy.tqqq_ticker
                            
                            # 다른 종목 매도
                            if other_ticker in prices and other_ticker not in processed_tickers:
                                if self.portfolio.get_position(other_ticker):
                                    pos = self.portfolio.get_position(other_ticker)
                                    if pos.quantity > 0:
                                        try:
                                            self.portfolio.sell(other_ticker, pos.quantity, prices[other_ticker], date)
                                            processed_tickers.add(other_ticker)
                                        except Exception as e:
                                            logger.warning(f"매도 실패 [{other_ticker}] {e}")
                            
                            # 목표 종목 100% 매수
                            portfolio_value = self.portfolio.total_value
                            if target_ticker in prices and target_ticker not in processed_tickers:
                                target_price = prices[target_ticker]
                                if target_price > 0:
                                    target_quantity = 0
                                    if self.portfolio.get_position(target_ticker):
                                        target_quantity = self.portfolio.get_position(target_ticker).quantity
                                    
                                    quantity = self.strategy.calculate_position_size(
                                        portfolio_value=portfolio_value,
                                        price=target_price,
                                        signal=1,
                                        current_quantity=target_quantity,
                                        cash=self.portfolio.cash,
                                        commission_rate=self.commission_rate,
                                        ticker=target_ticker
                                    )
                                    
                                    if quantity > 0:
                                        try:
                                            self.portfolio.buy(target_ticker, quantity, target_price, date)
                                            processed_tickers.add(target_ticker)
                                        except Exception as e:
                                            logger.warning(f"{target_ticker} 매수 실패: {e}")
                        
                        # QQQQIDSGOVMA 전략: Signal=1일 때 ABOVE 모드 전환 (TQQQ 100%)
                        elif (hasattr(self.strategy, 'tqqq_ticker') and hasattr(self.strategy, 'qid_ticker') and 
                              hasattr(self.strategy, 'sgov_ticker') and stock_signal == 1 and current_mode == "ABOVE"):
                            # 초기 QID 가치 리셋
                            if hasattr(self.strategy, 'initial_qid_value'):
                                self.strategy.initial_qid_value = None
                            portfolio_value = self.portfolio.total_value
                            
                            # QID, SGOV, TQQQ 외 종목 매도
                            for ticker in self.tickers:
                                if ticker in [self.strategy.tqqq_ticker, self.strategy.qid_ticker, self.strategy.sgov_ticker]:
                                    continue
                                if ticker not in prices or ticker in processed_tickers:
                                    continue
                                if self.portfolio.get_position(ticker):
                                    pos = self.portfolio.get_position(ticker)
                                    if pos.quantity > 0:
                                        try:
                                            self.portfolio.sell(ticker, pos.quantity, prices[ticker], date)
                                            processed_tickers.add(ticker)
                                        except Exception as e:
                                            logger.warning(f"매도 실패 [{ticker}] {e}")
                            
                            # QID와 SGOV 매도
                            for ticker in [self.strategy.qid_ticker, self.strategy.sgov_ticker]:
                                if ticker not in prices or ticker in processed_tickers:
                                    continue
                                if self.portfolio.get_position(ticker):
                                    pos = self.portfolio.get_position(ticker)
                                    if pos.quantity > 0:
                                        try:
                                            self.portfolio.sell(ticker, pos.quantity, prices[ticker], date)
                                            processed_tickers.add(ticker)
                                        except Exception as e:
                                            logger.warning(f"매도 실패 [{ticker}] {e}")
                            
                            # TQQQ 100% 매수
                            portfolio_value = self.portfolio.total_value
                            if self.strategy.tqqq_ticker in prices:
                                tqqq_price = prices[self.strategy.tqqq_ticker]
                                if tqqq_price > 0:
                                    tqqq_quantity = 0
                                    if self.portfolio.get_position(self.strategy.tqqq_ticker):
                                        tqqq_quantity = self.portfolio.get_position(self.strategy.tqqq_ticker).quantity
                                    
                                    quantity = self.strategy.calculate_position_size(
                                        portfolio_value=portfolio_value,
                                        price=tqqq_price,
                                        signal=1,
                                        current_quantity=tqqq_quantity,
                                        cash=self.portfolio.cash,
                                        commission_rate=self.commission_rate,
                                        ticker=self.strategy.tqqq_ticker,
                                        mode="ABOVE"
                                    )
                                    
                                    if quantity > 0:
                                        try:
                                            self.portfolio.buy(self.strategy.tqqq_ticker, quantity, tqqq_price, date)
                                            processed_tickers.add(self.strategy.tqqq_ticker)
                                        except Exception as e:
                                            logger.warning(f"TQQQ 매수 실패: {e}")
                        
                        # QQQQIDSGOVMA 전략: Signal=3일 때 BELOW 모드 리밸런싱 (QID 50% + SGOV 50%)
                        elif (hasattr(self.strategy, 'tqqq_ticker') and hasattr(self.strategy, 'qid_ticker') and 
                              hasattr(self.strategy, 'sgov_ticker') and stock_signal == 3 and current_mode == "BELOW"):
                            portfolio_value = self.portfolio.total_value
                            
                            # TQQQ 매도
                            if self.strategy.tqqq_ticker in prices and self.portfolio.get_position(self.strategy.tqqq_ticker):
                                pos = self.portfolio.get_position(self.strategy.tqqq_ticker)
                                if pos.quantity > 0:
                                    try:
                                        self.portfolio.sell(self.strategy.tqqq_ticker, pos.quantity, prices[self.strategy.tqqq_ticker], date)
                                        processed_tickers.add(self.strategy.tqqq_ticker)
                                    except Exception as e:
                                        logger.warning(f"TQQQ 매도 실패: {e}")
                            
                            # QID와 SGOV 현재 가치 계산
                            qid_value = 0.0
                            sgov_value = 0.0
                            qid_quantity = 0
                            sgov_quantity = 0
                            qid_price = 0.0
                            sgov_price = 0.0
                            initial_qid_value = None
                            
                            if self.strategy.qid_ticker in prices:
                                qid_price = prices[self.strategy.qid_ticker]
                            if self.strategy.sgov_ticker in prices:
                                sgov_price = prices[self.strategy.sgov_ticker]
                            
                            if self.strategy.qid_ticker in self.portfolio.positions:
                                pos = self.portfolio.get_position(self.strategy.qid_ticker)
                                qid_quantity = pos.quantity
                                qid_value = qid_quantity * qid_price
                            
                            if self.strategy.sgov_ticker in self.portfolio.positions:
                                pos = self.portfolio.get_position(self.strategy.sgov_ticker)
                                sgov_quantity = pos.quantity
                                sgov_value = sgov_quantity * sgov_price
                            
                            # 초기 QID 가치 가져오기 또는 설정
                            if hasattr(self.strategy, 'initial_qid_value'):
                                initial_qid_value = self.strategy.initial_qid_value
                            
                            # 초기 진입: QID와 SGOV가 모두 없으면 초기 매수
                            if qid_quantity == 0 and sgov_quantity == 0:
                                # QID 초기 매수
                                if self.strategy.qid_ticker in prices and qid_price > 0:
                                    initial_qid_value_param = portfolio_value * getattr(self.strategy, 'qid_pct', 0.5)
                                    qid_target_quantity = self.strategy.calculate_position_size(
                                        portfolio_value=portfolio_value,
                                        price=qid_price,
                                        signal=3,
                                        current_quantity=0,
                                        cash=self.portfolio.cash,
                                        current_qid_value=0.0,
                                        current_sgov_value=0.0,
                                        commission_rate=self.commission_rate,
                                        ticker=self.strategy.qid_ticker,
                                        mode="BELOW",
                                        qid_price=qid_price,
                                        initial_qid_value=initial_qid_value_param
                                    )
                                    if qid_target_quantity > 0:
                                        try:
                                            self.portfolio.buy(self.strategy.qid_ticker, qid_target_quantity, qid_price, date)
                                            processed_tickers.add(self.strategy.qid_ticker)
                                            # 초기 QID 가치 저장
                                            if hasattr(self.strategy, 'initial_qid_value'):
                                                self.strategy.initial_qid_value = initial_qid_value_param
                                        except Exception as e:
                                            logger.warning(f"초기 매수 실패 [{self.strategy.qid_ticker}] {e}")
                                
                                # SGOV 초기 매수 (QID 매수 후 포트폴리오 가치 재계산)
                                portfolio_value = self.portfolio.total_value
                                if self.strategy.qid_ticker in self.portfolio.positions and self.strategy.qid_ticker in prices:
                                    pos = self.portfolio.get_position(self.strategy.qid_ticker)
                                    qid_value = pos.quantity * prices[self.strategy.qid_ticker]
                                
                                if self.strategy.sgov_ticker in prices and sgov_price > 0:
                                    sgov_target_quantity = self.strategy.calculate_position_size(
                                        portfolio_value=portfolio_value,
                                        price=sgov_price,
                                        signal=3,
                                        current_quantity=0,
                                        cash=self.portfolio.cash,
                                        current_qid_value=qid_value,
                                        current_sgov_value=0.0,
                                        commission_rate=self.commission_rate,
                                        ticker=self.strategy.sgov_ticker,
                                        mode="BELOW",
                                        qid_price=qid_price,
                                        initial_qid_value=initial_qid_value
                                    )
                                    if sgov_target_quantity > 0:
                                        try:
                                            self.portfolio.buy(self.strategy.sgov_ticker, sgov_target_quantity, sgov_price, date)
                                            processed_tickers.add(self.strategy.sgov_ticker)
                                        except Exception as e:
                                            logger.warning(f"초기 매수 실패 [{self.strategy.sgov_ticker}] {e}")
                            else:
                                # QID와 SGOV 리밸런싱 처리
                                portfolio_value = self.portfolio.total_value
                                
                                # 가치 재계산
                                if self.strategy.qid_ticker in self.portfolio.positions and self.strategy.qid_ticker in prices:
                                    pos = self.portfolio.get_position(self.strategy.qid_ticker)
                                    qid_value = pos.quantity * prices[self.strategy.qid_ticker]
                                if self.strategy.sgov_ticker in self.portfolio.positions and self.strategy.sgov_ticker in prices:
                                    pos = self.portfolio.get_position(self.strategy.sgov_ticker)
                                    sgov_value = pos.quantity * prices[self.strategy.sgov_ticker]
                                
                                # 초기 QID 가치가 없으면 현재 포트폴리오 가치 기준으로 설정
                                if initial_qid_value is None:
                                    initial_qid_value = portfolio_value * getattr(self.strategy, 'qid_pct', 0.5)
                                    if hasattr(self.strategy, 'initial_qid_value'):
                                        self.strategy.initial_qid_value = initial_qid_value
                                
                                # QID와 SGOV 리밸런싱 처리 (매도 먼저, 매수 나중)
                                sell_orders = []
                                buy_orders = []
                                
                                # QID 처리
                                if self.strategy.qid_ticker in prices and self.strategy.qid_ticker not in processed_tickers:
                                    portfolio_value = self.portfolio.total_value
                                    qid_price = prices[self.strategy.qid_ticker]
                                    qid_quantity = 0
                                    if self.portfolio.get_position(self.strategy.qid_ticker):
                                        qid_quantity = self.portfolio.get_position(self.strategy.qid_ticker).quantity
                                    
                                    # QID 가치 재계산
                                    if self.strategy.qid_ticker in self.portfolio.positions:
                                        pos = self.portfolio.get_position(self.strategy.qid_ticker)
                                        qid_value = pos.quantity * qid_price
                                    
                                    qid_quantity_change = self.strategy.calculate_position_size(
                                        portfolio_value=portfolio_value,
                                        price=qid_price,
                                        signal=3,
                                        current_quantity=qid_quantity,
                                        cash=self.portfolio.cash,
                                        commission_rate=self.commission_rate,
                                        ticker=self.strategy.qid_ticker,
                                        mode="BELOW",
                                        current_qid_value=qid_value,
                                        current_sgov_value=sgov_value,
                                        qid_price=qid_price,
                                        initial_qid_value=initial_qid_value
                                    )
                                    
                                    if qid_quantity_change > 0:
                                        buy_orders.append((self.strategy.qid_ticker, qid_quantity_change, qid_price))
                                    elif qid_quantity_change < 0:
                                        sell_orders.append((self.strategy.qid_ticker, abs(qid_quantity_change), qid_price))
                                    
                                    processed_tickers.add(self.strategy.qid_ticker)
                                
                                # SGOV 처리
                                if self.strategy.sgov_ticker in prices and self.strategy.sgov_ticker not in processed_tickers:
                                    portfolio_value = self.portfolio.total_value
                                    sgov_price = prices[self.strategy.sgov_ticker]
                                    sgov_quantity = 0
                                    if self.portfolio.get_position(self.strategy.sgov_ticker):
                                        sgov_quantity = self.portfolio.get_position(self.strategy.sgov_ticker).quantity
                                    
                                    # SGOV 가치 재계산
                                    if self.strategy.sgov_ticker in self.portfolio.positions:
                                        pos = self.portfolio.get_position(self.strategy.sgov_ticker)
                                        sgov_value = pos.quantity * sgov_price
                                    
                                    # QID 가치 재계산
                                    if self.strategy.qid_ticker in self.portfolio.positions:
                                        pos = self.portfolio.get_position(self.strategy.qid_ticker)
                                        qid_value = pos.quantity * prices[self.strategy.qid_ticker]
                                    
                                    sgov_quantity_change = self.strategy.calculate_position_size(
                                        portfolio_value=portfolio_value,
                                        price=sgov_price,
                                        signal=3,
                                        current_quantity=sgov_quantity,
                                        cash=self.portfolio.cash,
                                        commission_rate=self.commission_rate,
                                        ticker=self.strategy.sgov_ticker,
                                        mode="BELOW",
                                        current_qid_value=qid_value,
                                        current_sgov_value=sgov_value,
                                        qid_price=qid_price,
                                        initial_qid_value=initial_qid_value
                                    )
                                    
                                    if sgov_quantity_change > 0:
                                        buy_orders.append((self.strategy.sgov_ticker, sgov_quantity_change, sgov_price))
                                    elif sgov_quantity_change < 0:
                                        sell_orders.append((self.strategy.sgov_ticker, abs(sgov_quantity_change), sgov_price))
                                    
                                    processed_tickers.add(self.strategy.sgov_ticker)
                                
                                # 먼저 모든 매도 실행
                                for ticker, qty, price in sell_orders:
                                    try:
                                        self.portfolio.sell(ticker, qty, price, date)
                                    except Exception as e:
                                        logger.warning(f"리밸런싱 매도 실패 [{ticker}] {e}")
                                
                                # 매도 후 포트폴리오 가치 재계산
                                portfolio_value = self.portfolio.total_value
                                
                                # 그 다음 모든 매수 실행
                                for ticker, qty, price in buy_orders:
                                    try:
                                        self.portfolio.buy(ticker, qty, price, date)
                                    except Exception as e:
                                        logger.warning(f"리밸런싱 매수 실패 [{ticker}] {e}")
                        
                        # QQQEMAShannon 전략: Signal=3일 때 리밸런싱 처리
                        elif (hasattr(self.strategy, 'qqq_ticker') and hasattr(self.strategy, 'tqqq_ticker') and 
                              hasattr(self.strategy, 'sgov_ticker') and hasattr(self.strategy, 'qid_ticker') and 
                              stock_signal == 3 and current_mode in ["ABOVE", "BELOW"]):
                            portfolio_value = self.portfolio.total_value
                            
                            if current_mode == "ABOVE":
                                # ABOVE 모드: QQQ + TQQQ 리밸런싱
                                ticker1 = self.strategy.qqq_ticker
                                ticker2 = self.strategy.tqqq_ticker
                                
                                # 다른 종목 매도
                                for ticker in self.tickers:
                                    if ticker in [ticker1, ticker2]:
                                        continue
                                    if ticker not in prices or ticker in processed_tickers:
                                        continue
                                    if self.portfolio.get_position(ticker):
                                        pos = self.portfolio.get_position(ticker)
                                        if pos.quantity > 0:
                                            try:
                                                self.portfolio.sell(ticker, pos.quantity, prices[ticker], date)
                                                processed_tickers.add(ticker)
                                            except Exception as e:
                                                logger.warning(f"매도 실패 [{ticker}] {e}")
                            else:
                                # BELOW 모드: SGOV + QID 리밸런싱
                                ticker1 = self.strategy.sgov_ticker
                                ticker2 = self.strategy.qid_ticker
                                
                                # 다른 종목 매도
                                for ticker in self.tickers:
                                    if ticker in [ticker1, ticker2]:
                                        continue
                                    if ticker not in prices or ticker in processed_tickers:
                                        continue
                                    if self.portfolio.get_position(ticker):
                                        pos = self.portfolio.get_position(ticker)
                                        if pos.quantity > 0:
                                            try:
                                                self.portfolio.sell(ticker, pos.quantity, prices[ticker], date)
                                                processed_tickers.add(ticker)
                                            except Exception as e:
                                                logger.warning(f"매도 실패 [{ticker}] {e}")
                            
                            # 두 종목의 현재 가치 계산
                            value1 = 0.0
                            value2 = 0.0
                            quantity1 = 0
                            quantity2 = 0
                            price1 = 0.0
                            price2 = 0.0
                            
                            if ticker1 in prices:
                                price1 = prices[ticker1]
                            if ticker2 in prices:
                                price2 = prices[ticker2]
                            
                            if ticker1 in self.portfolio.positions:
                                pos1 = self.portfolio.get_position(ticker1)
                                quantity1 = pos1.quantity
                                value1 = quantity1 * price1
                            
                            if ticker2 in self.portfolio.positions:
                                pos2 = self.portfolio.get_position(ticker2)
                                quantity2 = pos2.quantity
                                value2 = quantity2 * price2
                            
                            # 초기 진입: 두 종목이 모두 없으면 초기 매수
                            if quantity1 == 0 and quantity2 == 0:
                                # ticker1 초기 매수
                                if ticker1 in prices and price1 > 0:
                                    target_quantity1 = self.strategy.calculate_position_size(
                                        portfolio_value=portfolio_value,
                                        price=price1,
                                        signal=3,
                                        current_quantity=0,
                                        cash=self.portfolio.cash,
                                        commission_rate=self.commission_rate,
                                        ticker=ticker1,
                                        mode=current_mode,
                                        current_value1=0.0,
                                        current_value2=0.0
                                    )
                                    if target_quantity1 > 0:
                                        try:
                                            self.portfolio.buy(ticker1, target_quantity1, price1, date)
                                            processed_tickers.add(ticker1)
                                        except Exception as e:
                                            logger.warning(f"초기 매수 실패 [{ticker1}] {e}")
                                
                                # ticker2 초기 매수 (ticker1 매수 후 포트폴리오 가치 재계산)
                                portfolio_value = self.portfolio.total_value
                                if ticker1 in self.portfolio.positions and ticker1 in prices:
                                    pos1 = self.portfolio.get_position(ticker1)
                                    value1 = pos1.quantity * prices[ticker1]
                                
                                if ticker2 in prices and price2 > 0:
                                    target_quantity2 = self.strategy.calculate_position_size(
                                        portfolio_value=portfolio_value,
                                        price=price2,
                                        signal=3,
                                        current_quantity=0,
                                        cash=self.portfolio.cash,
                                        commission_rate=self.commission_rate,
                                        ticker=ticker2,
                                        mode=current_mode,
                                        current_value1=value1,
                                        current_value2=0.0
                                    )
                                    if target_quantity2 > 0:
                                        try:
                                            self.portfolio.buy(ticker2, target_quantity2, price2, date)
                                            processed_tickers.add(ticker2)
                                        except Exception as e:
                                            logger.warning(f"초기 매수 실패 [{ticker2}] {e}")
                            else:
                                # 밴딩 리밸런싱 체크 및 처리
                                portfolio_value = self.portfolio.total_value
                                
                                # 가치 재계산
                                if ticker1 in self.portfolio.positions and ticker1 in prices:
                                    pos1 = self.portfolio.get_position(ticker1)
                                    value1 = pos1.quantity * prices[ticker1]
                                if ticker2 in self.portfolio.positions and ticker2 in prices:
                                    pos2 = self.portfolio.get_position(ticker2)
                                    value2 = pos2.quantity * prices[ticker2]
                                
                                needs_rebalance, rebalance_ticker_flag = self.strategy.check_banding_rebalance(
                                    portfolio_value=portfolio_value,
                                    current_value1=value1,
                                    current_value2=value2,
                                    price1=price1,
                                    price2=price2,
                                    quantity1=quantity1,
                                    quantity2=quantity2,
                                    mode=current_mode
                                )
                                
                                # 두 종목 모두 리밸런싱 처리 (매도 먼저, 매수 나중)
                                sell_orders = []
                                buy_orders = []
                                
                                for ticker in [ticker1, ticker2]:
                                    if ticker not in prices or ticker in processed_tickers:
                                        continue
                                    
                                    portfolio_value = self.portfolio.total_value
                                    ticker_price = prices[ticker]
                                    ticker_quantity = 0
                                    if self.portfolio.get_position(ticker):
                                        ticker_quantity = self.portfolio.get_position(ticker).quantity
                                    
                                    # 가치 재계산
                                    if ticker == ticker1:
                                        if ticker1 in self.portfolio.positions:
                                            pos1 = self.portfolio.get_position(ticker1)
                                            value1 = pos1.quantity * prices[ticker1]
                                    else:
                                        if ticker2 in self.portfolio.positions:
                                            pos2 = self.portfolio.get_position(ticker2)
                                            value2 = pos2.quantity * prices[ticker2]
                                    
                                    quantity = self.strategy.calculate_position_size(
                                        portfolio_value=portfolio_value,
                                        price=ticker_price,
                                        signal=3,
                                        current_quantity=ticker_quantity,
                                        cash=self.portfolio.cash,
                                        commission_rate=self.commission_rate,
                                        ticker=ticker,
                                        mode=current_mode,
                                        current_value1=value1,
                                        current_value2=value2
                                    )
                                    
                                    if quantity > 0:
                                        buy_orders.append((ticker, quantity, ticker_price))
                                    elif quantity < 0:
                                        sell_orders.append((ticker, abs(quantity), ticker_price))
                                    
                                    processed_tickers.add(ticker)
                                
                                # 먼저 모든 매도 실행
                                for ticker, qty, price in sell_orders:
                                    try:
                                        self.portfolio.sell(ticker, qty, price, date)
                                    except Exception as e:
                                        logger.warning(f"리밸런싱 매도 실패 [{ticker}] {e}")
                                
                                # 매도 후 포트폴리오 가치 재계산
                                portfolio_value = self.portfolio.total_value
                                
                                # 그 다음 모든 매수 실행
                                for ticker, qty, price in buy_orders:
                                    try:
                                        self.portfolio.buy(ticker, qty, price, date)
                                    except Exception as e:
                                        logger.warning(f"리밸런싱 매수 실패 [{ticker}] {e}")
                        
                        # InverseMA 전략: Signal=3일 때 ABOVE 모드 리밸런싱 (QQQ:TQQQ 1:1)
                        elif hasattr(self.strategy, 'qqq_ticker') and hasattr(self.strategy, 'tqqq_ticker') and stock_signal == 3:
                            # ABOVE 모드: QQQ 50% + TQQQ 50% 밴딩 리밸런싱
                            portfolio_value = self.portfolio.total_value
                            
                            qqq_value = 0.0
                            tqqq_value = 0.0
                            qqq_quantity = 0
                            tqqq_quantity = 0
                            qqq_price = 0.0
                            tqqq_price = 0.0
                            
                            if self.strategy.qqq_ticker in prices:
                                qqq_price = prices[self.strategy.qqq_ticker]
                            if self.strategy.tqqq_ticker in prices:
                                tqqq_price = prices[self.strategy.tqqq_ticker]
                            
                            if self.strategy.qqq_ticker in self.portfolio.positions:
                                pos = self.portfolio.get_position(self.strategy.qqq_ticker)
                                qqq_quantity = pos.quantity
                                qqq_value = qqq_quantity * qqq_price
                            
                            if self.strategy.tqqq_ticker in self.portfolio.positions:
                                pos = self.portfolio.get_position(self.strategy.tqqq_ticker)
                                tqqq_quantity = pos.quantity
                                tqqq_value = tqqq_quantity * tqqq_price
                            
                            # 밴딩 리밸런싱 체크
                            needs_rebalance, rebalance_ticker = self.strategy.check_banding_rebalance(
                                portfolio_value=portfolio_value,
                                current_qqq_value=qqq_value,
                                current_tqqq_value=tqqq_value,
                                qqq_price=qqq_price,
                                tqqq_price=tqqq_price,
                                qqq_quantity=qqq_quantity,
                                tqqq_quantity=tqqq_quantity
                            )
                            
                            # QQQ와 TQQQ 모두 리밸런싱 처리 (매도 먼저, 매수 나중)
                            sell_orders = []
                            buy_orders = []
                            
                            for ticker in [self.strategy.qqq_ticker, self.strategy.tqqq_ticker]:
                                if ticker not in prices or ticker in processed_tickers:
                                    continue
                                
                                portfolio_value = self.portfolio.total_value
                                ticker_price = prices[ticker]
                                ticker_quantity = 0
                                if self.portfolio.get_position(ticker):
                                    ticker_quantity = self.portfolio.get_position(ticker).quantity
                                
                                quantity = self.strategy.calculate_position_size(
                                    portfolio_value=portfolio_value,
                                    price=ticker_price,
                                    signal=3,
                                    current_quantity=ticker_quantity,
                                    cash=self.portfolio.cash,
                                    commission_rate=self.commission_rate,
                                    ticker=ticker,
                                    mode="ABOVE",
                                    current_qqq_value=qqq_value,
                                    current_tqqq_value=tqqq_value,
                                    qqq_price=qqq_price
                                )
                                
                                if quantity > 0:
                                    buy_orders.append((ticker, quantity, ticker_price))
                                elif quantity < 0:
                                    sell_orders.append((ticker, abs(quantity), ticker_price))
                                
                                processed_tickers.add(ticker)
                            
                            # 먼저 모든 매도 실행
                            for ticker, qty, price in sell_orders:
                                try:
                                    self.portfolio.sell(ticker, qty, price, date)
                                except Exception as e:
                                    logger.warning(f"리밸런싱 매도 실패 [{ticker}] {e}")
                            
                            # 매도 후 포트폴리오 가치 재계산
                            portfolio_value = self.portfolio.total_value
                            
                            # 그 다음 모든 매수 실행
                            for ticker, qty, price in buy_orders:
                                try:
                                    self.portfolio.buy(ticker, qty, price, date)
                                except Exception as e:
                                    logger.warning(f"리밸런싱 매수 실패 [{ticker}] {e}")
                        
                        # MovingAverageRebalance 전략: Signal=3일 때 리밸런싱 처리
                        elif hasattr(self.strategy, 'stock_ticker1') and stock_signal == 3 and target_ticker == "ABOVE":
                            # n일선 위 모드: stock_ticker1과 stock_ticker2를 밴딩 리밸런싱
                            portfolio_value = self.portfolio.total_value
                            
                            # stock_ticker1과 stock_ticker2의 현재 가치 계산
                            stock1_value = 0.0
                            stock2_value = 0.0
                            stock1_quantity = 0
                            stock2_quantity = 0
                            stock1_price = 0.0
                            stock2_price = 0.0
                            
                            if self.strategy.stock_ticker1 in self.portfolio.positions:
                                pos1 = self.portfolio.get_position(self.strategy.stock_ticker1)
                                stock1_quantity = pos1.quantity
                                if self.strategy.stock_ticker1 in prices:
                                    stock1_price = prices[self.strategy.stock_ticker1]
                                    stock1_value = stock1_quantity * stock1_price
                            
                            if self.strategy.stock_ticker2 in self.portfolio.positions:
                                pos2 = self.portfolio.get_position(self.strategy.stock_ticker2)
                                stock2_quantity = pos2.quantity
                                if self.strategy.stock_ticker2 in prices:
                                    stock2_price = prices[self.strategy.stock_ticker2]
                                    stock2_value = stock2_quantity * stock2_price
                            
                            # 초기 진입: stock_ticker1과 stock_ticker2가 모두 없으면 초기 매수
                            if stock1_quantity == 0 and stock2_quantity == 0:
                                # stock_ticker1 초기 매수
                                if self.strategy.stock_ticker1 in prices and stock1_price > 0:
                                    stock1_target_quantity = self.strategy.calculate_position_size(
                                        portfolio_value=portfolio_value,
                                        price=stock1_price,
                                        signal=3,
                                        current_quantity=0,
                                        cash=self.portfolio.cash,
                                        current_stock1_value=0.0,
                                        current_stock2_value=0.0,
                                        current_bond_value=0.0,
                                        commission_rate=self.commission_rate,
                                        ticker=self.strategy.stock_ticker1
                                    )
                                    if stock1_target_quantity > 0:
                                        try:
                                            self.portfolio.buy(self.strategy.stock_ticker1, stock1_target_quantity, stock1_price, date)
                                            processed_tickers.add(self.strategy.stock_ticker1)
                                        except Exception as e:
                                            logger.warning(f"초기 매수 실패 [{self.strategy.stock_ticker1}] {e}")
                                
                                # stock_ticker2 초기 매수 (stock_ticker1 매수 후 포트폴리오 가치 재계산)
                                portfolio_value = self.portfolio.total_value
                                # stock_ticker1 가치 재계산
                                if self.strategy.stock_ticker1 in self.portfolio.positions and self.strategy.stock_ticker1 in prices:
                                    pos1 = self.portfolio.get_position(self.strategy.stock_ticker1)
                                    if self.strategy.stock_ticker1 in prices:
                                        stock1_value = pos1.quantity * prices[self.strategy.stock_ticker1]
                                
                                if self.strategy.stock_ticker2 in prices and stock2_price > 0:
                                    stock2_target_quantity = self.strategy.calculate_position_size(
                                        portfolio_value=portfolio_value,
                                        price=stock2_price,
                                        signal=3,
                                        current_quantity=0,
                                        cash=self.portfolio.cash,
                                        current_stock1_value=stock1_value,
                                        current_stock2_value=0.0,
                                        current_bond_value=0.0,
                                        commission_rate=self.commission_rate,
                                        ticker=self.strategy.stock_ticker2
                                    )
                                    if stock2_target_quantity > 0:
                                        try:
                                            self.portfolio.buy(self.strategy.stock_ticker2, stock2_target_quantity, stock2_price, date)
                                            processed_tickers.add(self.strategy.stock_ticker2)
                                        except Exception as e:
                                            logger.warning(f"초기 매수 실패 [{self.strategy.stock_ticker2}] {e}")
                                
                                # bond_ticker 매도 (있다면)
                                if self.strategy.bond_ticker in self.portfolio.positions and self.strategy.bond_ticker in prices:
                                    bond_pos = self.portfolio.get_position(self.strategy.bond_ticker)
                                    if bond_pos.quantity > 0:
                                        try:
                                            self.portfolio.sell(self.strategy.bond_ticker, bond_pos.quantity, prices[self.strategy.bond_ticker], date)
                                            processed_tickers.add(self.strategy.bond_ticker)
                                        except Exception as e:
                                            logger.warning(f"매도 실패 [{self.strategy.bond_ticker}] {e}")
                            else:
                                # 밴딩 리밸런싱 체크
                                portfolio_value = self.portfolio.total_value
                                # 가치 재계산
                                if self.strategy.stock_ticker1 in self.portfolio.positions and self.strategy.stock_ticker1 in prices:
                                    pos1 = self.portfolio.get_position(self.strategy.stock_ticker1)
                                    stock1_value = pos1.quantity * prices[self.strategy.stock_ticker1]
                                if self.strategy.stock_ticker2 in self.portfolio.positions and self.strategy.stock_ticker2 in prices:
                                    pos2 = self.portfolio.get_position(self.strategy.stock_ticker2)
                                    stock2_value = pos2.quantity * prices[self.strategy.stock_ticker2]
                                
                                needs_rebalance, rebalance_ticker = self.strategy.check_banding_rebalance(
                                    portfolio_value=portfolio_value,
                                    current_stock1_value=stock1_value,
                                    current_stock2_value=stock2_value,
                                    stock1_price=stock1_price,
                                    stock2_price=stock2_price,
                                    stock1_quantity=stock1_quantity,
                                    stock2_quantity=stock2_quantity
                                )
                                
                                if needs_rebalance and rebalance_ticker and rebalance_ticker in prices:
                                    # 리밸런싱 필요한 종목 처리
                                    rebalance_price = prices[rebalance_ticker]
                                    if rebalance_price <= 0:
                                        continue
                                    
                                    rebalance_quantity = 0
                                    if self.portfolio.get_position(rebalance_ticker):
                                        rebalance_quantity = self.portfolio.get_position(rebalance_ticker).quantity
                                    
                                    rebalance_target_quantity = self.strategy.calculate_position_size(
                                        portfolio_value=portfolio_value,
                                        price=rebalance_price,
                                        signal=3,
                                        current_quantity=rebalance_quantity,
                                        cash=self.portfolio.cash,
                                        current_stock1_value=stock1_value,
                                        current_stock2_value=stock2_value,
                                        current_bond_value=0.0,
                                        commission_rate=self.commission_rate,
                                        ticker=rebalance_ticker
                                    )
                                    
                                    if rebalance_target_quantity > 0:
                                        try:
                                            self.portfolio.buy(rebalance_ticker, rebalance_target_quantity, rebalance_price, date)
                                        except Exception as e:
                                            logger.warning(f"리밸런싱 매수 실패 [{rebalance_ticker}] {e}")
                                    elif rebalance_target_quantity < 0:
                                        try:
                                            self.portfolio.sell(rebalance_ticker, abs(rebalance_target_quantity), rebalance_price, date)
                                        except Exception as e:
                                            logger.warning(f"리밸런싱 매도 실패 [{rebalance_ticker}] {e}")
                                    
                                    processed_tickers.add(rebalance_ticker)
                            
                            # bond_ticker 매도 (n일선 위 모드에서는 불필요)
                            if self.strategy.bond_ticker in self.portfolio.positions and self.strategy.bond_ticker in prices:
                                bond_pos = self.portfolio.get_position(self.strategy.bond_ticker)
                                if bond_pos.quantity > 0:
                                    try:
                                        self.portfolio.sell(self.strategy.bond_ticker, bond_pos.quantity, prices[self.strategy.bond_ticker], date)
                                        processed_tickers.add(self.strategy.bond_ticker)
                                    except Exception as e:
                                        logger.warning(f"매도 실패 [{self.strategy.bond_ticker}] {e}")
                        
                        elif target_ticker and target_ticker != "ABOVE":
                            portfolio_value = self.portfolio.total_value
                            
                            # Step 1: 목표 종목이 아닌 종목 먼저 전량 매도 (현금 확보)
                            # 중요: 반드시 매도 후 매수 순서로 처리
                            original_holding = getattr(self.strategy, 'current_holding', None)
                            self.strategy.current_holding = target_ticker
                            
                            # 모든 목표가 아닌 종목을 먼저 매도
                            for ticker in self.tickers:
                                if ticker not in prices or date not in self.data_dict[ticker].index:
                                    continue
                                
                                if ticker == target_ticker:
                                    continue  # 목표 종목은 나중에 처리 (Step 3)
                                
                                ticker_price = prices[ticker]
                                ticker_current_quantity = 0
                                if self.portfolio.get_position(ticker):
                                    ticker_current_quantity = self.portfolio.get_position(ticker).quantity
                                
                                # 보유 수량이 있으면 반드시 매도
                                if ticker_current_quantity > 0:
                                    # 현재 가치 계산
                                    current_stock_value = 0.0
                                    current_bond_value = 0.0
                                    if hasattr(self.strategy, 'stock_ticker') and self.strategy.stock_ticker:
                                        if self.strategy.stock_ticker in self.portfolio.positions:
                                            pos = self.portfolio.get_position(self.strategy.stock_ticker)
                                            if self.strategy.stock_ticker in prices:
                                                current_stock_value = pos.quantity * prices[self.strategy.stock_ticker]
                                    if hasattr(self.strategy, 'bond_ticker') and self.strategy.bond_ticker:
                                        if self.strategy.bond_ticker in self.portfolio.positions:
                                            pos = self.portfolio.get_position(self.strategy.bond_ticker)
                                            if self.strategy.bond_ticker in prices:
                                                current_bond_value = pos.quantity * prices[self.strategy.bond_ticker]
                                    
                                    quantity = self.strategy.calculate_position_size(
                                        portfolio_value=portfolio_value,
                                        price=ticker_price,
                                        signal=1,
                                        current_quantity=ticker_current_quantity,
                                        cash=self.portfolio.cash,
                                        current_bond_value=current_bond_value,
                                        current_stock_value=current_stock_value,
                                        commission_rate=self.commission_rate,
                                        ticker=ticker
                                    )
                                    
                                    if quantity < 0:
                                        try:
                                            self.portfolio.sell(ticker, abs(quantity), ticker_price, date)
                                        except Exception as e:
                                            logger.warning(f"매도 실패 [{ticker}] {e}")
                                    
                                    processed_tickers.add(ticker)
                            
                            # Step 2: 매도 완료 후 포트폴리오 가치 재계산
                            # 매도로 확보된 현금으로 목표 종목을 매수하기 위해 가치 재계산
                            portfolio_value = self.portfolio.total_value
                            
                            # Step 3: 목표 종목 100% 매수 (매도 후 확보된 현금으로)
                            if target_ticker in prices and target_ticker in self.data_dict and date in self.data_dict[target_ticker].index:
                                target_price = prices[target_ticker]
                                target_current_quantity = 0
                                if self.portfolio.get_position(target_ticker):
                                    target_current_quantity = self.portfolio.get_position(target_ticker).quantity
                                
                                current_stock_value = 0.0
                                current_bond_value = 0.0
                                if hasattr(self.strategy, 'stock_ticker') and self.strategy.stock_ticker:
                                    if self.strategy.stock_ticker in self.portfolio.positions:
                                        pos = self.portfolio.get_position(self.strategy.stock_ticker)
                                        if self.strategy.stock_ticker in prices:
                                            current_stock_value = pos.quantity * prices[self.strategy.stock_ticker]
                                if hasattr(self.strategy, 'bond_ticker') and self.strategy.bond_ticker:
                                    if self.strategy.bond_ticker in self.portfolio.positions:
                                        pos = self.portfolio.get_position(self.strategy.bond_ticker)
                                        if self.strategy.bond_ticker in prices:
                                            current_bond_value = pos.quantity * prices[self.strategy.bond_ticker]
                                
                                target_quantity = self.strategy.calculate_position_size(
                                    portfolio_value=portfolio_value,
                                    price=target_price,
                                    signal=1,
                                    current_quantity=target_current_quantity,
                                    cash=self.portfolio.cash,
                                    current_bond_value=current_bond_value,
                                    current_stock_value=current_stock_value,
                                    commission_rate=self.commission_rate,
                                    ticker=target_ticker
                                )
                                
                                if target_quantity > 0:
                                    try:
                                        self.portfolio.buy(target_ticker, target_quantity, target_price, date)
                                    except Exception as e:
                                        logger.warning(f"매수 실패 [{target_ticker}] {e}")
                                
                                processed_tickers.add(target_ticker)
                            
                            # 원래 값 복원
                            if original_holding is not None:
                                self.strategy.current_holding = original_holding
            
            # 각 종목에 대해 신호 체크 및 리밸런싱
            # MovingAverage/MovingAverageBreakout/MovingAverageRebalance 전략은 이미 처리되었으므로 건너뛰기
            if not (hasattr(self.strategy, 'stock_ticker') or hasattr(self.strategy, 'base_ticker')):
                for ticker in self.tickers:
                    if ticker not in prices:
                        continue
                    
                    price = prices[ticker]
                    df = self.data_dict[ticker]
                    
                    if date not in df.index:
                        continue
                    
                    row = df.loc[date]
                    signal = row.get("Signal", 0)
                    
                    if signal != 0 and ticker not in processed_tickers:
                        # 포지션 사이징 계산
                        portfolio_value = self.portfolio.total_value
                        current_quantity = 0
                        if self.portfolio.get_position(ticker):
                            current_quantity = self.portfolio.get_position(ticker).quantity
                        
                        # 다른 종목들의 현재 가치 계산
                        current_stock_value = 0.0
                        current_bond_value = 0.0
                        
                        if hasattr(self.strategy, 'stock_ticker') and self.strategy.stock_ticker:
                            stock_ticker = self.strategy.stock_ticker
                            if stock_ticker in self.portfolio.positions:
                                pos = self.portfolio.get_position(stock_ticker)
                                if stock_ticker in prices:
                                    current_stock_value = pos.quantity * prices[stock_ticker]
                        
                        if hasattr(self.strategy, 'bond_ticker') and self.strategy.bond_ticker:
                            bond_ticker = self.strategy.bond_ticker
                            if bond_ticker in self.portfolio.positions:
                                pos = self.portfolio.get_position(bond_ticker)
                                if bond_ticker in prices:
                                    current_bond_value = pos.quantity * prices[bond_ticker]
                        
                        quantity = self.strategy.calculate_position_size(
                            portfolio_value=portfolio_value,
                            price=price,
                            signal=signal,
                            current_quantity=current_quantity,
                            cash=self.portfolio.cash,
                            current_bond_value=current_bond_value,
                            current_stock_value=current_stock_value,
                            commission_rate=self.commission_rate,
                            ticker=ticker
                        )
                        
                        # 거래 실행
                        if quantity > 0:
                            try:
                                self.portfolio.buy(ticker, quantity, price, date)
                                if signal == 2:
                                    logger.debug(f"리밸런싱 매수 [{ticker}] {quantity}주 @ ${price:.2f}")
                            except Exception as e:
                                logger.warning(f"매수 실패 [{ticker}] {e}")
                        elif quantity < 0:
                            try:
                                self.portfolio.sell(ticker, abs(quantity), price, date)
                                if signal == 2:
                                    logger.debug(f"리밸런싱 매도 [{ticker}] {abs(quantity)}주 @ ${price:.2f}")
                            except Exception as e:
                                logger.warning(f"매도 실패 [{ticker}] {e}")
            
            # 스냅샷
            self.portfolio.snapshot(date)
        
        logger.info("백테스팅 완료")
        
        # 결과 정리
        self.results = pd.DataFrame(self.portfolio.equity_curve)
        if not self.results.empty:
            self.results.set_index("date", inplace=True)
        
        return self.results

    def get_summary(self) -> dict:
        """백테스팅 결과 요약"""
        if self.results.empty:
            return {}
        
        final_value = self.results["total_value"].iloc[-1]
        total_return = self.portfolio.total_profit_loss_pct
        
        # 연환산 수익률 계산
        days = len(self.results)
        years = days / 365.25
        annualized_return = ((final_value / self.initial_cash) ** (1 / years) - 1) * 100 if years > 0 else 0
        
        tickers_str = ", ".join(self.tickers)
        
        # 리스크 보정 지표 계산
        metrics = calculate_all_metrics(self.results, self.initial_cash)
        
        summary = {
            "Strategy": self.strategy.name if self.strategy else "N/A",
            "Tickers": tickers_str,
            "Period": f"{self.results.index[0].strftime('%Y-%m-%d')} ~ {self.results.index[-1].strftime('%Y-%m-%d')}",
            "Days": days,
            "Initial Cash": f"${self.initial_cash:,.2f}",
            "Final Value": f"${final_value:,.2f}",
            "Total Return": f"{total_return:.2f}%",
            "Annualized Return": f"{annualized_return:.2f}%",
            "Total Trades": len(self.portfolio.trades),
        }
        
        # 추가 지표 추가
        if metrics:
            summary.update({
                "Sharpe Ratio": f"{metrics.get('sharpe_ratio', 0):.2f}",
                "Sortino Ratio": f"{metrics.get('sortino_ratio', 0):.2f}",
                "Calmar Ratio": f"{metrics.get('calmar_ratio', 0):.2f}",
                "Volatility": f"{metrics.get('volatility', 0):.2f}%",
                "Max Drawdown": f"{metrics.get('max_drawdown', 0):.2f}%",
            })
            if metrics.get("recovery_days") is not None:
                summary["Recovery Days"] = f"{metrics['recovery_days']}일"
            else:
                summary["Recovery Days"] = "미회복"
        
        # 현금 버전 통계 추가
        if (hasattr(self.strategy, 'use_bond') and not self.strategy.use_bond and 
            self.stock_pct_history):
            avg_stock_pct = np.mean(self.stock_pct_history) * 100
            below_avg = np.mean(self.below_ma_stock_pct) * 100 if self.below_ma_stock_pct else 0
            above_avg = np.mean(self.above_ma_stock_pct) * 100 if self.above_ma_stock_pct else 0
            max_stock_pct = np.max(self.stock_pct_history) * 100
            min_stock_pct = np.min(self.stock_pct_history) * 100
            
            summary["현금버전 통계"] = {
                "전체 평균 TQQQ 비율": f"{avg_stock_pct:.2f}%",
                "200일선 아래 평균 TQQQ 비율": f"{below_avg:.2f}%",
                "200일선 위 평균 TQQQ 비율": f"{above_avg:.2f}%",
                "최대 TQQQ 비율": f"{max_stock_pct:.2f}%",
                "최소 TQQQ 비율": f"{min_stock_pct:.2f}%",
                "200일선 아래 일수": f"{self.below_ma_days}일",
                "200일선 위 일수": f"{self.above_ma_days}일",
            }
        
        return summary

    def get_holdings(self) -> pd.DataFrame:
        """현재 보유 종목"""
        return self.portfolio.get_holdings_summary()

