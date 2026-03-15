<template>
  <div class="dialpad">
    <input
      class="phone-input"
      type="tel"
      v-model="phoneNumber"
      placeholder="Enter phone number"
      :readonly="callState !== 'idle'"
    />

    <div class="keypad-grid">
      <button
        v-for="key in keys"
        :key="key"
        class="key-btn"
        :disabled="callState !== 'idle'"
        @click="pressKey(key)"
      >{{ key }}</button>
    </div>

    <div class="action-buttons">
      <button
        class="call-btn"
        :disabled="callState !== 'idle' || !phoneNumber"
        @click="onCall"
      >Call</button>
      <button
        class="end-btn"
        :disabled="callState === 'idle' || callState === 'ended' || callState === 'error'"
        @click="onEnd"
      >End Call</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { useCallStore } from '../stores/callStore'

const store = useCallStore()
const { phoneNumber, callState } = storeToRefs(store)

const keys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '0', '#']

function pressKey(key: string) {
  phoneNumber.value += key
}

const emit = defineEmits<{
  (e: 'call'): void
  (e: 'end'): void
}>()

function onCall() {
  emit('call')
}

function onEnd() {
  emit('end')
}
</script>

<style scoped>
.dialpad {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 0 16px;
  width: 100%;
  box-sizing: border-box;
}

.phone-input {
  width: 100%;
  max-width: 320px;
  padding: 10px 14px;
  font-size: 1.1rem;
  border: 1.5px solid #d1d5db;
  border-radius: 8px;
  text-align: center;
  box-sizing: border-box;
}

.keypad-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  width: 100%;
  max-width: 280px;
}

.key-btn {
  padding: 14px 0;
  font-size: 1.2rem;
  border: 1.5px solid #e5e7eb;
  border-radius: 50%;
  background: #f9fafb;
  cursor: pointer;
  transition: background 0.1s;
}

.key-btn:active:not(:disabled) {
  background: #e5e7eb;
}

.key-btn:disabled {
  opacity: 0.4;
  cursor: default;
}

.action-buttons {
  display: flex;
  gap: 16px;
  width: 100%;
  max-width: 280px;
}

.call-btn,
.end-btn {
  flex: 1;
  padding: 12px 0;
  font-size: 1rem;
  font-weight: 600;
  border: none;
  border-radius: 24px;
  cursor: pointer;
  transition: opacity 0.15s;
}

.call-btn {
  background: #22c55e;
  color: #fff;
}

.end-btn {
  background: #ef4444;
  color: #fff;
}

.call-btn:disabled,
.end-btn:disabled {
  opacity: 0.35;
  cursor: default;
}
</style>
