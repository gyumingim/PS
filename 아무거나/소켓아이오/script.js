let socket;
let currentRoom = null;
let currentUsername = null;
let currentUserId = null;
let typingTimer = null;
let isTyping = false;
let soundEnabled = true;
let messageOffset = 0;
let selectedReactionMessageId = null;
let allUsers = [];
let mentionIndex = -1;
let filteredUsers = [];
let lastScreen = 'roomSelectScreen';

// 이모지 목록 (확장됨)
const emojis = [
  '😀', '😃', '😄', '😁', '😆', '😅', '😂', '🤣',
  '😊', '😇', '🙂', '🙃', '😉', '😌', '😍', '🥰',
  '😘', '😗', '😙', '😚', '😋', '😛', '😝', '😜',
  '🤪', '🤨', '🧐', '🤓', '😎', '🤩', '🥳', '😏',
  '😒', '😞', '😔', '😟', '😕', '🙁', '☹️', '😣',
  '😖', '😫', '😩', '🥺', '😢', '😭', '😤', '😠',
  '😡', '🤬', '🤯', '😳', '🥵', '🥶', '😱', '😨',
  '😰', '😥', '😓', '🤗', '🤔', '🤭', '🤫', '🤥',
  '👋', '🤚', '🖐', '✋', '🖖', '👌', '🤌', '🤏',
  '✌️', '🤞', '🤟', '🤘', '🤙', '👈', '👉', '👆',
  '👇', '☝️', '👍', '👎', '👊', '✊', '🤛', '🤜',
  '👏', '🙌', '👐', '🤲', '🤝', '🙏', '💪', '🦾',
  '❤️', '🧡', '💛', '💚', '💙', '💜', '🤎', '🖤',
  '🤍', '💔', '❣️', '💕', '💖', '💗', '💘', '💝',
  '💞', '💟', '🔥', '✨', '💫', '⭐', '🌟', '💥',
  '💯', '💢', '💨', '💦', '💤', '🎉', '🎊', '🎈',
  '🎁', '🎀', '🎂', '🎄', '🎆', '🎇', '🧨', '✨',
  '🎃', '🎗️', '🥇', '🥈', '🥉', '🏆', '📢', '⚡',
  '🔔', '🔕', '🎵', '🎶', '💬', '💭', '🗯️', '💡',
  '🚀', '🛸', '🌍', '🌎', '🌏', '🌕', '🌖', '🌗'
];

// 빠른 반응 이모지
const quickReactions = ['👍', '❤️', '😂', '😮', '😢', '😡'];

// 초기화
document.addEventListener('DOMContentLoaded', () => {
  initializeEmojiPicker();
  connectSocket();
  setupEventListeners();
  loadTheme();
  
  // 기본 화면 표시 (히스토리 관리 없이)
  showScreen('roomSelectScreen', false);
  
  // 텍스트 영역 자동 크기 조정
  const msgInput = document.getElementById('msgInput');
  msgInput.addEventListener('input', autoResizeTextarea);
});

