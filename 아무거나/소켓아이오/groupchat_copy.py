from fastapi import fastapi
import socketio
import uvicorn

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*", logger=True, engineio_logger=True)

app = FastAPI()

app = socketio.ASGIApp(sio, app)


@sio.event
async def connect(sid, environ, auth):
    print(f"Client connected: {sid}")

@sio.event
async def join(sid, data):
    room = data.get("room")
    username = data.get("username")
    # AsyncServer 의 enter_room 은 coroutine 이므로 await
    await sio.enter_room(sid, room)
    await sio.emit("message", f"🔵 {username}님이 입장했습니다.", room=room)

@sio.event
async def message(sid, data):
    # data: { room: str, username: str, msg: str }
    room = data.get("room")
    username = data.get("username")
    msg = data.get("msg")
    await sio.emit("message", f"{username}: {msg}", room=room)

@sio.event
async def message(sid, data):
    # data: { room: str, username: str, msg: str }
    room = data.get("room")
    username = data.get("username")
    msg = data.get("msg")
    await sio.emit("message", f"{username}: {msg}", room=room)

@sio.event
async def leave(sid, data):
    room = data.get("room")
    username = data.get("username")
    await sio.emit("message", f"🔴 {username}님이 퇴장했습니다.", room=room)
    await sio.leave_room(sid, room)

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)