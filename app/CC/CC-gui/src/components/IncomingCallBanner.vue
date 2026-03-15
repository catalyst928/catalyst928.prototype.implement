<template>
  <div class="banner-overlay" @click.self="() => {}">
    <div class="banner-card">
      <div class="banner-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z" />
        </svg>
      </div>
      <h2 class="banner-title">Incoming Call</h2>
      <p v-if="callerPhone" class="banner-phone">{{ formatPhone(callerPhone) }}</p>
      <button class="btn-answer" aria-label="Answer incoming call" @click="$emit('answer')">
        Answer
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useSessionStore } from '../stores/sessionStore'
import { computed } from 'vue'

defineEmits<{ answer: [] }>()

const store = useSessionStore()
const callerPhone = computed(() => store.callerPhone)

function formatPhone(phone: string): string {
  if (phone.length === 11) {
    return `${phone.slice(0, 3)}-${phone.slice(3, 7)}-${phone.slice(7)}`
  }
  return phone
}
</script>

<style scoped>
.banner-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.banner-card {
  background: var(--color-surface);
  border-radius: 16px;
  padding: 40px 48px;
  text-align: center;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.banner-icon {
  margin-bottom: 16px;
  animation: pulse-ring 1.5s ease-in-out infinite;
}

@keyframes pulse-ring {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(1.1); }
}

.banner-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 8px;
}

.banner-phone {
  color: var(--color-text-muted);
  font-size: 1.125rem;
  margin-bottom: 24px;
}

.btn-answer {
  background: var(--color-success);
  color: #fff;
  border: none;
  border-radius: 24px;
  padding: 12px 48px;
  font-size: 1.125rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}

.btn-answer:hover {
  opacity: 0.9;
}

.btn-answer:focus-visible {
  outline: 2px solid var(--color-info);
  outline-offset: 2px;
}
</style>
