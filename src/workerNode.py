import threading
import time
import json
import random
import os
from connectService import create_rabbit_channel, connect_db
from logger import log, get_workerID, get_workerPort

# MongoDB 연결
collection = connect_db()

# 메시지 처리 함수
def task(message):
    result = [''] * len(message)
    error_flag = threading.Event()

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

    if collection.find_one({"task_id": task_id}):
        log("info", f"Task ID: {task_id} already processed")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    error_num = random.randint(1, 20)

    try:
        log("info", f"Processing: {message}, Task ID: {task_id}")

        if error_num == 1:
            log("error", "에러상황1: 작업 중 에러 발생 (ACK 없이 재시도)")
            raise Exception("에러상황1: 들어온 정보에 작업 중에 에러가 발생한 상황")

        uppercase_message = task(message)

        collection.insert_one({"task_id": task_id, "message": uppercase_message, "status": "Success"})

        if error_num == 2:
            log("error", "에러상황2: 작업 완료 후 ACK 누락 가능성")
            raise Exception("에러상황2: 작업 완료 했는데 노드가 불안정해서 중복이 발생할 수 있는 상황")

        ch.basic_ack(delivery_tag=method.delivery_tag)
        log("info", f"Task {task_id} processed successfully")

    except Exception as e:
        log("error", f"Error processing task {task_id}: {e}")
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
