import pika
import time
import pymongo
import requests

def create_channel():
    print("Waiting for RabbitMQ Connection...")
    # RabbitMQ 연결
    credentials = pika.PlainCredentials('test', 'test')
    for _ in range(10):  # 최대 10번 재시도
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters('rabbit', port=5672, credentials=credentials))
            break  
        except pika.exceptions.AMQPConnectionError:
            print("RabbitMQ connection failed, RETRYING")
            time.sleep(5)  # 5초 후 재시도

    channel = connection.channel()
    # 큐 선언 시 TTL 설정 5초
    ttl = 5000  
    arguments = { 'x-message-ttl': ttl  }

    channel.queue_declare(queue='task_queue', durable=True, arguments=arguments)
    channel.basic_qos(prefetch_count=1)
    return connection, channel

def connect_db():
    # MongoDB 연결
    mongo_client = pymongo.MongoClient("mongodb://db:27017/")
    db = mongo_client["test_db"]
    collection = db["processed_tasks"]

    return collection
