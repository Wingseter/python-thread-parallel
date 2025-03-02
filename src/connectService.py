import pika
import time
import pymongo
import os
import redis
import socket

# 환경 변수 로드 
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

MONGO_HOST = os.getenv("MONGO_HOST", "localhost")  
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))

RABBIT_HOST1 = os.getenv("RABBIT_HOST1", "localhost")  
RABBIT_PORT1 = int(os.getenv("RABBIT_PORT1", 5672))
RABBIT_HOST2 = os.getenv("RABBIT_HOST2", "localhost")  
RABBIT_PORT2 = int(os.getenv("RABBIT_PORT2", 5673))
RABBIT_HOST3 = os.getenv("RABBIT_HOST3", "localhost")  
RABBIT_PORT3 = int(os.getenv("RABBIT_PORT3", 5674))
RABBIT_USER = os.getenv("RABBITMQ_USER", "test")
RABBIT_PASS = os.getenv("RABBITMQ_PASS", "test")

# RabbitMQ 마지막 연결
last_rabbit_connection = 0 # option: 0, 1, 2

# Redis 클라이언트 설정
redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

# 작업이 완료된 task_id를 Redis에서 확인
def is_task_processed(task_id):
    return redis_client.exists(f"task:{task_id}")

# 작업 완료된 task_id를 Redis에 저장 (최대 1시간)
def mark_task_processed(task_id):
    redis_client.setex(f"task:{task_id}", 3600, "1")

def is_port_open(host, port, timeout=5):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError):
        return False

# RabbitMQ 채널 생성
def create_rabbit_channel():
    global last_rabbit_connection

    print("Waiting for RabbitMQ Connection...")
    
    credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
    connection = None

    rabbitmq_hosts = [
        (RABBIT_HOST1, RABBIT_PORT1),
        (RABBIT_HOST2, RABBIT_PORT2),
        (RABBIT_HOST3, RABBIT_PORT3),
    ]   
    
    for attempt in range(10):  # 최대 10번 재시도
        for i in range(3):
            index = (last_rabbit_connection + i) % 3
            host, port = rabbitmq_hosts[index]
            try:
                print(f"Trying to connect to RabbitMQ at {host}:{port} (Attempt {attempt+1}/10)")
                if not is_port_open(host, port, timeout=5):
                    raise Exception(f"RABBITMQ {port} is not open")
                else:
                    last_rabbit_connection = index
                
                connection = pika.BlockingConnection(pika.ConnectionParameters(host, port=port, credentials=credentials, socket_timeout=5))
                channel = connection.channel()
        
                channel.exchange_declare(exchange="dlx_exchange", exchange_type="direct", durable=True)  # DLX
                channel.queue_declare(queue="dead_letter_queue", durable=True)  # DLQ
                channel.queue_bind(queue="dead_letter_queue", exchange="dlx_exchange", routing_key="dlx_routing_key")

                # 작업 큐 선언 (TTL: 5초, DLX 적용)
                ttl = 5000  
                arguments = {
                    "x-message-ttl": ttl,
                    "x-dead-letter-exchange": "dlx_exchange",
                    "x-dead-letter-routing-key": "dlx_routing_key",
                }
                channel.queue_declare(queue="task_queue", durable=True, arguments=arguments)
                channel.basic_qos(prefetch_count=1)

                return connection, channel

            except (pika.exceptions.AMQPConnectionError, pika.exceptions.AMQPChannelError) as e:
                print("RabbitMQ connection failed, RETRYING")
                time.sleep(2)  # 2초 후 재시도
            except Exception as e:
                print(f"RabbitMQ connection failed: {e}")
                time.sleep(2)
            

# MongoDB 연결
def connect_db():
    mongo_client = pymongo.MongoClient(f"mongodb://{MONGO_HOST}:{MONGO_PORT}/")
    db = mongo_client["test_db"]
    collection = db["processed_tasks"]
    return collection
