import pika
import time
import json
import uuid

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
arguments = { 'x-message-ttl': ttl }
channel.queue_declare(queue='task_queue', durable=True, arguments=arguments)
channel.basic_qos(prefetch_count=1)


# 메시지 전송
def send_messages(num_messages=10):
    for i in range(1, num_messages + 1):
        task_id = str(uuid.uuid4())
        message = f"Message {i}"
        status = "Not Processed"

        message_body = json.dumps({"task_id": task_id, "status": status, "message": message})
        
        try:
            channel.basic_publish(
                exchange='',
                routing_key='task_queue',
                body=message_body,
                properties=pika.BasicProperties(
                    delivery_mode=2,  
                )
            )

            print(f"Sent: {message_body}")
        except Exception as e:
            print(f"Error sending message {message}: {e}")

        time.sleep(0.5)  

    print("모든 메시지 전송 완료")
    connection.close()

if __name__ == "__main__":
    send_messages(num_messages=987654321)