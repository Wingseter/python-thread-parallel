import threading
import time
import json
import random
import os
import signal
import socket
from connectService import create_rabbit_channel, connect_db, is_task_processed, mark_task_processed
from logger import log, get_workerID, get_workerPort

REMOTE_PORT = int(os.getenv("REMOTE_PORT", "9999")) 

# MongoDB 연결
collection = connect_db()

# Remote Control 변수 
error_num = 0

# 테스트를 위한 소켓 서버
def socket_server():
    global error_num
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", REMOTE_PORT))  
    server.listen(1)

    log("info", f"Socket Server started on port {REMOTE_PORT}. Waiting for commands...")

    while True:
        conn, addr = server.accept()
        data = conn.recv(1024).decode("utf-8").strip()
        
        if data.isdigit():
            error_num = int(data)
            log("info", f"Received new error_num: {error_num}")
            conn.sendall(f"Updated error_num to {error_num}".encode("utf-8"))
        else:
            conn.sendall("Invalid input. Send an integer.".encode("utf-8"))
        
        conn.close()

# 메시지 처리 함수 파일을 나누어도 되지만 평가를 돕기 위해 같이 둠
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

    # 멀티 쓰레드 배열
    threads = [threading.Thread(target=thread_task, args=(char, result, index)) for index, char in enumerate(message)]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # 쓰레드 중 하나라도 에러가 발생하면 에러 처리
    if error_flag.is_set():
        raise Exception("에러상황5: 강화된 멀티 쓰레드 에러 처리")

    uppercased_message = ''.join(result)

    return uppercased_message

# RabbitMQ 메시지 처리
def process_message(ch, method, properties, body):
    global error_num
    message_data = json.loads(body.decode())

    task_id = message_data["task_id"]
    message = message_data["message"]

    log("info", f"Processing: {message}, Task ID: {task_id}")

    # 방법 1: Redis 사용
    if is_task_processed(task_id):
        log("info", f"Task ID: {task_id} already processed (Redis Cache)")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return
    
    # 방법 2: Redis 대신 MongoDB 사용하려면 아래 주석 해제
    # if collection.find_one({"task_id": task_id}):
    #     log("info", f"Task ID: {task_id} already processed")
    #     ch.basic_ack(delivery_tag=method.delivery_tag)
    #     return

    try:
        if error_num == 1:
            raise Exception(f"에러 상황1: 들어온 {message} 에 작업 중에 에러가 발생한 상황(ACK 없이 재시도)")
        if error_num == 2:
            log("error", "에러 발생(작업 시작 ~ 중간) Criical Error Occurred - Worker Node DIE!")
            time.sleep(1)
            os.kill(os.getpid(), signal.SIGSEGV) # 노드가 죽어서 다음 실행 못함

        uppercase_message = task(message)

        collection.insert_one({"task_id": task_id, "message": uppercase_message, "status": "Success"})
        mark_task_processed(task_id)

        if error_num == 3:
            raise Exception(f"에러상황2: 작업 완료 했는데 노드가 불안정해서 {message} 중복이 발생할 수 있는 상황")
        if error_num == 4:
            log("error", "에러 발생(작업 이후) Criical Error Occurred - Worker Node DIE!")
            time.sleep(1)
            os.kill(os.getpid(), signal.SIGSEGV)

        ch.basic_ack(delivery_tag=method.delivery_tag)
        log("info", f"{message} processed to {uppercase_message} successfully")

    except Exception as e:
        log("error", f"Error {task_id}: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    error_num = 0
    time.sleep(0.5)

# RabbitMQ Worker
def worker():
    connection, channel = create_rabbit_channel()
    channel.basic_consume(queue='task_queue', on_message_callback=process_message)
    
    log("info", f"{get_workerID()} started on port {get_workerPort()}")

    channel.start_consuming()

if __name__ == "__main__":
    # 소켓 서버 실행 (에러 값을 변경할 수 있도록)
    socket_thread = threading.Thread(target=socket_server, daemon=True)
    socket_thread.start()

    # Worker 실행
    worker()
