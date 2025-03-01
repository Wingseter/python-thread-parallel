import threading
import time
import json
import random
import os
from connectService import create_rabbit_channel, connect_db, is_task_processed, mark_task_processed
from logger import log, get_workerID, get_workerPort

# MongoDB 연결
collection = connect_db()

# 메시지 처리 함수
def task(message):
    result = [''] * len(message)
    error_flag = threading.Event()

    # 합쳐도 되지만 멀티쓰레드를 설명하기 위해 따로 함수로 분리
    def uppercase_char(char):
        return char.upper()

    def thread_task(char, result, index):
        try:
            result[index] = uppercase_char(char)
        except Exception as e:
            log("error", f"Error in thread_task: {e}")
            error_flag.set()

    threads = [threading.Thread(target=thread_task, args=(char, result, index)) for index, char in enumerate(message)]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    if error_flag.is_set():
        raise Exception("에러상황3: 강화된 멀티 쓰레드 에러 처리")

    uppercased_message = ''.join(result)
    log("info", f"Uppercased Message: {uppercased_message}")

    return uppercased_message

# RabbitMQ 메시지 처리
def process_message(ch, method, properties, body):
    message_data = json.loads(body.decode())

    task_id = message_data["task_id"]
    message = message_data["message"]

    log("info", f"Processing: {message}, Task ID: {task_id}")

    if is_task_processed(task_id):
        log("info", f"Task ID: {task_id} already processed (Redis Cache)")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return
    
    # Redis 대신 MongoDB 사용하려면 아래 주석 해제
    # if collection.find_one({"task_id": task_id}):
    #     log("info", f"Task ID: {task_id} already processed")
    #     ch.basic_ack(delivery_tag=method.delivery_tag)
    #     return

    error_num = random.randint(1, 20) # 오류를 시뮬레이션 하기 위한 렌덤 값

    try:
        if error_num == 1:
            raise Exception(f"에러상황1: 들어온 {message} 에 작업 중에 에러가 발생한 상황(ACK 없이 재시도)")

        uppercase_message = task(message)

        collection.insert_one({"task_id": task_id, "message": uppercase_message, "status": "Success"})
        mark_task_processed(task_id)

        if error_num == 2:
            raise Exception(f"에러상황2: 작업 완료 했는데 노드가 불안정해서 {message} 중복이 발생할 수 있는 상황")

        ch.basic_ack(delivery_tag=method.delivery_tag)
        log("info", f"{message} processed successfully")

    except Exception as e:
        log("error", f"Error {task_id}: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    time.sleep(0.5)

# RabbitMQ Worker
def worker():
    connection, channel = create_rabbit_channel()
    channel.basic_consume(queue='task_queue', on_message_callback=process_message)
    
    log("info", f"{get_workerID()} started on port {get_workerPort()}")

    channel.start_consuming()

if __name__ == "__main__":
    worker()
