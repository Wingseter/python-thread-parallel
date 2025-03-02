import logging
import os
from lokiHandler import LokiHandler
import config

# 로거 설정 함수
def setup_logger():
    logger = logging.getLogger(f"worker_{config.get_worker_id()}")
    logger.setLevel(logging.INFO)

    # Loki 핸들러 추가
    loki_handler = LokiHandler(
        url=config.get_loki_url(),
        labels={"job": "workers", "worker_id": config.get_worker_id(), "port": config.get_worker_port()}
    )

    # 로키 출력 헨들러 추가
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")
    loki_handler.setFormatter(formatter)
    logger.addHandler(loki_handler)

    # 콘솔 출력 핸들러 추가
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

# 로거 인스턴스 생성
logger = setup_logger()

# 로그 출력 함수
def log(level, message):
    formatted_message = f"[Worker {config.get_worker_port()}] {message}"
    
    if level == "info":
        logger.info(formatted_message)
    elif level == "error":
        logger.error(formatted_message)
    elif level == "warning":
        logger.warning(formatted_message)
    else:
        logger.debug(formatted_message)
