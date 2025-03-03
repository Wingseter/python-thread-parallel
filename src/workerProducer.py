import time
import json
import uuid

import pika

from rabbitmqHandler import create_rabbit_channel


# 메시지 전송
def send_messages(num_messages=10):
    for i in range(1, num_messages + 1):
        # 고유 ID 생성
        task_id = str(uuid.uuid4())

        # 메시지 생성
        message = f"Message {i}"
        status = "Not Processed"
        message_body = json.dumps({"task_id": task_id, "status": status, "message": message})
        
        try:
            # 새로운 RabbitMQ 연결
            connection, channel = create_rabbit_channel()

            channel.basic_publish(
                exchange='',
                routing_key='task_queue',
                body=message_body,
                properties=pika.BasicProperties(
                    delivery_mode=2,  
                )
            )

            print(f"Sent: {message_body}")
            connection.close()
        except pika.exceptions.AMQPConnectionError:
            print("error RabbitMQ connection failed. Retrying...")
            time.sleep(5)
        except Exception as e:
            print(f"Send message failed {message}: {e}")
            time.sleep(5)

        time.sleep(0.5)  

    # 모든 메시지 전송 완료
    print("All Message Sent Successfully")
    connection.close()

if __name__ == "__main__":
    send_messages(num_messages=987654321) # 메시지를 계속 전송