import os

def get_redis_host():
    return os.getenv("REDIS_HOST", "localhost")

def get_redis_port():
    return int(os.getenv("REDIS_PORT", 6379))

def get_mongo_host():
    return os.getenv("MONGO_HOST", "localhost")

def get_mongo_port():
    return int(os.getenv("MONGO_PORT", 27017))

def get_rabbit_hosts():
    return [
        (os.getenv("RABBIT_HOST1", "localhost"), int(os.getenv("RABBIT_PORT1", 5672))),
        (os.getenv("RABBIT_HOST2", "localhost"), int(os.getenv("RABBIT_PORT2", 5673))),
        (os.getenv("RABBIT_HOST3", "localhost"), int(os.getenv("RABBIT_PORT3", 5674)))
    ]

def get_rabbit_user():
    return os.getenv("RABBITMQ_USER", "test")

def get_rabbit_pass():
    return os.getenv("RABBITMQ_PASS", "test")

def get_worker_id():
    return os.getenv("WORKER_ID", "default")

def get_worker_port():
    return os.getenv("WORKER_PORT", "8001")

def get_loki_url():
    return os.getenv("LOKI_URL", "http://localhost:3100/loki/api/v1/push")