// Socket.IO 연결
function connectSocket() {
  if (socket) return;
  
  try {
    socket = io('http://localhost:8000', {
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5,
      timeout: 20000
    });

    socket.on('connect', () => {
      console.log('🔗 서버에 연결됨');
      hideConnectionError();
      updateConnectionStatus('connected');
      socket.emit('get_rooms');
    });

    socket.on('connect_error', (error) => {
      console.error('❌ 연결 실패:', error);
      updateConnectionStatus('error');
      showConnectionError('서버에 연결할 수 없습니다. 서버가 실행중인지 확인해주세요.');
    });

    socket.on('disconnect', (reason) => {
      console.log('❌ 서버 연결 끊김:', reason);
      updateConnectionStatus('disconnected');
      if (reason === 'io server disconnect') {
        // 서버에서 연결을 끊은 경우 재연결 시도
        socket.connect();
      }
    });
  } catch (error) {
    console.error('❌ Socket.IO 초기화 실패:', error);
    showConnectionError('연결 초기화에 실패했습니다.');
  }
  
  socket.on('rooms_list', (rooms) => {
    updateRoomsList(rooms);
  });

  socket.on('room_created', (data) => {
    console.log('🏠 방 생성됨:', data.room_id);
    document.getElementById('newRoomInput').value = '';
    updateCharCounter('newRoomInput', 'roomCharCounter', 30);
    showSuccess('createRoomError', '방이 성공적으로 생성되었습니다!');
  });

  socket.on('join_success', (data) => {
    try {
      console.log('✅ 방 입장 성공:', data);
      
      currentRoom = data.room;
      currentUsername = data.username;
      currentUserId = socket.id;
      
      // UI 업데이트
      const roomNameEl = document.getElementById('currentRoomName');
      const userNameEl = document.getElementById('currentUserName');
      const msgInput = document.getElementById('msgInput');
      const sendBtn = document.getElementById('sendBtn');
      const messagesEl = document.getElementById('messages');
      const searchToggle = document.querySelector('.search-toggle');
      
      if (roomNameEl) roomNameEl.textContent = currentRoom;
      if (userNameEl) userNameEl.textContent = currentUsername;
      if (msgInput) msgInput.disabled = false;
      if (sendBtn) sendBtn.disabled = false;
      if (messagesEl) messagesEl.innerHTML = '';
      if (searchToggle) searchToggle.style.display = 'block';
      
      messageOffset = 0;
      showScreen('chatScreen');
      
      // 사용자 목록 요청
      if (socket && socket.connected) {
        socket.emit('get_user_list', { room_id: currentRoom });
      }
      
      console.log('🎉 채팅방 UI 초기화 완료');
    } catch (error) {
      console.error('❌ 방 입장 처리 에러:', error);
      showError('joinError', '방 입장 처리 중 오류가 발생했습니다.');
    }
  });

  socket.on('message_history', (history) => {
    // 히스토리 메시지들을 순서대로 추가
    history.forEach(msg => addMessageToDOM(msg, false));
    scrollToBottom();
  });

  socket.on('leave_success', () => {
    console.log('✅ 방 나가기 성공');
    
    // 상태 초기화
    currentRoom = null;
    currentUsername = null;
    currentUserId = null;
    
    // UI 초기화
    const msgInput = document.getElementById('msgInput');
    const sendBtn = document.getElementById('sendBtn');
    const searchToggle = document.querySelector('.search-toggle');
    
    if (msgInput) msgInput.disabled = true;
    if (sendBtn) sendBtn.disabled = true;
    if (searchToggle) searchToggle.style.display = 'none';
    
    clearTypingIndicator();
    
    // 방 선택 화면으로 이동
    showScreen('roomSelectScreen');
  });

  socket.on('message', (data) => {
    addMessage(data);
    
    // 알림 사운드 재생 (자신의 메시지가 아닌 경우)
    if (data.type === 'user' && data.user_id !== currentUserId && soundEnabled) {
      playNotificationSound();
    }
  });

  socket.on('user_list', (users) => {
    allUsers = users;
    updateUserList(users);
  });

  socket.on('typing_status', (data) => {
    updateTypingIndicator(data.users);
  });

  socket.on('search_results', (data) => {
    displaySearchResults(data.results, data.query);
  });

  socket.on('more_messages', (data) => {
    if (data.messages.length > 0) {
      const messagesContainer = document.getElementById('messages');
      const oldScrollHeight = messagesContainer.scrollHeight;
      
      // 메시지들을 맨 위에 추가
      data.messages.reverse().forEach(msg => {
        addMessageToDOM(msg, true);
      });
      
      // 스크롤 위치 유지
      messagesContainer.scrollTop = messagesContainer.scrollHeight - oldScrollHeight;
      messageOffset = data.offset;
    } else {
      document.getElementById('loadMoreBtn').style.display = 'none';
    }
  });

  socket.on('reaction_updated', (data) => {
    updateMessageReactions(data.message_id, data.reactions);
  });

  socket.on('mention_notification', (data) => {
    showMentionNotification(data);
  });

  socket.on('error', (message) => {
    const activeScreen = document.querySelector('.screen.active').id;
    let errorElementId = 'createRoomError';
    
    if (activeScreen === 'nameInputScreen') {
      errorElementId = 'joinError';
    }
    
    showError(errorElementId, message);
  });

  socket.on('disconnect', () => {
    console.log('❌ 서버 연결 끊김');
  });
}

