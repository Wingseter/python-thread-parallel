import redis
import config

# Redis 클라이언트 설정
redis_client = redis.StrictRedis(
    host=config.get_redis_host(), 
    port=config.get_redis_port(), 
    db=0, 
    decode_responses=True
)

# 작업이 완료된 task_id를 Redis에서 확인
def is_task_processed(task_id):
    return redis_client.exists(f"task:{task_id}")

# 작업 완료된 task_id를 Redis에 저장 (최대 1시간)
def mark_task_processed(task_id):
    redis_client.setex(f"task:{task_id}", 3600, "1")