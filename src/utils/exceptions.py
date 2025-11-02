"""
커스텀 예외 클래스
"""


class TradingError(Exception):
    """트레이딩 기본 예외"""
    pass


class InsufficientFundsError(TradingError):
    """자금 부족 예외"""
    pass


class InvalidOrderError(TradingError):
    """유효하지 않은 주문 예외"""
    pass


class DataCollectionError(TradingError):
    """데이터 수집 실패 예외"""
    pass


class StrategyError(TradingError):
    """전략 실행 오류 예외"""
    pass


class BacktestError(TradingError):
    """백테스팅 실행 오류 예외"""
    pass

