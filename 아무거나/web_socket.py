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
    # "reload" 옵션은 CLI에서 실행할 때 사용하는 편이 안전합니다.
    # 스크립트 내부에서 reload=True 를 주면 Windows에서 포트 충돌(WinError 10013)이 발생합니다.
    # 필요하면 터미널에서 `uvicorn 아무거나.web_socket:app --reload` 형태로 실행하세요.

    # 여기서는 직접 FastAPI 인스턴스를 넘겨 간단히 실행합니다.
    uvicorn.run(app, host="0.0.0.0", port=8002)