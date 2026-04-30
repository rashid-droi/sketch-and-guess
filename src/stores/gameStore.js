import { defineStore } from 'pinia';
import { ref, reactive } from 'vue';
import confetti from 'canvas-confetti';

export const useGameStore = defineStore('game', () => {
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
    isDrawer: false,
    wordLength: 0
  });

  const connect = (roomId, playerId, playerName) => {
    if (socket.value) {
      socket.value.onclose = null; // Prevent retry loop
      socket.value.close();
    }

    // Persist session for reconnection
    sessionStorage.setItem('room_id', roomId);
    sessionStorage.setItem('player_id', playerId);
    sessionStorage.setItem('player_name', playerName);

    gameState.roomId = roomId;
    gameState.playerId = playerId;
    gameState.playerName = playerName;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const apiHost = window.location.hostname === 'localhost' ? 'localhost:8000' : `${window.location.hostname}:8000`;
    const socketUrl = `${protocol}//${apiHost}/ws/${roomId}?player_id=${playerId}`;
    
    socket.value = new WebSocket(socketUrl);

    socket.value.onmessage = (event) => {
      const message = JSON.parse(event.data);
      handleMessage(message);
    };

    socket.value.onclose = () => {
      console.log('WebSocket connection closed. Retrying in 3s...');
      setTimeout(() => {
        if (gameState.roomId) connect(gameState.roomId, gameState.playerId, gameState.playerName);
      }, 3000);
    };
  };

  const playSound = (type) => {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      
      osc.connect(gain);
      gain.connect(ctx.destination);
      
      if (type === 'success') {
        osc.frequency.setValueAtTime(523.25, ctx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(1046.50, ctx.currentTime + 0.1);
        gain.gain.setValueAtTime(0.1, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3);
        osc.start();
        osc.stop(ctx.currentTime + 0.3);
      } else if (type === 'tick') {
        osc.frequency.setValueAtTime(150, ctx.currentTime);
        gain.gain.setValueAtTime(0.05, ctx.currentTime);
        osc.start();
        osc.stop(ctx.currentTime + 0.05);
      }
    } catch (e) {
      console.warn('Audio context blocked or not supported');
    }
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
        gameState.wordLength = data.word_length || 0;
        gameState.timer = 60;
        addSystemMessage(`${data.drawer_name} is now drawing!`);
        break;

      case 'timer_update':
        gameState.timer = data.seconds;
        if (data.seconds <= 5 && data.seconds > 0) playSound('tick');
        break;

      case 'correct_guess':
        playSound('success');
        addSystemMessage(`${data.player_name} guessed the word: ${data.word}!`);
        confetti({
          particleCount: 150,
          spread: 70,
          origin: { y: 0.6 },
          colors: ['#6366f1', '#22d3ee', '#8b5cf6', '#ffffff']
        });
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
        if (gameState.messages.length > 100) gameState.messages.shift();
        break;

      case 'draw':
        window.dispatchEvent(new CustomEvent('remote-draw', { detail: data }));
        break;
    }
  };

  const send = (type, data) => {
    if (socket.value && socket.value.readyState === WebSocket.OPEN) {
      const enrichedData = {
        ...data,
        player_id: gameState.playerId,
        player_name: gameState.playerName
      };
      socket.value.send(JSON.stringify({ type, data: enrichedData }));
    }
  };

  const addSystemMessage = (text) => {
    gameState.messages.push({
      id: Date.now(),
      player: 'System',
      text,
      type: 'system'
    });
    if (gameState.messages.length > 100) gameState.messages.shift();
  };

  const resetState = () => {
    if (socket.value) {
      socket.value.close();
      socket.value = null;
    }
    gameState.status = 'LOBBY';
    gameState.messages = [];
    gameState.players = [];
  };

  return {
    gameState,
    connect,
    send,
    resetState
  };
});
