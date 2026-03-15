<template>
  <div class="dialer-view">
    <header class="header-bar">
      <span class="header-title">CC-client — Customer Caller</span>
    </header>

    <VideoStream />

    <DialPad @call="handleCall" @end="handleEnd" />

    <CallStatus />
  </div>
</template>

<script setup lang="ts">
import VideoStream from '../components/VideoStream.vue'
import DialPad from '../components/DialPad.vue'
import CallStatus from '../components/CallStatus.vue'
import { useWebRTC } from '../composables/useWebRTC'

const { startCall, endCall } = useWebRTC()

async function handleCall() {
  await startCall()
}

async function handleEnd() {
  await endCall()
}
</script>

<style scoped>
.dialer-view {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 100dvh;
  width: 100%;
  max-width: 430px;
  margin: 0 auto;
  padding-bottom: 24px;
  box-sizing: border-box;
  gap: 12px;
}

.header-bar {
  width: 100%;
  padding: 14px 16px;
  background: #1e40af;
  color: #fff;
  text-align: center;
  box-sizing: border-box;
}

.header-title {
  font-size: 0.95rem;
  font-weight: 600;
  letter-spacing: 0.02em;
}
</style>