// 화면 전환 함수들 (단순화됨)
function showScreen(screenId, addToHistory = false) {
  // 같은 화면으로 전환 시도하는 경우 무시
  if (lastScreen === screenId && document.getElementById(screenId)?.classList.contains('active')) {
    return;
  }
  
  console.log('📱 화면 전환:', screenId);
  
  // 현재 화면 숨기기
  document.querySelectorAll('.screen').forEach(screen => {
    screen.classList.remove('active');
  });
  
  // 새 화면 표시
  const targetScreen = document.getElementById(screenId);
  if (targetScreen) {
    targetScreen.classList.add('active');
    lastScreen = screenId;
    
    // 화면별 추가 처리
    handleScreenTransition(screenId);
  } else {
    console.error('❌ 화면을 찾을 수 없음:', screenId);
  }
}

// 화면 전환 시 추가 처리
function handleScreenTransition(screenId) {
  switch (screenId) {
    case 'nameInputScreen':
      // 닉네임 입력창 포커스
      setTimeout(() => {
        const nameInput = document.getElementById('nameInput');
        if (nameInput) nameInput.focus();
      }, 100);
      break;
    case 'chatScreen':
      // 메시지 입력창 포커스
      setTimeout(() => {
        const msgInput = document.getElementById('msgInput');
        if (msgInput && !msgInput.disabled) msgInput.focus();
      }, 100);
      break;
  }
}

function showError(elementId, message) {
  const errorElement = document.getElementById(elementId);
  errorElement.textContent = message;
  errorElement.className = 'error';
  errorElement.style.display = 'block';
  setTimeout(() => {
    errorElement.style.display = 'none';
  }, 5000);
}

function showSuccess(elementId, message) {
  const element = document.getElementById(elementId);
  element.textContent = message;
  element.className = 'success';
  element.style.display = 'block';
  setTimeout(() => {
    element.style.display = 'none';
  }, 3000);
}

function showConnectionError(message) {
  // 연결 에러 표시
  let errorDiv = document.getElementById('connectionError');
  if (!errorDiv) {
    errorDiv = document.createElement('div');
    errorDiv.id = 'connectionError';
    errorDiv.style.cssText = `
      position: fixed;
      top: 80px;
      left: 50%;
      transform: translateX(-50%);
      background: var(--danger-color);
      color: white;
      padding: 15px 25px;
      border-radius: 10px;
      z-index: 2000;
      box-shadow: var(--shadow-lg);
      animation: slideInRoom 0.3s ease-out;
    `;
    document.body.appendChild(errorDiv);
  }
  errorDiv.textContent = message;
  errorDiv.style.display = 'block';
}

function hideConnectionError() {
  const errorDiv = document.getElementById('connectionError');
  if (errorDiv) {
    errorDiv.style.display = 'none';
  }
}

function updateConnectionStatus(status) {
  const statusDiv = document.getElementById('connectionStatus');
  if (!statusDiv) return;
  
  switch (status) {
    case 'connected':
      statusDiv.textContent = '🟢 연결됨';
      statusDiv.style.background = 'var(--success-color)';
      break;
    case 'disconnected':
      statusDiv.textContent = '🔴 연결 끊김';
      statusDiv.style.background = 'var(--danger-color)';
      break;
    case 'error':
      statusDiv.textContent = '⚠️ 연결 오류';
      statusDiv.style.background = 'var(--danger-color)';
      break;
    default:
      statusDiv.textContent = '🟡 연결 중...';
      statusDiv.style.background = 'var(--warning-color)';
  }
}

// 방 나가기 처리 (단순화)
function handleLeaveRoom() {
  console.log('🚪 방 나가기 처리');
  
  // 상태 초기화
  currentRoom = null;
  currentUsername = null;
  currentUserId = null;
  
  // UI 초기화
  const msgInput = document.getElementById('msgInput');
  const sendBtn = document.getElementById('sendBtn');
  const searchToggle = document.querySelector('.search-toggle');
  
  if (msgInput) {
    msgInput.disabled = true;
    msgInput.value = '';
  }
  if (sendBtn) sendBtn.disabled = true;
  if (searchToggle) searchToggle.style.display = 'none';
  
  // 메시지 영역 초기화
  const messagesEl = document.getElementById('messages');
  if (messagesEl) messagesEl.innerHTML = '';
  
  clearTypingIndicator();
  
  // 방 선택 화면으로 이동
  showScreen('roomSelectScreen');
}

