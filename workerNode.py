import pika
import pymongo
from concurrent.futures import ThreadPoolExecutor
import threading
import time
import json
import random

# MongoDB 연결
mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
db = mongo_client["test_db"]
collection = db["processed_tasks"]


def create_channel():
    credentials = pika.PlainCredentials('test', 'test')
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', port=5672, credentials=credentials))
    channel = connection.channel()

    # 큐 선언 시 TTL 설정 5초
    ttl = 5000  
    arguments = {
        'x-message-ttl': ttl  
    }

    channel.queue_declare(queue='task_queue', durable=True, arguments=arguments)

    channel.basic_qos(prefetch_count=1)


    return connection, channel

def process_message(ch, method, properties, body):
    message_data = json.loads(body.decode())
    status = message_data["status"]
    message = message_data["message"]

    # 강제 오류 발생 테스트
    error_num = random.randint(1, 20)

    try:
        print(f"[Worker] Received: {message}, Status: {status}")
        if error_num == 10: # 5% 확률
            status = "Failed"
        else:
            status = "Success"

        if status == "Failed":
            print("--------Error 발생-------")  # Exception!
            raise Exception("Intentional error for testing")

        def task():
            # 메시지를 대문자로 변환하는 작업을 각 문자별로 쓰레드로 처리
            def uppercase_char(char):
                return char.upper()

            def thread_task(char, result, index):
                result[index] = uppercase_char(char)

            result = [''] * len(message)
            threads = []

            # 각 문자를 대문자로 바꾸는 스레드 생성
            for index, char in enumerate(message):
                thread = threading.Thread(target=thread_task, args=(char, result, index))
                threads.append(thread)
                thread.start()

            # 모든 스레드가 종료될 때까지 대기
            for thread in threads:
                thread.join()

            uppercased_message = ''.join(result)
            print(f"Uppercased Message: {uppercased_message}")

            # MongoDB에 저장
            collection.insert_one({"message": uppercased_message})
        
        task()

        # 정상적으로 메시지가 처리되었으므로 ACK 보내기
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"[Worker] Error: {e}")
        
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)  # 재처리

    time.sleep(0.5)  # TODO: Just for test, remove later


# RabbitMQ Worker
def worker():
    connection, channel = create_channel()
    channel.basic_consume(queue='task_queue', on_message_callback=process_message)
    print(f"Worker started")

    channel.start_consuming()

if __name__ == "__main__":
    worker()
