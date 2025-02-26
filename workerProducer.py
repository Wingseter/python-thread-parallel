import pika

# RabbitMQ 연결
credentials = pika.PlainCredentials('test', 'test')
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', port=5672, credentials=credentials))
channel = connection.channel()

# 큐 선언
channel.queue_declare(queue='task_queue', durable=True)

# 메시지 전송
message = "Hello, workerNode!"
channel.basic_publish(
    exchange='',
    routing_key='task_queue',
    body=message,
    properties=pika.BasicProperties(
        delivery_mode=2,  
    )
)

print(f" [x] Sent {message}")
connection.close()
