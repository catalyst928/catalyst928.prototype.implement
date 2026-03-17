import { signaling } from '../api/signaling'
import { useCallStore } from '../stores/callStore'
import { onUnmounted } from 'vue'

const CALL_TIMEOUT_MS = 30_000
const RESET_DELAY_MS = 2_000

let pc: RTCPeerConnection | null = null
const iceCandidateBuffer: RTCIceCandidateInit[] = []
let answerSet = false

// Timer IDs for timeout and countdown
let callTimeoutId: ReturnType<typeof setTimeout> | null = null
let countdownIntervalId: ReturnType<typeof setInterval> | null = null

function clearTimers(): void {
  if (callTimeoutId !== null) {
    clearTimeout(callTimeoutId)
    callTimeoutId = null
  }
  if (countdownIntervalId !== null) {
    clearInterval(countdownIntervalId)
    countdownIntervalId = null
  }
}

function createPeerConnection(): RTCPeerConnection {
  const conn = new RTCPeerConnection({ iceServers: [] })

  conn.onicecandidate = (event) => {
    if (event.candidate) {
      signaling.send({ type: 'ice-candidate', data: { candidate: event.candidate } })
    }
  }

  conn.ontrack = (event) => {
    const store = useCallStore()
    const [stream] = event.streams
    store.remoteStream = stream ?? null
  }

  conn.onconnectionstatechange = () => {
    const store = useCallStore()
    if (conn.connectionState === 'connected') {
      clearTimers()
      store.timeoutRemaining = 0
      store.callState = 'connected'
      signaling.send({ type: 'call-start', data: { phone: store.phoneNumber } })
    } else if (conn.connectionState === 'failed' || conn.connectionState === 'disconnected') {
      store.callState = 'error'
      store.errorMessage = `WebRTC connection ${conn.connectionState}`
      _scheduleReset()
    }
  }

  return conn
}

async function applyBufferedCandidates(): Promise<void> {
  if (!pc) return
  while (iceCandidateBuffer.length > 0) {
    const candidate = iceCandidateBuffer.shift()!
    await pc.addIceCandidate(new RTCIceCandidate(candidate))
  }
}

function _scheduleReset(): void {
  setTimeout(() => {
    const store = useCallStore()
    store.callState = 'idle'
    store.errorMessage = ''
    store.phoneNumber = ''
    store.timeoutRemaining = 0
  }, RESET_DELAY_MS)
}

export function useWebRTC() {
  const unsubscribe = signaling.onMessage(async (msg) => {
    const store = useCallStore()

    if (msg.type === 'answer' && pc) {
      const data = msg.data as { sdp: string }
      await pc.setRemoteDescription(new RTCSessionDescription({ type: 'answer', sdp: data.sdp }))
      answerSet = true
      store.callState = 'ringing'
      await applyBufferedCandidates()
    }

    if (msg.type === 'ice-candidate') {
      const data = msg.data as { candidate: RTCIceCandidateInit }
      if (!answerSet) {
        iceCandidateBuffer.push(data.candidate)
      } else if (pc) {
        await pc.addIceCandidate(new RTCIceCandidate(data.candidate))
      }
    }

    if (msg.type === 'call-end') {
      await _endCallInternal(false)
    }
  })

  onUnmounted(unsubscribe)

  async function startCall(): Promise<void> {
    const store = useCallStore()
    await signaling.connect()

    const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: true })
    store.localStream = stream

    pc = createPeerConnection()
    answerSet = false
    iceCandidateBuffer.length = 0

    stream.getTracks().forEach((track) => pc!.addTrack(track, stream))

    const offer = await pc.createOffer()
    await pc.setLocalDescription(offer)

    store.callState = 'dialing'
    signaling.send({ type: 'offer', data: { sdp: offer.sdp } })

    // Start 30 s countdown
    store.timeoutRemaining = CALL_TIMEOUT_MS / 1000
    countdownIntervalId = setInterval(() => {
      const s = useCallStore()
      if (s.timeoutRemaining > 0) s.timeoutRemaining -= 1
    }, 1000)

    // Start 30 s hard timeout
    callTimeoutId = setTimeout(async () => {
      const s = useCallStore()
      s.errorMessage = 'No Answer'
      await _endCallInternal(false)
    }, CALL_TIMEOUT_MS)
  }

  async function endCall(): Promise<void> {
    clearTimers()
    signaling.send({ type: 'call-end', data: {} })
    await _endCallInternal(false)
  }

  async function _endCallInternal(sendSignal: boolean): Promise<void> {
    const store = useCallStore()

    clearTimers()

    if (sendSignal) {
      signaling.send({ type: 'call-end', data: {} })
    }

    if (store.localStream) {
      store.localStream.getTracks().forEach((t) => t.stop())
      store.localStream = null
    }
    if (store.remoteStream) {
      store.remoteStream.getTracks().forEach((t) => t.stop())
      store.remoteStream = null
    }

    if (pc) {
      pc.close()
      pc = null
    }

    answerSet = false
    iceCandidateBuffer.length = 0
    store.callState = 'ended'

    _scheduleReset()
  }

  return { startCall, endCall }
}
