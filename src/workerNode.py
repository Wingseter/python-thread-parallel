import threading
import time
import json
import pika
import os
import signal
import socket
from connectService import create_rabbit_channel, connect_db, is_task_processed, mark_task_processed
from logger import log, get_workerID, get_workerPort
from multiThreadTask import task

REMOTE_PORT = int(os.getenv("REMOTE_PORT", "9999")) 

# MongoDB 연결
collection = connect_db()

# Remote Control 변수 
error_num = 0

# 처리량 측정을 위한 변수
total_messages_processed = 0
start_time = time.time()

# 테스트를 위한 소켓 서버
def socket_server():
    global error_num
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", REMOTE_PORT))  
    server.listen(1)

    log("info", f"Socket Server started on port {REMOTE_PORT}. Waiting for commands...")

    # 계속해서 돌아가며 에러 리모트 컨트롤 실행
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


# RabbitMQ 메시지 처리
def process_message(ch, method, properties, body):
    global error_num, total_messages_processed, start_time

    message_data = json.loads(body.decode())

    task_id = message_data["task_id"]
    message = message_data["message"]

    log("info", f"Processing: {message}, Task ID: {task_id}")

    # Redis를 사용해 중복 처리
    if is_task_processed(task_id):
        log("info", f"Task ID: {task_id} already processed (Redis Cache)")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return
    
    try:
        # 예외 상황 1, 2 
        if error_num == 1:
            raise Exception(f"에러 상황1: 들어온 {message} 에 작업 중에 에러가 발생한 상황(ACK 없이 재시도)")
        if error_num == 2:
            log("error", "에러 발생(작업 시작 ~ 중간) 노드 죽음")
            time.sleep(1)
            os.kill(os.getpid(), signal.SIGSEGV) # 노드가 죽어서 다음 실행 못함

        # 작업 처리
        uppercase_message = task(message)

        # 결과 저장
        collection.insert_one({"task_id": task_id, "message": uppercase_message, "status": "Success"})
        mark_task_processed(task_id)

        # 예외 상황 3, 4
        if error_num == 3:
            raise Exception(f"에러상황2: 작업 완료 했는데 노드가 불안정해서 {message} 중복이 발생할 수 있는 상황")
        if error_num == 4:
            log("error", "에러 발생(작업 이후) 노드 죽음")
            time.sleep(1)
            os.kill(os.getpid(), signal.SIGSEGV)

        # 메시지 처리 완료
        ch.basic_ack(delivery_tag=method.delivery_tag)

        # 처리량 측정
        total_messages_processed += 1
        elapsed_time = time.time() - start_time
        messages_per_second = total_messages_processed / elapsed_time if elapsed_time > 0 else 0

        log("info", f"[Worker {get_workerID()}] Processed {total_messages_processed} messages | {messages_per_second:.2f} msg/sec")

    except Exception as e:
        log("error", f"Error {task_id}: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    time.sleep(0.5)

# RabbitMQ Worker
def worker():
    while True:
        try:
            connection, channel = create_rabbit_channel()
            channel.basic_consume(queue='task_queue', on_message_callback=process_message)
                        
            log("info", f"{get_workerID()} started on port {get_workerPort()}")

            channel.start_consuming()

        except pika.exceptions.AMQPConnectionError:
            log("error", "RabbitMQ connection failed. Connect another...")
            time.sleep(5)
        except Exception as e:
            log("error", f"RabbitMQ connection failed: {e}")
            time.sleep(5)


if __name__ == "__main__":
    # 소켓 서버 실행 (에러 값을 변경할 수 있도록)
    socket_thread = threading.Thread(target=socket_server, daemon=True)
    socket_thread.start()

    # Worker 실행
    worker()
