import pymysql
import config
from logger import log

# MySQL 연결 함수
def connect_db():
    retry = 5
    for attempt in range(retry):
        try:
            conn = pymysql.connect(
                host=config.get_db_host(),
                user=config.get_db_user(),
                password=config.get_db_pass(),
                database=config.get_db_name(),
                port=config.get_db_port(),
                charset="utf8mb4",
                autocommit=True
            )
            log("info", "Connected to MySQL successfully")

            # 테이블 생성 (초기 실행 시 필요)
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS processed_tasks (
                        task_id VARCHAR(36) PRIMARY KEY,
                        message TEXT NOT NULL,
                        status VARCHAR(10) NOT NULL
                    );
                """)

            return conn
        except Exception as e:
            log("error", f"MySQL Connection Failed (Attempt {attempt + 1}/{retry}): {e}")
    
    log("error", "MySQL connection failed")
    raise RuntimeError("Failed to connect to MySQL")

