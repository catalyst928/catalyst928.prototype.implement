<template>
  <div v-if="callState === 'connected'" class="video-section">
    <div class="remote-wrapper">
      <video ref="remoteVideo" autoplay playsinline class="remote-video"></video>
      <span class="video-label label-agent">Agent</span>

      <div class="local-wrapper">
        <video ref="localVideo" autoplay playsinline muted class="local-video"></video>
        <span class="video-label label-you">You</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useCallStore } from '../stores/callStore'

const store = useCallStore()
const { callState, localStream, remoteStream } = storeToRefs(store)

const localVideo = ref<HTMLVideoElement | null>(null)
const remoteVideo = ref<HTMLVideoElement | null>(null)

function bindStream(el: HTMLVideoElement | null, stream: MediaStream | null) {
  if (el) el.srcObject = stream
}

// Watch both the stream and the template ref — whichever arrives last triggers the bind
watch([localVideo, localStream], ([el, stream]) => bindStream(el, stream))
watch([remoteVideo, remoteStream], ([el, stream]) => bindStream(el, stream))

onUnmounted(() => {
  if (localVideo.value) localVideo.value.srcObject = null
  if (remoteVideo.value) remoteVideo.value.srcObject = null
})
</script>

<style scoped>
.video-section {
  width: 100%;
  display: flex;
  justify-content: center;
  padding: 8px 16px;
  box-sizing: border-box;
}

.remote-wrapper {
  position: relative;
  width: 60vw;
  height: 60vw;
  max-width: 260px;
  max-height: 260px;
  border-radius: 12px;
  overflow: hidden;
  background: #111;
}

.remote-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.local-wrapper {
  position: absolute;
  bottom: 8px;
  right: 8px;
  width: 28vw;
  height: 28vw;
  max-width: 90px;
  max-height: 90px;
  border-radius: 8px;
  overflow: hidden;
  border: 2px solid #fff;
  background: #222;
}

.local-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.video-label {
  position: absolute;
  font-size: 0.7rem;
  color: #fff;
  background: rgba(0, 0, 0, 0.5);
  padding: 2px 6px;
  border-radius: 4px;
}

.label-agent {
  top: 6px;
  left: 6px;
}

.label-you {
  bottom: 2px;
  left: 2px;
}
</style>
