import { signaling } from '../api/signaling'
import { useSessionStore } from '../stores/sessionStore'

let pc: RTCPeerConnection | null = null
const iceCandidateBuffer: RTCIceCandidateInit[] = []
let offerSet = false

function createPeerConnection(): RTCPeerConnection {
  const conn = new RTCPeerConnection({ iceServers: [] })

  conn.onicecandidate = (event) => {
    if (event.candidate) {
      signaling.send({ type: 'ice-candidate', data: { candidate: event.candidate } })
    }
  }

  conn.ontrack = (event) => {
    const store = useSessionStore()
    const [stream] = event.streams
    store.remoteStream = stream ?? null
  }

  conn.onconnectionstatechange = () => {
    const store = useSessionStore()
    if (conn.connectionState === 'connected') {
      store.callState = 'call_active'
    } else if (conn.connectionState === 'failed' || conn.connectionState === 'disconnected') {
      store.callState = 'error'
      store.errorMessage = `WebRTC connection ${conn.connectionState}`
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

export function useWebRTC() {
  async function answerCall(offerSdp: string): Promise<void> {
    const store = useSessionStore()
    await signaling.connect()

    let stream: MediaStream | null = null
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: true })
      store.localStream = stream
    } catch (e) {
      console.warn('[webrtc] getUserMedia failed, proceeding without local media:', e)
    }

    pc = createPeerConnection()
    offerSet = false
    iceCandidateBuffer.length = 0

    if (stream) {
      stream.getTracks().forEach((track) => pc!.addTrack(track, stream!))
    }

    await pc.setRemoteDescription(new RTCSessionDescription({ type: 'offer', sdp: offerSdp }))
    offerSet = true
    await applyBufferedCandidates()

    const answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    signaling.send({ type: 'answer', data: { sdp: answer.sdp } })
  }

  function addIceCandidate(candidate: RTCIceCandidateInit): void {
    if (!offerSet) {
      iceCandidateBuffer.push(candidate)
    } else if (pc) {
      pc.addIceCandidate(new RTCIceCandidate(candidate))
    }
  }

  async function endCall(): Promise<void> {
    const store = useSessionStore()

    signaling.send({ type: 'call-end', data: {} })

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

    offerSet = false
    iceCandidateBuffer.length = 0
    store.callState = 'call_ended'
  }

  function endCallInternal(): void {
    const store = useSessionStore()

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

    offerSet = false
    iceCandidateBuffer.length = 0
    store.callState = 'call_ended'
  }

  return { answerCall, addIceCandidate, endCall, endCallInternal }
}