// 방 목록 업데이트 (단순화)
function updateRoomsList(rooms) {
  const roomsList = document.getElementById('roomsList');
  if (!roomsList) return;
  
  if (rooms.length === 0) {
    roomsList.innerHTML = `
      <div class="empty-rooms">
        <div class="icon">🏠</div>
        <h3>방이 없어요!</h3>
        <p>새로운 방을 만들어서 친구들과 수다 떨어요~</p>
      </div>
    `;
    return;
  }

  roomsList.innerHTML = rooms.map(room => `
    <div class="room-item" onclick="selectRoom('${room.id}')">
      <div class="room-info">
        <h3>💬 ${escapeHtml(room.name)}</h3>
        <p>📅 생성일: ${new Date(room.created_at * 1000).toLocaleString()}</p>
      </div>
      <div class="user-count">${room.user_count}명</div>
    </div>
  `).join('');
}

// 사용자 목록 업데이트 (단순화)
function updateUserList(users) {
  const userList = document.getElementById('userList');
  const userCount = document.getElementById('userCount');
  
  if (!userList || !userCount) return;
  
  userCount.textContent = users.length;
  
  userList.innerHTML = users.map(user => `
    <div class="user-item" onclick="mentionUser('${escapeHtml(user.username)}')">
      <div class="user-avatar">${getUserInitial(user.username)}</div>
      <div>
        <div class="user-name">${escapeHtml(user.username)}</div>
        <div class="user-status">온라인</div>
      </div>
    </div>
  `).join('');
}

// 메시지 추가
function addMessage(data) {
  addMessageToDOM(data, false);
  
  // 멘션 확인
  if (data.type === 'user' && data.content.includes(`@${currentUsername}`)) {
    const messagesContainer = document.getElementById('messages');
    const lastMessage = messagesContainer.lastElementChild;
    if (lastMessage) {
      lastMessage.classList.add('mention');
    }
  }
  
  scrollToBottom();
}

