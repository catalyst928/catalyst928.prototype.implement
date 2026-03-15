<template>
  <div v-if="callState !== 'idle'" class="call-status">
    <span class="indicator-dot" :class="dotClass"></span>
    <span class="status-label">{{ statusLabel }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useCallStore } from '../stores/callStore'

const store = useCallStore()
const { callState, errorMessage, timeoutRemaining } = storeToRefs(store)

const statusLabel = computed(() => {
  switch (callState.value) {
    case 'dialing': return `Connecting… (${timeoutRemaining.value}s)`
    case 'ringing': return `Ringing… (${timeoutRemaining.value}s)`
    case 'connected': return 'Call Connected'
    case 'ended': return errorMessage.value === 'No Answer' ? 'No Answer' : 'Call Ended'
    case 'error': return errorMessage.value || 'Connection Error'
    default: return ''
  }
})

const dotClass = computed(() => {
  switch (callState.value) {
    case 'connected': return 'dot-green'
    case 'error': return 'dot-red'
    default: return 'dot-gray'
  }
})
</script>

<style scoped>
.call-status {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px 0;
  font-size: 0.95rem;
  color: #333;
}

.indicator-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dot-green  { background: #22c55e; }
.dot-red    { background: #ef4444; }
.dot-gray   { background: #9ca3af; }
</style>
