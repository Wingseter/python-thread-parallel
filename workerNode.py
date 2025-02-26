import pika
import pymongo
from concurrent.futures import ThreadPoolExecutor
import threading

# MongoDB 연결
mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
db = mongo_client["test_db"]
collection = db["processed_tasks"]


def create_channel():
    credentials = pika.PlainCredentials('test', 'test')
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', port=5672, credentials=credentials))
    channel = connection.channel()
    channel.queue_declare(queue='task_queue', durable=True)

    channel.basic_qos(prefetch_count=1)

    return connection, channel

# 메시지 처리 함수 
def process_message(ch, method, properties, body):
    message = body.decode()
    print(f"[Worker] Received: {message}")

    def task():
        # 메시지를 대문자로 변환하는 작업을 각 문자별로 스레드
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


        for thread in threads:
            thread.join()

        uppercased_message = ''.join(result)
        print(f"Uppercased Message: {uppercased_message}")

        collection.insert_one({"message": message})
        print(f"Saved to MongoDB: {message}")
    
    task()

    # ACK 보내기
    ch.basic_ack(delivery_tag=method.delivery_tag)

# RabbitMQ Worker
def worker():
    connection, channel = create_channel()
    channel.basic_consume(queue='task_queue', on_message_callback=process_message)
    print(f"Worker started")

    channel.start_consuming()

if __name__ == "__main__":
    worker()
