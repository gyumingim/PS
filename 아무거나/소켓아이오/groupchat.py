from fastapi import FastAPI
import socketio
import uvicorn
import time
from datetime import datetime

# 1) Socket.IO 서버 생성
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
# 2) FastAPI 앱 생성
app = FastAPI()
# 3) Socket.IO와 FastAPI 통합
app = socketio.ASGIApp(sio, app)

# 방 관리를 위한 데이터 구조
rooms = {}  # {room_id: {users: {sid: username}, created_at: timestamp}}

# 사용자별 현재 방 정보 저장
user_rooms = {}  # {sid: {room: str, username: str}}

# 타이핑 상태 관리
typing_users = {}  # {room_id: {sid: username}}

def get_timestamp():
    """현재 타임스탬프 반환"""
    return datetime.now().isoformat()

async def broadcast_user_list(room_id):
    """방의 사용자 목록 브로드캐스트"""
    if room_id in rooms:
        user_list = [{"sid": sid, "username": username} 
                    for sid, username in rooms[room_id]["users"].items()]
        await sio.emit("user_list", user_list, room=room_id)

async def clear_typing_status(room_id, sid):
    """타이핑 상태 제거"""
    if room_id in typing_users and sid in typing_users[room_id]:
        del typing_users[room_id][sid]
        
        if len(typing_users[room_id]) == 0:
            del typing_users[room_id]
        
        # 타이핑 상태 업데이트 브로드캐스트
        await broadcast_typing_status(room_id)

async def broadcast_typing_status(room_id):
    """타이핑 상태 브로드캐스트"""
    typing_list = []
    if room_id in typing_users:
        typing_list = list(typing_users[room_id].values())
    
    await sio.emit("typing_status", {"users": typing_list}, room=room_id)

# 4) 이벤트 핸들러 정의
@sio.event
async def connect(sid, environ, auth):
    print(f"Client connected: {sid}")

@sio.event
async def get_rooms(sid):
    """방 목록과 각 방의 사용자 수 반환"""
    room_list = []
    for room_id, room_data in rooms.items():
        room_list.append({
            "id": room_id,
            "name": room_id,
            "user_count": len(room_data["users"]),
            "created_at": room_data["created_at"]
        })
    await sio.emit("rooms_list", room_list, room=sid)

@sio.event
async def create_room(sid, data):
    """새 방 생성"""
    room_id = data.get("room_id", "").strip()
    
    if not room_id:
        await sio.emit("error", "방 이름을 입력해주세요.", room=sid)
        return
    
    if room_id in rooms:
        await sio.emit("error", "이미 존재하는 방입니다.", room=sid)
        return
    
    # 새 방 생성
    rooms[room_id] = {
        "users": {},
        "created_at": time.time()
    }
    
    await sio.emit("room_created", {"room_id": room_id}, room=sid)

@sio.event
async def join(sid, data):
    room = data.get("room", "").strip()
    username = data.get("username", "").strip()
    
    if not room or not username:
        await sio.emit("error", "방 ID와 닉네임을 입력해주세요.", room=sid)
        return
    
    # 방이 존재하지 않으면 생성
    if room not in rooms:
        rooms[room] = {
            "users": {},
            "created_at": time.time()
        }
    
    # 중복 닉네임 검사
    for existing_username in rooms[room]["users"].values():
        if existing_username.lower() == username.lower():
            await sio.emit("error", "이미 사용 중인 닉네임입니다.", room=sid)
            return
    
    # 사용자 정보 저장
    rooms[room]["users"][sid] = username
    user_rooms[sid] = {"room": room, "username": username}
    
    # 방에 입장
    await sio.enter_room(sid, room)
    
    # 입장 메시지 (타임스탬프 포함)
    join_message = {
        "type": "system",
        "content": f"🔵 {username}님이 입장했습니다.",
        "timestamp": get_timestamp(),
        "username": "시스템"
    }
    await sio.emit("message", join_message, room=room)
    
    await sio.emit("join_success", {"room": room, "username": username}, room=sid)
    
    # 사용자 목록 업데이트
    await broadcast_user_list(room)

@sio.event
async def message(sid, data):
    # data: { room: str, username: str, msg: str }
    room = data.get("room")
    username = data.get("username")
    msg = data.get("msg", "").strip()
    
    if not msg:
        await sio.emit("error", "메시지를 입력해주세요.", room=sid)
        return
    
    # 사용자가 해당 방에 있는지 확인
    if sid not in user_rooms or user_rooms[sid]["room"] != room:
        await sio.emit("error", "방에 입장하지 않은 상태입니다.", room=sid)
        return
    
    # 타이핑 상태 클리어
    await clear_typing_status(room, sid)
    
    # 메시지 전송 (타임스탬프 포함)
    message_data = {
        "type": "user",
        "content": msg,
        "username": username,
        "timestamp": get_timestamp(),
        "user_id": sid
    }
    await sio.emit("message", message_data, room=room)

@sio.event
async def leave(sid, data=None):
    """방 나가기"""
    if sid not in user_rooms:
        return
    
    room_info = user_rooms[sid]
    room = room_info["room"]
    username = room_info["username"]
    
    # 타이핑 상태 클리어
    await clear_typing_status(room, sid)
    
    # 방에서 사용자 제거
    if room in rooms and sid in rooms[room]["users"]:
        del rooms[room]["users"][sid]
        
        # 방에 아무도 없으면 삭제
        if len(rooms[room]["users"]) == 0:
            del rooms[room]
            # 타이핑 사용자 목록도 정리
            if room in typing_users:
                del typing_users[room]
        else:
            # 다른 사용자들에게 퇴장 알림
            leave_message = {
                "type": "system",
                "content": f"🔴 {username}님이 퇴장했습니다.",
                "timestamp": get_timestamp(),
                "username": "시스템"
            }
            await sio.emit("message", leave_message, room=room)
            
            # 사용자 목록 업데이트
            await broadcast_user_list(room)
    
    # 사용자 정보 제거
    del user_rooms[sid]
    
    # 방에서 나가기
    await sio.leave_room(sid, room)
    await sio.emit("leave_success", room=sid)

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")
    # 연결 끊어진 사용자를 방에서 제거
    await leave(sid)

@sio.event
async def typing_start(sid, data):
    """타이핑 시작"""
    if sid not in user_rooms:
        return
    
    room_info = user_rooms[sid]
    room = room_info["room"]
    username = room_info["username"]
    
    # 타이핑 사용자 추가
    if room not in typing_users:
        typing_users[room] = {}
    
    typing_users[room][sid] = username
    
    # 타이핑 상태 브로드캐스트
    await broadcast_typing_status(room)

@sio.event
async def typing_stop(sid, data):
    """타이핑 종료"""
    if sid not in user_rooms:
        return
    
    room_info = user_rooms[sid]
    room = room_info["room"]
    
    # 타이핑 상태 클리어
    await clear_typing_status(room, sid)

@sio.event
async def get_user_list(sid, data):
    """사용자 목록 요청"""
    room_id = data.get("room_id")
    if room_id and room_id in rooms:
        await broadcast_user_list(room_id)

@sio.event
async def ping(sid, data):
    """핑 이벤트 - 연결 상태 확인"""
    await sio.emit("pong", {"timestamp": get_timestamp()}, room=sid)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)