function addMessageToDOM(data, prepend = false) {
  const messages = document.getElementById('messages');
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${data.type}`;
  messageDiv.dataset.messageId = data.id;
  
  // 자신의 메시지인지 확인
  if (data.type === 'user' && data.user_id === currentUserId) {
    messageDiv.classList.add('own');
  }
  
  let timestamp;
  if (data.timestamp) {
    if (data.timestamp.includes('T')) {
      // ISO 형식
      timestamp = new Date(data.timestamp).toLocaleTimeString('ko-KR', {
        hour: '2-digit',
        minute: '2-digit'
      });
    } else {
      // 타임스탬프
      timestamp = new Date(data.timestamp * 1000).toLocaleTimeString('ko-KR', {
        hour: '2-digit',
        minute: '2-digit'
      });
    }
  } else {
    timestamp = new Date().toLocaleTimeString('ko-KR', {
      hour: '2-digit',
      minute: '2-digit'
    });
  }
  
  let headerContent = '';
  if (data.type === 'user') {
    headerContent = `
      <span class="message-username">${escapeHtml(data.username)}</span>
      <span class="message-timestamp">${timestamp}</span>
    `;
  } else if (data.type === 'system') {
    headerContent = `<span class="message-timestamp">${timestamp}</span>`;
  }
  
  // 멘션 처리
  let processedContent = escapeHtml(data.content);
  if (data.type === 'user') {
    processedContent = processedContent.replace(/@(\w+)/g, '<span style="color: var(--mention-color); font-weight: bold;">@$1</span>');
  }
  
  let actionsHTML = '';
  if (data.type === 'user' && data.id) {
    actionsHTML = `
      <div class="message-actions">
        <button class="reaction-btn" onclick="openReactionModal(${data.id})" title="반응">👍</button>
      </div>
    `;
  }
  
  messageDiv.innerHTML = `
    <div class="message-header">${headerContent}</div>
    <div class="message-content">${processedContent}</div>
    <div class="message-reactions" id="reactions-${data.id}"></div>
    ${actionsHTML}
  `;
  
  if (prepend && messages.children.length > 1) {
    // 로드 모어 버튼 다음에 삽입
    messages.insertBefore(messageDiv, messages.children[1]);
  } else {
    messages.appendChild(messageDiv);
  }
  
  // 첫 번째 메시지가 아니라면 더 보기 버튼 표시
  if (messages.children.length > 1) {
    document.getElementById('loadMoreBtn').style.display = 'block';
  }
}

// 메시지 반응 업데이트
function updateMessageReactions(messageId, reactions) {
  const reactionsContainer = document.getElementById(`reactions-${messageId}`);
  if (!reactionsContainer) return;
  
  if (Object.keys(reactions).length === 0) {
    reactionsContainer.innerHTML = '';
    return;
  }
  
  reactionsContainer.innerHTML = Object.entries(reactions).map(([reaction, count]) => `
    <div class="reaction" onclick="toggleReaction(${messageId}, '${reaction}')">
      <span>${reaction}</span>
      <span>${count}</span>
    </div>
  `).join('');
}

// 타이핑 표시 업데이트
function updateTypingIndicator(typingUsers) {
  const indicator = document.getElementById('typingIndicator');
  const typingText = document.getElementById('typingText');
  
  if (!indicator || !typingText) return;
  
  // 자신은 제외
  const otherTypingUsers = typingUsers.filter(user => user !== currentUsername);
  
  if (otherTypingUsers.length === 0) {
    indicator.classList.add('hidden');
    return;
  }
  
  let newText = '';
  if (otherTypingUsers.length === 1) {
    newText = `${otherTypingUsers[0]}님이 입력 중`;
  } else if (otherTypingUsers.length === 2) {
    newText = `${otherTypingUsers[0]}님과 ${otherTypingUsers[1]}님이 입력 중`;
  } else {
    newText = `${otherTypingUsers[0]}님 외 ${otherTypingUsers.length - 1}명이 입력 중`;
  }
  
  typingText.textContent = newText;
  indicator.classList.remove('hidden');
}

function clearTypingIndicator() {
  document.getElementById('typingIndicator').classList.add('hidden');
}

// 방 선택
function selectRoom(roomId) {
  try {
    if (!roomId || roomId.trim() === '') {
      showError('createRoomError', '유효하지 않은 방 이름입니다.');
      return;
    }
    
    currentRoom = roomId;
    document.getElementById('selectedRoomName').textContent = roomId;
    showScreen('nameInputScreen');
    document.getElementById('nameInput').focus();
    
    // 이전 에러 메시지 초기화
    document.getElementById('joinError').style.display = 'none';
  } catch (error) {
    console.error('❌ 방 선택 에러:', error);
    showError('createRoomError', '방 선택 중 오류가 발생했습니다.');
  }
}

// 방 생성
function createRoom() {
  try {
    const roomName = document.getElementById('newRoomInput').value.trim();
    console.log('🏠 방 생성 시도:', { roomName, connected: socket?.connected });
    
    if (!roomName) {
      showError('createRoomError', '방 이름을 입력해주세요.');
      return;
    }
    
    if (!socket || !socket.connected) {
      showError('createRoomError', '서버에 연결되지 않았습니다. 페이지를 새로고침해주세요.');
      return;
    }
    
    console.log('🏠 방 생성 요청 전송:', roomName);
    socket.emit('create_room', { room_id: roomName });
    
    // 버튼 비활성화 (중복 요청 방지)
    const btn = event?.target || document.querySelector('button[type="submit"]');
    if (btn) {
      btn.disabled = true;
      btn.textContent = '생성 중...';
      setTimeout(() => {
        btn.disabled = false;
        btn.textContent = '🏠 만들기!';
      }, 2000);
    }
  } catch (error) {
    console.error('❌ 방 생성 에러:', error);
    showError('createRoomError', '방 생성 중 오류가 발생했습니다.');
  }
}

// 방 입장
function joinRoom() {
  try {
    const username = document.getElementById('nameInput').value.trim();
    console.log('🚀 방 입장 시도:', { 
      room: currentRoom, 
      username: username, 
      connected: socket?.connected,
      currentState: { currentRoom, currentUsername, currentUserId }
    });
    
    if (!username) {
      showError('joinError', '닉네임을 입력해주세요.');
      return;
    }
    
    if (!currentRoom) {
      showError('joinError', '선택된 방이 없습니다.');
      return;
    }
    
    if (!socket || !socket.connected) {
      showError('joinError', '서버에 연결되지 않았습니다. 페이지를 새로고침해주세요.');
      return;
    }
    
    console.log('🚀 방 입장 요청 전송:', { room: currentRoom, username: username });
    socket.emit('join', { room: currentRoom, username: username });
    
    // 버튼 비활성화 (중복 요청 방지)
    const btn = event?.target || document.querySelector('button[type="submit"]');
    if (btn) {
      btn.disabled = true;
      btn.textContent = '입장 중...';
      setTimeout(() => {
        btn.disabled = false;
        btn.textContent = '📞 들어가기!';
      }, 3000);
    }
  } catch (error) {
    console.error('❌ 방 입장 에러:', error);
    showError('joinError', '방 입장 중 오류가 발생했습니다.');
  }
}

// 방 나가기
function leaveRoom() {
  console.log('🚪 방 나가기 버튼 클릭');
  
  if (socket && socket.connected && currentRoom) {
    // 서버에 방 나가기 요청
    socket.emit('leave');
  } else {
    // 연결이 끊어진 경우 직접 처리
    handleLeaveRoom();
  }
}

// 메시지 전송
function sendMessage() {
  const msgInput = document.getElementById('msgInput');
  const message = msgInput.value.trim();
  if (!message || !currentRoom || !currentUsername) return;

  socket.emit('message', {
    room: currentRoom,
    username: currentUsername,
    msg: message
  });
  
  msgInput.value = '';
  autoResizeTextarea({ target: msgInput });
  updateCharCounter('msgInput', 'msgCharCounter', 500);
  
  // 타이핑 상태 중지
  if (isTyping) {
    socket.emit('typing_stop', {});
    isTyping = false;
  }
}

// 검색 기능
function toggleSearchPanel() {
  const panel = document.getElementById('searchPanel');
  panel.classList.toggle('active');
  
  if (panel.classList.contains('active')) {
    document.getElementById('searchInput').focus();
  }
}

function searchMessages() {
  const query = document.getElementById('searchInput').value.trim();
  if (!query) {
    showError('searchResults', '검색어를 입력해주세요.');
    return;
  }
  
  if (!currentRoom) return;
  
  socket.emit('search_messages_event', { query: query });
}

function displaySearchResults(results, query) {
  const container = document.getElementById('searchResults');
  
  if (results.length === 0) {
    container.innerHTML = `
      <p style="text-align: center; color: var(--text-muted); padding: 40px;">
        "${query}" 검색 결과가 없습니다.
      </p>
    `;
    return;
  }
  
  container.innerHTML = `
    <h4 style="margin-bottom: 15px;">"${query}" 검색 결과 (${results.length}개)</h4>
    ${results.map(msg => `
      <div class="search-result-item">
        <div class="search-result-content">
          ${highlightSearchTerm(escapeHtml(msg.content), query)}
        </div>
        <div class="search-result-meta">
          ${msg.username} • ${new Date(msg.timestamp).toLocaleString()}
        </div>
      </div>
    `).join('')}
  `;
}

function highlightSearchTerm(text, term) {
  const regex = new RegExp(`(${term})`, 'gi');
  return text.replace(regex, '<span class="search-highlight">$1</span>');
}

// 더 많은 메시지 로드
function loadMoreMessages() {
  if (!currentRoom) return;
  
  socket.emit('load_more_messages', {
    offset: messageOffset,
    limit: 20
  });
}

// 반응 기능
function openReactionModal(messageId) {
  selectedReactionMessageId = messageId;
  document.getElementById('reactionModal').classList.add('active');
}

function closeReactionModal() {
  document.getElementById('reactionModal').classList.remove('active');
  selectedReactionMessageId = null;
}

function addReaction(reaction) {
  if (!selectedReactionMessageId) return;
  
  socket.emit('add_reaction', {
    message_id: selectedReactionMessageId,
    reaction: reaction
  });
  
  closeReactionModal();
}

function toggleReaction(messageId, reaction) {
  socket.emit('add_reaction', {
    message_id: messageId,
    reaction: reaction
  });
}

// 멘션 기능
function mentionUser(username) {
  const msgInput = document.getElementById('msgInput');
  const currentText = msgInput.value;
  
  if (currentText.trim() === '') {
    msgInput.value = `@${username} `;
  } else {
    msgInput.value = `${currentText} @${username} `;
  }
  
  msgInput.focus();
  autoResizeTextarea({ target: msgInput });
  updateCharCounter('msgInput', 'msgCharCounter', 500);
}

function showMentionDropdown() {
  const dropdown = document.getElementById('mentionDropdown');
  dropdown.classList.add('show');
  
  dropdown.innerHTML = allUsers.map((user, index) => `
    <div class="mention-item ${index === 0 ? 'selected' : ''}" onclick="selectMention('${escapeHtml(user.username)}')">
      <div class="mention-avatar">${getUserInitial(user.username)}</div>
      <span>${escapeHtml(user.username)}</span>
    </div>
  `).join('');
  
  mentionIndex = 0;
  filteredUsers = allUsers;
}

function selectMention(username) {
  const msgInput = document.getElementById('msgInput');
  const currentText = msgInput.value;
  const atIndex = currentText.lastIndexOf('@');
  
  if (atIndex !== -1) {
    const beforeAt = currentText.substring(0, atIndex);
    msgInput.value = `${beforeAt}@${username} `;
  } else {
    msgInput.value = `${currentText}@${username} `;
  }
  
  document.getElementById('mentionDropdown').classList.remove('show');
  msgInput.focus();
  updateCharCounter('msgInput', 'msgCharCounter', 500);
}

function showMentionNotification(data) {
  // 간단한 알림 (실제로는 브라우저 알림 API 사용 가능)
  playNotificationSound();
  
  // 임시 알림 표시
  const notification = document.createElement('div');
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: var(--primary-color);
    color: white;
    padding: 15px 20px;
    border-radius: 10px;
    box-shadow: var(--shadow-lg);
    z-index: 1000;
    animation: slideInRoom 0.3s ease-out;
  `;
  notification.innerHTML = `
    <strong>${data.from_user}님이 멘션했습니다</strong><br>
    <small>${data.message.substring(0, 50)}...</small>
  `;
  
  document.body.appendChild(notification);
  
  setTimeout(() => {
    notification.remove();
  }, 5000);
}

