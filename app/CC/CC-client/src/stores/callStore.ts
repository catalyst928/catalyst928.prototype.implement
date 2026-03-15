import { defineStore } from 'pinia'
import { ref } from 'vue'

export type CallState = 'idle' | 'dialing' | 'ringing' | 'connected' | 'ended' | 'error'

export const useCallStore = defineStore('call', () => {
  const callState = ref<CallState>('idle')
  const phoneNumber = ref<string>('')
  const localStream = ref<MediaStream | null>(null)
  const remoteStream = ref<MediaStream | null>(null)
  const errorMessage = ref<string>('')
  const timeoutRemaining = ref<number>(0)

  return { callState, phoneNumber, localStream, remoteStream, errorMessage, timeoutRemaining }
})
