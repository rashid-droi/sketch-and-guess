<script setup>
import { ref, onMounted, watch, nextTick, onBeforeUnmount } from 'vue';
import { useGameStore } from '../stores/gameStore';

const props = defineProps(['messages', 'onSend']);
const gameStore = useGameStore();

const newMessage = ref('');
const messageContainer = ref(null);
const isAtBottom = ref(true);

const sendMessage = () => {
  if (!newMessage.value.trim()) return;
  props.onSend('chat', { message: newMessage.value });
  newMessage.value = '';
};

const scrollToBottom = (smooth = false) => {
  const el = messageContainer.value;
  if (!el) return;

  el.scrollTo({
    top: el.scrollHeight,
    behavior: smooth ? 'smooth' : 'auto'
  });
};

const handleScroll = () => {
  const el = messageContainer.value;
  if (!el) return;

  isAtBottom.value =
    el.scrollHeight - el.scrollTop <= el.clientHeight + 20;
};

const manualScrollToBottom = () => {
  isAtBottom.value = true;
  scrollToBottom(true);
};

watch(() => props.messages.length, () => {
  if (isAtBottom.value) {
    nextTick(() => scrollToBottom());
  }
});

onMounted(() => {
  scrollToBottom();
  messageContainer.value?.addEventListener('scroll', handleScroll);
});

onBeforeUnmount(() => {
  messageContainer.value?.removeEventListener('scroll', handleScroll);
});

const getPlayerColor = (name) => {
  if (!name || name === 'System') return '#64748b';

  const colors = [
    '#ef4444', '#f59e0b', '#10b981',
    '#3b82f6', '#8b5cf6', '#ec4899'
  ];

  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }

  return colors[Math.abs(hash) % colors.length];
};
</script>

<template>
  <div class="chat-wrapper">
    <div class="chat-container">

      <!-- HEADER -->
      <div class="chat-header">
        <span class="chat-title">LIVE CHAT</span>
        <div class="status-indicator">
          <div class="status-dot"></div>
          <span class="status-text">LIVE</span>
        </div>
      </div>

      <!-- MESSAGES -->
      <div
        class="message-area"
        ref="messageContainer"
        @scroll="handleScroll"
      >
        <div
          v-for="msg in messages"
          :key="msg.id"
          class="chat-line"
        >
          <div v-if="msg.type === 'system'" class="system-note">
            {{ msg.text }}
          </div>

          <div v-else class="user-message">
            <div
              class="author-avatar"
              :style="{ backgroundColor: getPlayerColor(msg.player) }"
            >
              {{ msg.player?.charAt(0).toUpperCase() || '?' }}
            </div>

            <div class="text-content">
              <span class="author-name">{{ msg.player }}</span>
              <span class="message-text">{{ msg.text }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- SCROLL BUTTON -->
      <button
        v-if="!isAtBottom"
        class="scroll-down-btn"
        @click="manualScrollToBottom"
      >
        ↓ New Messages
      </button>

      <!-- INPUT -->
      <div class="input-area">
        <input
          v-model="newMessage"
          type="text"
          placeholder="Type a message..."
          class="chat-input"
          @keyup.enter="sendMessage"
        />

        <button
          @click="sendMessage"
          class="send-btn"
          :disabled="!newMessage.trim()"
        >
          ↗
        </button>
      </div>

    </div>
  </div>
</template>

<style scoped>

/* ===== ROOT ===== */
.chat-wrapper {
  width: 100%;
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: stretch;
  padding: 0.5rem;
}

/* ===== CONTAINER ===== */
.chat-container {
  width: 100%;
  max-width: 900px;
  height: 100%;
  display: flex;
  flex-direction: column;
  position: relative;

  background: rgba(15, 23, 42, 0.75);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 14px;
  overflow: hidden;
}

/* ===== HEADER ===== */
.chat-header {
  flex-shrink: 0;
  padding: 0.75rem 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-title {
  font-size: 0.75rem;
  letter-spacing: 0.12em;
  font-weight: 700;
  color: #94a3b8;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.status-dot {
  width: 6px;
  height: 6px;
  background: #22c55e;
  border-radius: 50%;
}

.status-text {
  font-size: 0.65rem;
  color: #22c55e;
}

/* ===== MESSAGE AREA ===== */
.message-area {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem 0;
  scroll-behavior: smooth;
}

/* Chat lines */
.chat-line {
  padding: 0.35rem 0.9rem;
}

.user-message {
  display: flex;
  gap: 0.6rem;
}

/* Avatar */
.author-avatar {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  font-size: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

/* Text */
.text-content {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.author-name {
  font-size: 0.75rem;
  font-weight: 600;
  color: #94a3b8;
}

.message-text {
  font-size: 0.9rem;
  color: #e2e8f0;
  word-break: break-word;
}

/* System */
.system-note {
  text-align: center;
  font-size: 0.7rem;
  opacity: 0.7;
}

/* ===== INPUT ===== */
.input-area {
  flex-shrink: 0;
  display: flex;
  gap: 0.5rem;
  padding: 0.6rem;
  background: rgba(0,0,0,0.3);
  backdrop-filter: blur(6px);
}

.chat-input {
  flex: 1;
  padding: 0.6rem 0.9rem;
  border-radius: 10px;
  border: 1px solid rgba(255,255,255,0.1);
  background: transparent;
  color: white;
  font-size: 0.9rem;
}

.send-btn {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  background: var(--primary);
  color: white;
  font-size: 1rem;
}

/* ===== SCROLL BUTTON ===== */
.scroll-down-btn {
  position: absolute;
  bottom: 70px;
  left: 50%;
  transform: translateX(-50%);
  padding: 0.4rem 1rem;
  border-radius: 20px;
  font-size: 0.75rem;
  background: rgba(0,0,0,0.6);
  color: white;
}

/* ===== RESPONSIVE ===== */

/* Tablet */
@media (max-width: 1024px) {
  .chat-container {
    max-width: 100%;
    border-radius: 10px;
  }
}

/* Mobile */
@media (max-width: 600px) {

  .chat-wrapper {
    padding: 0;
  }

  .chat-container {
    border-radius: 0;
  }

  .author-avatar {
    width: 20px;
    height: 20px;
    font-size: 0.6rem;
  }

  .message-text {
    font-size: 0.8rem;
  }

  .chat-input {
    font-size: 0.8rem;
  }

  .send-btn {
    width: 36px;
    height: 36px;
  }

  .scroll-down-btn {
    bottom: 65px;
    font-size: 0.65rem;
  }
}

/* Very small devices */
@media (max-width: 380px) {
  .message-text {
    font-size: 0.75rem;
  }
}

</style>