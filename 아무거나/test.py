from cmath import polar
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    # 1) 클라이언트 연결 무조건 수락
    await ws.accept()
    try:
        while True:
            # 2) 클라이언트로부터 메시지 수신
            data = await ws.receive_text()
            print(f"Received: {data}")
            # 3) 응답 전송
            await ws.send_text(f"Server says: {data[::-1]}")  # 받은 텍스트를 뒤집어서 응답
    except WebSocketDisconnect:
        print("Client disconnected")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)