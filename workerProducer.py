import pika
import time

# RabbitMQ 연결
credentials = pika.PlainCredentials('test', 'test')
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', port=5672, credentials=credentials))
channel = connection.channel()

# 큐 선언
channel.queue_declare(queue='task_queue', durable=True)

# 메시지 전송
def send_messages(num_messages=10):
    for i in range(1, num_messages + 1):
        message = f"Task {i}"
        
        channel.basic_publish(
            exchange='',
            routing_key='task_queue',
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,  
            )
        )
        
        print(f"Sent: {message}")
        time.sleep(0.5)  # TODO Delete Just for test

    print("모든 메시지 전송 완료")
    connection.close()

send_messages(num_messages=20)