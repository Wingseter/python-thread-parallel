import pika
import time
import pymongo
import requests
import os
import redis

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

# 작업이 완료된 task_id를 Redis에서 확인
def is_task_processed(task_id):
    return redis_client.exists(f"task:{task_id}")

# 작업 완료된 task_id를 Redis에 저장 (최대 1시간)
def mark_task_processed(task_id):
    redis_client.setex(f"task:{task_id}", 3600, "1")  

def create_rabbit_channel():
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
    
    # Dead Letter Exchange 선언
    channel.exchange_declare(exchange='dlx_exchange', exchange_type='direct', durable=True) # DLX
    channel.queue_declare(queue='dead_letter_queue', durable=True) # DLQ
    # DLX와 DLQ 바인딩
    channel.queue_bind(queue='dead_letter_queue', exchange='dlx_exchange', routing_key='dlx_routing_key')


    # 큐 선언 시 TTL 설정 5초
    ttl = 5000  
    arguments = { 
        'x-message-ttl': ttl,
        'x-dead-letter-exchange': 'dlx_exchange',  
        'x-dead-letter-routing-key': 'dlx_routing_key'  
    }

    channel.queue_declare(queue='task_queue', durable=True, arguments=arguments)
    channel.basic_qos(prefetch_count=1)

    return connection, channel

def connect_db():
    # MongoDB 연결
    mongo_client = pymongo.MongoClient("mongodb://db:27017/")
    db = mongo_client["test_db"]
    collection = db["processed_tasks"]

    return collection
