import pika
import time
import json
import uuid
from connectService import create_channel

connection, channel = create_channel()

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
            print(f"메시지 보내기 실패 {message}: {e}")

        time.sleep(0.5)  

    print("모든 메시지 전송 완료")
    connection.close()

if __name__ == "__main__":
    send_messages(num_messages=987654321)