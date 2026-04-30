import { ref, reactive } from 'vue';

export function useSocket() {
  const socket = ref(null);
  
  // Reactive state to be used by components
  const state = reactive({
    isConnected: false,
    messages: [],
    players: [],
    currentWord: '',
    maskedWord: '',
    timer: 60,
    isDrawer: false,
    currentDrawerId: '',
    status: 'LOBBY'
  });

  const connect = (roomId, playerId) => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const socketUrl = `${protocol}//localhost:8000/ws/${roomId}?player_id=${playerId}`;
    
    socket.value = new WebSocket(socketUrl);

    socket.value.onopen = () => {
      state.isConnected = true;
      addSystemMessage('Connected to game server.');
    };

    socket.value.onmessage = (event) => {
      const { type, data } = JSON.parse(event.data);
      handleIncomingMessage(type, data);
    };

    socket.value.onclose = () => {
      state.isConnected = false;
      addSystemMessage('Disconnected from server.');
    };

    socket.value.onerror = (error) => {
      console.error('WebSocket Error:', error);
    };
  };

  const handleIncomingMessage = (type, data) => {
    switch (type) {
      case 'chat':
        state.messages.push({
          id: Date.now(),
          player: data.player_name || 'System',
          text: data.message,
          type: 'user'
        });
        break;

      case 'draw':
        // Dispatch global event for the Canvas component to pick up
        window.dispatchEvent(new CustomEvent('remote-draw', { detail: data }));
        break;

      case 'game_event':
        addSystemMessage(data.details);
        if (data.event === 'game_start') state.status = 'IN_PROGRESS';
        break;

      case 'new_turn':
        state.currentDrawerId = data.drawer_id;
        state.isDrawer = data.drawer_id === localStorage.getItem('player_id'); // Simple check
        state.currentWord = data.full_word;
        state.maskedWord = data.masked_word;
        state.timer = 60;
        addSystemMessage(`${data.drawer_name} is drawing!`);
        break;

      case 'timer_update':
        state.timer = data.seconds;
        break;

      case 'score_update':
        state.players = data.leaderboard;
        break;

      case 'correct_guess':
        addSystemMessage(`${data.player_name} GUESSED IT! The word was ${data.word}`);
        break;
    }
  };

  const send = (type, data) => {
    if (socket.value && socket.value.readyState === WebSocket.OPEN) {
      socket.value.send(JSON.stringify({ type, data }));
    }
  };

  const addSystemMessage = (text) => {
    state.messages.push({
      id: Date.now(),
      player: 'System',
      text,
      type: 'system'
    });
  };

  const close = () => {
    if (socket.value) {
      socket.value.close();
    }
  };

  return {
    state,
    connect,
    send,
    close
  };
}
