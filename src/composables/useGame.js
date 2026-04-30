import { ref, reactive } from 'vue';

export function useGame() {
  const socket = ref(null);
  const gameState = reactive({
    roomId: '',
    playerId: '',
    playerName: '',
    players: [],
    status: 'LOBBY',
    currentDrawer: '',
    currentWord: '',
    maskedWord: '',
    timer: 60,
    messages: [],
    isDrawer: false
  });

  const connect = (roomId, playerId, playerName) => {
    gameState.roomId = roomId;
    gameState.playerId = playerId;
    gameState.playerName = playerName;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // Assuming backend runs on localhost:8000 for development
    const socketUrl = `${protocol}//localhost:8000/ws/${roomId}?player_id=${playerId}`;
    
    socket.value = new WebSocket(socketUrl);

    socket.value.onmessage = (event) => {
      const message = JSON.parse(event.data);
      handleMessage(message);
    };

    socket.value.onclose = () => {
      console.log('WebSocket connection closed');
    };
  };

  const handleMessage = (message) => {
    const { type, data } = message;

    switch (type) {
      case 'game_event':
        addSystemMessage(data.details);
        if (data.event === 'game_start') gameState.status = 'IN_PROGRESS';
        break;
      
      case 'new_turn':
        gameState.currentDrawer = data.drawer_id;
        gameState.isDrawer = data.drawer_id === gameState.playerId;
        gameState.currentWord = data.full_word;
        gameState.maskedWord = data.masked_word;
        gameState.timer = 60;
        addSystemMessage(`${data.drawer_name} is now drawing!`);
        break;

      case 'timer_update':
        gameState.timer = data.seconds;
        break;

      case 'correct_guess':
        addSystemMessage(`${data.player_name} guessed the word: ${data.word}!`);
        // Update scores logic would go here, or just wait for next turn event
        break;

      case 'score_update':
        gameState.players = data.leaderboard;
        break;

      case 'chat':
        gameState.messages.push({
          id: Date.now(),
          player: data.player_name || 'System',
          text: data.message,
          type: 'user'
        });
        break;

      case 'draw':
        // Handled directly by the Canvas component via event listener or property
        window.dispatchEvent(new CustomEvent('remote-draw', { detail: data.data }));
        break;
    }
  };

  const send = (type, data) => {
    if (socket.value && socket.value.readyState === WebSocket.OPEN) {
      socket.value.send(JSON.stringify({ type, data }));
    }
  };

  const addSystemMessage = (text) => {
    gameState.messages.push({
      id: Date.now(),
      player: 'System',
      text,
      type: 'system'
    });
  };

  return {
    gameState,
    connect,
    send
  };
}