// 방 목록 새로고침 (수동)
function refreshRooms() {
  console.log('🔄 수동 방 목록 새로고침');
  if (socket && socket.connected) {
    socket.emit('get_rooms');
  }
}

// 뒤로가기
function backToRoomSelect() {
  console.log('⬅️ 뒤로가기 버튼 클릭');
  currentRoom = null;
  showScreen('roomSelectScreen');
}

// 이벤트 리스너 설정
function setupEventListeners() {
  // 메시지 입력에서만 엔터키 처리 (form 제출과 별도)
  document.getElementById('msgInput').addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  document.getElementById('searchInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') searchMessages();
  });

  // 타이핑 감지
  document.getElementById('msgInput').addEventListener('input', handleTyping);

  // 문자 수 카운터
  document.getElementById('newRoomInput').addEventListener('input', (e) => {
    updateCharCounter('newRoomInput', 'roomCharCounter', 30);
  });

  document.getElementById('nameInput').addEventListener('input', (e) => {
    updateCharCounter('nameInput', 'nameCharCounter', 20);
  });

  document.getElementById('msgInput').addEventListener('input', (e) => {
    updateCharCounter('msgInput', 'msgCharCounter', 500);
    handleMentionInput(e);
  });

  // 클릭 외부 감지
  document.addEventListener('click', (e) => {
    const emojiPicker = document.getElementById('emojiPicker');
    const emojiBtn = document.querySelector('.emoji-btn');
    const mentionDropdown = document.getElementById('mentionDropdown');
    const mentionBtn = document.querySelector('.mention-btn');
    
    if (!emojiPicker.contains(e.target) && e.target !== emojiBtn) {
      emojiPicker.classList.remove('show');
    }
    
    if (!mentionDropdown.contains(e.target) && e.target !== mentionBtn) {
      mentionDropdown.classList.remove('show');
    }
  });

  // 모달 닫기
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeReactionModal();
      document.getElementById('searchPanel').classList.remove('active');
    }
  });
}

