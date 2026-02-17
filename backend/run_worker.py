import sys
import os

# Add backend to path
sys.path.insert(0, "/home/shravyashanbhogue/prod/coolStufs/faysal/backend")

from rq import Worker, Queue
from redis import Redis

redis_conn = Redis.from_url("redis://localhost:6379/0")

if __name__ == "__main__":
    queue = Queue(connection=redis_conn)
    worker = Worker([queue], connection=redis_conn)
    worker.work()
