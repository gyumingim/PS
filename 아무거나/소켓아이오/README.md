# 💬 BABA CHAT - 페이지별 분리 구조

## 📁 파일 구조

```
아무거나/소켓아이오/
├── index.html       # 메인 엔트리 (자동으로 rooms.html로 리다이렉트)
├── rooms.html       # 🏠 방 선택 페이지
├── join.html        # 👤 닉네임 입력 페이지
├── chat.html        # 💬 채팅 페이지
├── style.css        # 🎨 공통 스타일시트
├── script.js        # ⚙️ JavaScript (사용하지 않음 - 각 페이지에 인라인)
└── groupchat.py     # 🔧 서버 (백엔드)
```

## 🌊 페이지 플로우

```
index.html → rooms.html → join.html → chat.html
    ↓           ↓            ↓           ↓
  시작페이지   방 선택      닉네임 입력   채팅하기
```

## 📄 각 페이지 설명

### 1. `index.html` - 메인 시작 페이지
- 자동으로 `rooms.html`로 리다이렉트
- 사용자가 직접 방문하는 첫 페이지

### 2. `rooms.html` - 방 선택 페이지
- 생성된 채팅방 목록 표시
- 새로운 방 만들기 기능
- 방 클릭 시 `join.html?room=방이름`으로 이동

### 3. `join.html` - 닉네임 입력 페이지
- URL 파라미터에서 방 이름 받음
- 닉네임 입력 후 서버에 join 요청
- 입장 성공 시 `chat.html?room=방이름&username=닉네임`으로 이동

### 4. `chat.html` - 채팅 페이지
- URL 파라미터에서 방 이름과 닉네임 받음
- 실시간 채팅 기능
- 사용자 목록, 타이핑 표시, 이모지, 검색 등 모든 채팅 기능

## 🔄 페이지 간 이동

### URL 파라미터 전달
- `join.html?room=방이름`
- `chat.html?room=방이름&username=닉네임`

### JavaScript 이동
```javascript
// 방 선택 → 닉네임 입력
window.location.href = `join.html?room=${encodeURIComponent(roomId)}`;

// 닉네임 입력 → 채팅
window.location.href = `chat.html?room=${encodeURIComponent(data.room)}&username=${encodeURIComponent(data.username)}`;

// 채팅 → 방 선택 (나가기)
window.location.href = 'rooms.html';
```

## 🎯 장점

### ✅ **명확한 분리**
- 각 페이지가 독립적인 기능
- 코드 유지보수 쉬움
- 디버깅 용이

### ✅ **SEO 친화적**
- 각 페이지별 고유 URL
- 브라우저 뒤로가기 정상 작동
- 북마크 가능

### ✅ **로딩 최적화**
- 필요한 기능만 로드
- 채팅 페이지에서만 복잡한 JavaScript 로드

### ✅ **사용자 경험**
- 브라우저 새로고침 시 상태 유지
- URL 공유 가능

## 🚀 사용 방법

1. **서버 시작**
   ```bash
   python groupchat.py
   ```

2. **브라우저 접속**
   ```
   http://localhost:8000/
   ```

3. **플로우 따라하기**
   - 방 선택 또는 새 방 만들기
   - 닉네임 입력
   - 채팅 시작!

## 🔧 개발자 정보

각 HTML 파일은 독립적인 JavaScript를 포함하고 있어서 `script.js` 파일은 실제로 사용되지 않습니다. 
모든 기능은 각 페이지의 인라인 스크립트로 구현되어 있습니다.

**공통 스타일은 `style.css`에서 관리됩니다.**