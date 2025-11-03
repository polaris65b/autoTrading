"""
포트폴리오 관리 모듈
현금, 보유 종목, 거래 내역 등을 관리
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, List
import pandas as pd
from loguru import logger

from src.utils.exceptions import InsufficientFundsError, InvalidOrderError
from src.config.settings import get_settings


@dataclass
class Position:
    """보유 포지션 정보"""

    ticker: str
    quantity: int
    avg_price: float
    current_price: float
    first_buy_date: datetime

    @property
    def market_value(self) -> float:
        """평가 금액"""
        return self.quantity * self.current_price

    @property
    def cost(self) -> float:
        """매수 원가"""
        return self.quantity * self.avg_price

    @property
    def profit_loss(self) -> float:
        """평가 손익"""
        return self.market_value - self.cost

    @property
    def profit_loss_pct(self) -> float:
        """평가 손익률"""
        if self.cost == 0:
            return 0.0
        return (self.profit_loss / self.cost) * 100


@dataclass
class Trade:
    """거래 내역"""

    date: datetime
    ticker: str
    action: str  # 'BUY' or 'SELL'
    quantity: int
    price: float
    commission: float
    amount: float

    @property
    def net_amount(self) -> float:
        """순 거래 금액 (수수료 포함)"""
        return self.amount + self.commission


@dataclass
class Portfolio:
    """포트폴리오 클래스"""

    initial_cash: float
    commission_rate: float = 0.0014
    
    cash: float = field(init=False)
    positions: Dict[str, Position] = field(default_factory=dict)
    trades: List[Trade] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)
    
    def __post_init__(self):
        self.cash = self.initial_cash

    def _calculate_commission(self, amount: float) -> float:
        """수수료 계산"""
        return amount * self.commission_rate

    def update_price(self, ticker: str, price: float):
        """
        현재가 업데이트
        
        Args:
            ticker: 종목 코드
            price: 현재가
        """
        if ticker in self.positions:
            self.positions[ticker].current_price = price
    
    def receive_dividend(self, ticker: str, dividend_per_share: float, date: datetime):
        """
        배당금 수령
        
        Args:
            ticker: 종목 코드
            dividend_per_share: 주당 배당금
            date: 배당일
        """
        if ticker not in self.positions:
            return
        
        pos = self.positions[ticker]
        total_dividend = pos.quantity * dividend_per_share
        
        if total_dividend > 0:
            self.cash += total_dividend
            logger.debug(f"배당금 수령 [{ticker}] {pos.quantity}주 × ${dividend_per_share:.4f} = ${total_dividend:.2f}")

    def buy(
        self,
        ticker: str,
        quantity: int,
        price: float,
        date: datetime,
        allow_fractional: bool = False
    ):
        """
        매수 주문
        
        Args:
            ticker: 종목 코드
            quantity: 수량
            price: 주문가
            date: 거래일
            allow_fractional: 소수점 매수 허용 여부
        """
        if quantity <= 0:
            raise InvalidOrderError("수량은 0보다 커야 합니다")
        
        if not allow_fractional and not isinstance(quantity, int):
            raise InvalidOrderError("정수 단위 거래만 가능합니다")

        amount = quantity * price
        commission = self._calculate_commission(amount)
        total_cost = amount + commission

        if self.cash < total_cost:
            raise InsufficientFundsError(
                f"자금 부족: 보유 {self.cash:,.0f}원 < 필요 {total_cost:,.0f}원"
            )

        self.cash -= total_cost

        # 기존 보유 종목인 경우 평균 단가 재계산
        if ticker in self.positions:
            pos = self.positions[ticker]
            total_quantity = pos.quantity + quantity
            total_cost = (pos.cost + amount)
            pos.avg_price = total_cost / total_quantity
            pos.quantity = total_quantity
        else:
            self.positions[ticker] = Position(
                ticker=ticker,
                quantity=quantity,
                avg_price=price,
                current_price=price,
                first_buy_date=date
            )

        trade = Trade(
            date=date,
            ticker=ticker,
            action="BUY",
            quantity=quantity,
            price=price,
            commission=commission,
            amount=amount
        )
        
        self.trades.append(trade)
        logger.debug(f"매수 [{ticker}] {quantity}주 @ {price:,.0f}원")

    def sell(
        self,
        ticker: str,
        quantity: int,
        price: float,
        date: datetime,
        allow_partial: bool = True
    ):
        """
        매도 주문
        
        Args:
            ticker: 종목 코드
            quantity: 수량
            price: 주문가
            date: 거래일
            allow_partial: 부분 매도 허용 여부
        """
        if ticker not in self.positions:
            raise InvalidOrderError(f"보유하지 않은 종목입니다: {ticker}")

        if quantity <= 0:
            raise InvalidOrderError("수량은 0보다 커야 합니다")

        pos = self.positions[ticker]
        
        if quantity > pos.quantity:
            if not allow_partial:
                raise InvalidOrderError(
                    f"보유 수량 부족: 보유 {pos.quantity}주 < 주문 {quantity}주"
                )
            quantity = pos.quantity

        amount = quantity * price
        commission = self._calculate_commission(amount)
        net_amount = amount - commission

        self.cash += net_amount

        # 포지션 업데이트
        pos.quantity -= quantity
        if pos.quantity == 0:
            del self.positions[ticker]

        trade = Trade(
            date=date,
            ticker=ticker,
            action="SELL",
            quantity=quantity,
            price=price,
            commission=commission,
            amount=amount
        )
        
        self.trades.append(trade)
        logger.debug(f"매도 [{ticker}] {quantity}주 @ {price:,.0f}원")

    @property
    def total_market_value(self) -> float:
        """총 평가 금액"""
        return sum(pos.market_value for pos in self.positions.values())

    @property
    def total_value(self) -> float:
        """총 자산 (현금 + 보유 종목 평가금)"""
        return self.cash + self.total_market_value

    @property
    def total_profit_loss(self) -> float:
        """총 평가 손익"""
        return sum(pos.profit_loss for pos in self.positions.values())

    @property
    def total_profit_loss_pct(self) -> float:
        """총 수익률"""
        if self.initial_cash == 0:
            return 0.0
        return ((self.total_value - self.initial_cash) / self.initial_cash) * 100

    def get_position(self, ticker: str) -> Optional[Position]:
        """포지션 조회"""
        return self.positions.get(ticker)

    def get_holdings_summary(self) -> pd.DataFrame:
        """보유 종목 요약 정보"""
        if not self.positions:
            return pd.DataFrame()

        data = []
        for pos in self.positions.values():
            data.append({
                "Ticker": pos.ticker,
                "Quantity": pos.quantity,
                "Avg Price": f"{pos.avg_price:.2f}",
                "Current Price": f"{pos.current_price:.2f}",
                "Market Value": f"{pos.market_value:.2f}",
                "P&L": f"{pos.profit_loss:.2f}",
                "Return %": f"{pos.profit_loss_pct:.2f}%"
            })

        return pd.DataFrame(data)

    def snapshot(self, date: datetime):
        """포트폴리오 스냅샷 저장"""
        for pos in self.positions.values():
            # 현재가를 snapshot 시점의 가격으로 업데이트
            pass
        
        equity = self.total_value
        self.equity_curve.append({
            "date": date,
            "cash": self.cash,
            "market_value": self.total_market_value,
            "total_value": equity,
            "num_positions": len(self.positions)
        })

