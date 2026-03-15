<template>
  <div class="video-panel">
    <div class="video-container">
      <video
        ref="remoteVideoEl"
        class="remote-video"
        autoplay
        playsinline
        aria-label="Customer video"
      />
      <video
        ref="localVideoEl"
        class="local-video"
        autoplay
        playsinline
        muted
        aria-label="Agent video (you)"
      />
      <span class="label remote-label">Customer</span>
      <span class="label local-label">You</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useSessionStore } from '../stores/sessionStore'

const store = useSessionStore()
const remoteVideoEl = ref<HTMLVideoElement | null>(null)
const localVideoEl = ref<HTMLVideoElement | null>(null)

watch(() => store.remoteStream, (stream) => {
  if (remoteVideoEl.value) {
    remoteVideoEl.value.srcObject = stream
  }
})

watch(() => store.localStream, (stream) => {
  if (localVideoEl.value) {
    localVideoEl.value.srcObject = stream
  }
})
</script>

<style scoped>
.video-panel {
  width: 100%;
}

.video-container {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  background: #1a1a2e;
  border-radius: 12px;
  overflow: hidden;
}

.remote-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.local-video {
  position: absolute;
  bottom: 8px;
  right: 8px;
  width: 25%;
  aspect-ratio: 16 / 9;
  object-fit: cover;
  border-radius: 8px;
  border: 2px solid rgba(255, 255, 255, 0.3);
}

.label {
  position: absolute;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  font-size: 0.7rem;
  padding: 2px 8px;
  border-radius: 4px;
}

.remote-label {
  top: 8px;
  left: 8px;
}

.local-label {
  bottom: 8px;
  right: calc(25% + 16px);
}
</style>
