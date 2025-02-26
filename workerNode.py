import pika
import pymongo

# MongoDB 연결
mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
db = mongo_client["test_db"]
collection = db["processed_tasks"]

# RabbitMQ 연결
credentials = pika.PlainCredentials('test', 'test')
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', port=5672, credentials=credentials))
channel = connection.channel()

channel.queue_declare(queue='task_queue', durable=True)

# 메시지 처리 함수
def callback(ch, method, properties, body):
    message = body.decode()
    print(f"Received {message}")

    # MongoDB에 저장
    collection.insert_one({"message": message})
    print(f"Saved to MongoDB: {message}")

    # ACK 보내기
    ch.basic_ack(delivery_tag=method.delivery_tag)

# 소비자 설정
channel.basic_qos(prefetch_count=1)  # 한 번에 하나의 메시지만 처리
channel.basic_consume(queue='task_queue', on_message_callback=callback)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
