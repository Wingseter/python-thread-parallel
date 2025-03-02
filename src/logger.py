import logging
import os
from lokiHandler import LokiHandler

# 환경 변수
WORKER_ID = os.getenv("WORKER_ID", "default")
WORKER_PORT = os.getenv("WORKER_PORT", "8001")
LOKI_URL = os.getenv("LOKI_URL", "http://localhost:3100/loki/api/v1/push")

def get_workerID():
    return WORKER_ID

def get_workerPort():
    return WORKER_PORT

def get_lokiURL():
    return LOKI_URL

# 로거 설정 함수
def setup_logger():
    logger = logging.getLogger(f"worker_{WORKER_PORT}")
    logger.setLevel(logging.INFO)

    # Loki 핸들러 추가
    loki_handler = LokiHandler(
        url=LOKI_URL,
        labels={"job": "workers", "worker_id": WORKER_ID, "port": WORKER_PORT}
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
    formatted_message = f"[Worker {WORKER_PORT}] {message}"
    
    if level == "info":
        logger.info(formatted_message)
    elif level == "error":
        logger.error(formatted_message)
    elif level == "warning":
        logger.warning(formatted_message)
    else:
        logger.debug(formatted_message)
