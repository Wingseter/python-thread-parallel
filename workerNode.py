import pika
import pymongo
from concurrent.futures import ThreadPoolExecutor

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
        # TODO 멀티 프로세스 활동 하기
        pass

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
