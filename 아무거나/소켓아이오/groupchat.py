from fastapi import FastAPI, Request
import socketio
import uvicorn

# 1) Socket.IO 서버 생성
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*", logger=True, engineio_logger=True)
# 2) FastAPI 앱 생성
app = FastAPI()
# 3) Socket.IO와 FastAPI 통합
app = socketio.ASGIApp(sio, app)

# 4) 이벤트 핸들러 정의
@sio.event
async def connect(sid, environ, auth):
    # python-socketio v5 이상: connect(sid, environ, auth)
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