// 멘션 입력 처리
function handleMentionInput(e) {
  const input = e.target;
  const text = input.value;
  const cursorPosition = input.selectionStart;
  
  // @ 뒤의 텍스트 찾기
  const beforeCursor = text.substring(0, cursorPosition);
  const atIndex = beforeCursor.lastIndexOf('@');
  
  if (atIndex !== -1) {
    const afterAt = beforeCursor.substring(atIndex + 1);
    
    if (afterAt.includes(' ')) {
      document.getElementById('mentionDropdown').classList.remove('show');
      return;
    }
    
    // 사용자 필터링
    filteredUsers = allUsers.filter(user => 
      user.username.toLowerCase().includes(afterAt.toLowerCase())
    );
    
    if (filteredUsers.length > 0) {
      const dropdown = document.getElementById('mentionDropdown');
      dropdown.innerHTML = filteredUsers.map((user, index) => `
        <div class="mention-item ${index === 0 ? 'selected' : ''}" onclick="selectMention('${escapeHtml(user.username)}')">
          <div class="mention-avatar">${getUserInitial(user.username)}</div>
          <span>${escapeHtml(user.username)}</span>
        </div>
      `).join('');
      dropdown.classList.add('show');
      mentionIndex = 0;
    } else {
      document.getElementById('mentionDropdown').classList.remove('show');
    }
  } else {
    document.getElementById('mentionDropdown').classList.remove('show');
  }
}

