import pika
import pymongo
import threading
import time
import json
import random
from prometheus_client import start_http_server, Counter, Gauge
import os
from connectService import create_channel, connect_db

collection = connect_db()

def task(message):
    result = [''] * len(message)
    threads = []
    error_flag = 1

    # 예외 처리를 강화해서 각 
    # 메시지를 대문자로 변환하는 작업을 각 문자별로 쓰레드로 처리
    def uppercase_char(char):
        return char.upper()

    # 각 문자를 대문자로 변환하는 작업을 수행하는 스레드 함수
    def thread_task(char, result, index):
        try:
            result[index] = uppercase_char(char)
        except Exception as e:
            print(f"Error in thread_task: {e}")
            error_flag = error_flag * 0


    # 각 문자를 대문자로 바꾸는 스레드 생성
    for index, char in enumerate(message):
        thread = threading.Thread(target=thread_task, args=(char, result, index))
        threads.append(thread)
        thread.start()

    # 모든 스레드가 종료될 때까지 대기
    for thread in threads:
        thread.join()

    # 멀티 쓰레드 중 하나라도 에러가 발생할 경우
    if error_flag == 0:
        raise Exception("에러상황3: 강화된 멀티 쓰레드 에러 처리")

    # 멀티 쓰레드 결과 출력
    uppercased_message = ''.join(result)
    print(f"Uppercased Message: {uppercased_message}")

    return uppercased_message

def process_message(ch, method, properties, body):
    message_data = json.loads(body.decode())
    task_id = message_data["task_id"]
    message = message_data["message"]

    if collection.find_one({"task_id": task_id}):  # 이미 처리된 메시지인 경우
        print(f"[Worker] Task ID: {task_id} already processed")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    # 강제 오류 발생 테스트 TODO: 리모드로 변경
    error_num = random.randint(1, 20)

    try:
        print(f"[Worker] Processing: {message}, Task ID: {task_id}")

        if error_num == 1: # 5% 확률
            print("--------Error 발생-------")  # Exception ACK 안보내고 Queue에 다시 넣기
            raise Exception("에러상황1: 들어온 정보에 작업 중에 에러가 발생한 상황")
      
        uppercase_message = task(message)
        # MongoDB에 저장
        collection.insert_one({"task_id": task_id, "message": uppercase_message, "status": "Success"})
        
        if error_num == 2: # 역시 5% 확률
            print("--------Error 발생-------")  # Exception 완료 했는데 ACK 안보낼 경우
            raise Exception("에러상황2: 작업 완료 했는데 노드가 불안정해서 중복이 발생할 수 있는 상황")
 
        # 정상적으로 메시지가 처리되었으므로 ACK 보내기
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"[Worker] Error: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True) 

    time.sleep(0.5)  # TODO: Just for test, remove later


# RabbitMQ Worker
def worker(worker_port):
    connection, channel = create_channel()
    channel.basic_consume(queue='task_queue', on_message_callback=process_message)
    print(f"Worker started")

    channel.start_consuming()

if __name__ == "__main__":
    worker_port = int(os.getenv("WORKER_PORT", 8001))
    worker(worker_port)
