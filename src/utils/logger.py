"""
로깅 설정 모듈
"""

from pathlib import Path
import sys
from loguru import logger

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config.settings import get_settings


def setup_logger():
    """로거 설정"""
    settings = get_settings()
    
    # 로그 디렉토리 생성
    settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # 기본 로거 제거
    logger.remove()
    
    # 콘솔 로깅
    logger.add(
        lambda msg: print(msg, end=""),
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="DEBUG",
        colorize=True,
    )
    
    # 파일 로깅
    logger.add(
        settings.LOG_DIR / "backtest_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="30 days",
        compression="zip",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
    )
    
    return logger

