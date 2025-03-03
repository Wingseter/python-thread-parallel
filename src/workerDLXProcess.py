import time
import json

from dbHandler import connect_db, get_insert_failed_task_sql
from logger import log
from rabbitmqHandler import create_rabbit_channel

# DLX 메시지를 처리하여 MySQL failed_tasks 테이블에 저장
def process_failed_messages():
    db_conn = connect_db()

    while True:
        try:
            connection, channel = create_rabbit_channel()

            method_frame, header_frame, body = channel.basic_get(queue='dead_letter_queue')

            if method_frame:
                message_data = json.loads(body.decode())
                task_id = message_data["task_id"]
                message = message_data["message"]

                log("info", f"[DLX Processor] Storing failed message to DB: {task_id}")

                # MySQL에 실패한 메시지 저장
                with db_conn.cursor() as cursor:
                    cursor.execute(get_insert_failed_task_sql(), (task_id, message))

                # DLX에서 메시지 삭제
                channel.basic_ack(delivery_tag=method_frame.delivery_tag)

            time.sleep(0.5)  # DLX 처리 간격

        except Exception as e:
            log("error", f"[DLX Processor] Error: {e}")
            time.sleep(5)  

if __name__ == "__main__":
    process_failed_messages()