// 타이핑 처리
function handleTyping() {
  if (!isTyping && currentRoom) {
    isTyping = true;
    socket.emit('typing_start', {});
  }

  clearTimeout(typingTimer);
  typingTimer = setTimeout(() => {
    if (isTyping && currentRoom) {
      isTyping = false;
      socket.emit('typing_stop', {});
    }
  }, 1000);
}

// 텍스트 영역 자동 크기 조정
function autoResizeTextarea(event) {
  const textarea = event.target;
  textarea.style.height = 'auto';
  textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
}

// 문자 수 카운터 업데이트
function updateCharCounter(inputId, counterId, maxLength) {
  const input = document.getElementById(inputId);
  const counter = document.getElementById(counterId);
  const length = input.value.length;
  
  counter.textContent = `${length}/${maxLength}`;
  
  counter.classList.remove('warning', 'danger');
  if (length > maxLength * 0.8) {
    counter.classList.add('warning');
  }
  if (length > maxLength * 0.95) {
    counter.classList.add('danger');
  }
}

// 이모지 피커 초기화
function initializeEmojiPicker() {
  const emojiPicker = document.getElementById('emojiPicker');
  
  emojis.forEach(emoji => {
    const button = document.createElement('button');
    button.className = 'emoji-item';
    button.textContent = emoji;
    button.onclick = () => insertEmoji(emoji);
    emojiPicker.appendChild(button);
  });
}

// 이모지 피커 토글
function toggleEmojiPicker() {
  const emojiPicker = document.getElementById('emojiPicker');
  emojiPicker.classList.toggle('show');
}

// 이모지 삽입
function insertEmoji(emoji) {
  const msgInput = document.getElementById('msgInput');
  const start = msgInput.selectionStart;
  const end = msgInput.selectionEnd;
  const text = msgInput.value;
  
  msgInput.value = text.substring(0, start) + emoji + text.substring(end);
  msgInput.selectionStart = msgInput.selectionEnd = start + emoji.length;
  
  updateCharCounter('msgInput', 'msgCharCounter', 500);
  autoResizeTextarea({ target: msgInput });
  msgInput.focus();
  
  document.getElementById('emojiPicker').classList.remove('show');
}

// 테마 토글
function toggleTheme() {
  const body = document.body;
  const currentTheme = body.getAttribute('data-theme');
  const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
  
  body.setAttribute('data-theme', newTheme);
  localStorage.setItem('theme', newTheme);
  
  const themeBtn = document.querySelector('.theme-toggle');
  themeBtn.textContent = newTheme === 'dark' ? '☀️ 라이트모드' : '🌙 다크모드';
}

// 테마 로드
function loadTheme() {
  const savedTheme = localStorage.getItem('theme') || 'light';
  document.body.setAttribute('data-theme', savedTheme);
  
  const themeBtn = document.querySelector('.theme-toggle');
  themeBtn.textContent = savedTheme === 'dark' ? '☀️ 라이트모드' : '🌙 다크모드';
}

// 알림 사운드 재생
function playNotificationSound() {
  try {
    const audio = document.getElementById('notificationSound');
    audio.currentTime = 0;
    audio.play().catch(e => console.log('🔇 Sound play failed:', e));
  } catch (e) {
    console.log('🔇 Sound play failed:', e);
  }
}

// 스크롤 관련
function scrollToBottom() {
  const messages = document.getElementById('messages');
  messages.scrollTop = messages.scrollHeight;
}

// 유틸리티 함수들
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function getUserInitial(username) {
  return username.charAt(0).toUpperCase();
}