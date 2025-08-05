import asyncio
from aioredis import from_url

async def pub():
    r = from_url("redis://localhost:6379/0", decode_responses=True)
    await r.publish("chat:42", "FastAPI+Redis Pub/Sub 테스트!")
    await r.close()

async def sub():
    r = from_url("redis://localhost:6379/0", decode_responses=True)
    pubsub = r.pubsub()
    await pubsub.subscribe("chat:42")
    async for msg in pubsub.listen():
        if msg["type"] == "message":
            print("받은 메시지 →", msg["data"])
            break
    await pubsub.unsubscribe("chat:42")
    await r.close()

async def main():
    # 구독을 먼저 실행
    task = asyncio.create_task(sub())
    # 잠시 후 발행
    await asyncio.sleep(0.1)
    await pub()
    await task

if __name__ == "__main__":
    asyncio.run(main())
