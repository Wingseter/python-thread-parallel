import time

import pika
import pika.exceptions

from timeoutBlockingConnection import TimeoutBlockingConnection
import config

# RabbitMQ 마지막 연결
last_rabbit_connection = 0 # option: 0, 1, 2

# RabbitMQ 채널 생성
def create_rabbit_channel():
    global last_rabbit_connection

    credentials = pika.PlainCredentials(config.get_rabbit_user(), config.get_rabbit_pass())
    connection = None

    rabbitmq_hosts = config.get_rabbit_hosts()

    for attempt in range(10):  # 최대 10번 재시도
        for i in range(len(rabbitmq_hosts)):  # 모든 RabbitMQ 노드를 순환하며 시도
            index = (last_rabbit_connection + i) % len(rabbitmq_hosts)
            host, port = rabbitmq_hosts[index]

            print(f"Trying to connect to RabbitMQ at {host}:{port} (Attempt {attempt+1}/10) [Node Index: {index}]")

            try:
                # 연결 시도
                connection = TimeoutBlockingConnection(
                    pika.ConnectionParameters(
                        host, port=port, credentials=credentials,
                        connection_attempts=1, socket_timeout=5, stack_timeout=5, heartbeat= 5
                    ),
                    timeout=5
                )
                channel = connection.channel()

                # DLX 설정
                setup_dead_letter_exchange(channel)

                # 작업 큐 설정
                setup_task_queue(channel)

                # 연결 성공 시 last_rabbit_connection 업데이트
                last_rabbit_connection = index

                print(f"Successfully connected to RabbitMQ at {host}:{port}. Updating last_rabbit_connection to {index}")
                return connection, channel

            except (pika.exceptions.AMQPConnectionError, pika.exceptions.AMQPChannelError, pika.exceptions.ConnectionBlockedTimeout) as e:
                print(f"RabbitMQ connection failed at {host}:{port}, retrying... ({e})")
            except Exception as e:
                print(f"Unexpected RabbitMQ error at {host}:{port}: {e}")

            time.sleep(2)

    raise Exception("Runtime Error: All RabbitMQ connection attempts failed.")

# DLX 설정
def setup_dead_letter_exchange(channel):
    channel.exchange_declare(exchange="dlx_exchange", exchange_type="direct", durable=True)
    channel.queue_declare(queue="dead_letter_queue", durable=True)
    channel.queue_bind(queue="dead_letter_queue", exchange="dlx_exchange", routing_key="dlx_routing_key")

# 작업 큐 설정
def setup_task_queue(channel):
    # 작업 큐 선언 (TTL: 5초, DLX 적용)
    ttl = 5000  
    arguments = {
        "x-message-ttl": ttl,
        "x-dead-letter-exchange": "dlx_exchange",
        "x-dead-letter-routing-key": "dlx_routing_key",
    }
    channel.queue_declare(queue="task_queue", durable=True, arguments=arguments)
    channel.basic_qos(prefetch_count=1)

