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
    currentDrawerName: '',
    currentWord: '',
    maskedWord: '',
    timer: 60,
    messages: [],
    isDrawer: false,
    wordLength: 0,
    wordChoices: [],
    mvps: null,
    clearCounter: 0,
    hasGuessedCorrectly: false,
    hostId: ''
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
    const socketUrl = `${protocol}//${apiHost}/ws/${roomId}?player_id=${playerId}&player_name=${encodeURIComponent(playerName)}`;
    
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
    if (data && data.host_id) gameState.hostId = data.host_id;
    console.log(`[DEBUG] [WS] Received event: ${type}`, data);

    switch (type) {
      case 'rehydration':
        console.log(`[DEBUG] [Sync] Received ${data.players?.length || 0} players in rehydration`);
        gameState.status = data.status;
        
        if (data.players) {
          gameState.players.splice(0, gameState.players.length, ...data.players);
        }
        
        gameState.currentDrawer = data.current_drawer;
        
        const drawer = data.players?.find(p => p.player_id === data.current_drawer);
        gameState.currentDrawerName = drawer ? drawer.player_name : 'Someone';
        
        gameState.currentWord = data.current_word;
        gameState.maskedWord = data.masked_word;
        gameState.timer = data.timer;
        gameState.isDrawer = data.current_drawer === gameState.playerId;
        gameState.wordChoices = data.word_choices || [];
        gameState.clearCounter = data.clear_counter || 0;
        break;

      case 'choosing_word':
        console.log('[DEBUG] [FSM] Transitioning to CHOOSING state:', data);
        gameState.status = 'CHOOSING';
        gameState.currentDrawer = data.drawer_id;
        gameState.currentDrawerName = data.drawer_name;
        gameState.isDrawer = data.drawer_id === gameState.playerId;
        gameState.wordChoices = data.choices || [];
        gameState.timer = data.delay || 10;
        addSystemMessage(`${data.drawer_name} is choosing a word...`);
        break;

      case 'game_event':
        addSystemMessage(data.details);
        if (data.event === 'game_start') gameState.status = 'IN_PROGRESS';
        break;
      
      case 'round_ended':
        gameState.status = 'ROUND_END';
        gameState.currentWord = data.word; // Reveal the full word
        addSystemMessage(`Round ended! The word was: ${data.word}`);
        break;

      case 'game_over':
        gameState.status = 'GAME_OVER';
        gameState.mvps = data.mvps;
        if (data.leaderboard) {
          gameState.players.splice(0, gameState.players.length, ...data.leaderboard);
        }
        addSystemMessage('Game Over! Check the final leaderboard.');
        break;

      case 'game_paused':
        gameState.status = 'PAUSED';
        addSystemMessage('Game paused by host');
        break;

      case 'game_resumed':
        gameState.status = data.status;
        addSystemMessage('Game resumed');
        break;

      case 'clear_canvas':
        console.log('[DEBUG] [Canvas] Clearing drawing surface');
        gameState.clearCounter++;
        break;

      case 'new_turn':
        gameState.status = 'DRAWING';
        gameState.hasGuessedCorrectly = false;
        gameState.currentDrawer = data.drawer_id;
        gameState.isDrawer = data.drawer_id === gameState.playerId;
        gameState.currentWord = data.full_word;
        gameState.maskedWord = data.masked_word;
        gameState.wordLength = data.word_length || 0;
        gameState.timer = data.seconds || 60;
        addSystemMessage(`${data.drawer_name} is now drawing!`);
        // Force canvas reset event
        window.dispatchEvent(new CustomEvent('canvas-clear'));
        break;

      case 'timer_update':
        gameState.timer = data.seconds;
        if (data.seconds <= 5 && data.seconds > 0) playSound('tick');
        break;

      case 'correct_guess':
        playSound('success');
        addSystemMessage(`${data.player_name} guessed the word! (+${data.points} pts)`);
        
        // Trigger satisfying confetti celebration
        confetti({
          particleCount: 150,
          spread: 70,
          origin: { y: 0.6 },
          colors: ['#6366f1', '#22d3ee', '#8b5cf6', '#ffffff']
        });
        
        // Update local state immediately for responsiveness
        if (data.player_id === gameState.playerId) {
          gameState.hasGuessedCorrectly = true;
        }
        const p = gameState.players.find(p => p.player_id === data.player_id);
        if (p) {
          p.score = data.total_score;
          p.guessed_this_round = true;
          p.streak = data.streak;
        }
        break;

      case 'score_update':
        console.log('[DEBUG] [Sync] Leaderboard Update:', data.leaderboard);
        if (data.leaderboard) {
          gameState.players.splice(0, gameState.players.length, ...data.leaderboard);
        }
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

  const selectWord = (word) => {
    const apiHost = window.location.hostname === 'localhost' ? 'localhost:8000' : `${window.location.hostname}:8000`;
    fetch(`http://${apiHost}/select-word/${gameState.roomId}?player_id=${gameState.playerId}&word=${word}`, { method: 'POST' });
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

  const setPlayer = (id, name) => {
    console.log(`[DEBUG] [Store] Setting local player: ${name} (${id})`);
    gameState.playerId = id;
    gameState.playerName = name;
  };

  const resetState = () => {
    console.log('[DEBUG] [Store] Resetting state');
    if (socket.value) {
      socket.value.close();
      socket.value = null;
    }
    gameState.status = 'LOBBY';
    gameState.messages = [];
    gameState.players.splice(0, gameState.players.length);
  };

  return {
    gameState,
    connect,
    send,
    setPlayer,
    resetState
  };
});
