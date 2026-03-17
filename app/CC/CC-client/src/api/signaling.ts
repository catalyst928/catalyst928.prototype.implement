const WS_URL = 'ws://localhost:8001/ws/signal?role=client'
const RECONNECT_BASE_MS = 1000
const RECONNECT_MAX_MS = 10000

type MessageHandler = (msg: Record<string, unknown>) => void

let socket: WebSocket | null = null
let reconnectAttempt = 0
let reconnectTimer: ReturnType<typeof setTimeout> | null = null
const handlers: MessageHandler[] = []

function connect(): Promise<void> {
  if (socket && socket.readyState === WebSocket.OPEN) return Promise.resolve()

  return new Promise<void>((resolve, reject) => {
    socket = new WebSocket(WS_URL)

    socket.onmessage = (event: MessageEvent) => {
      try {
        const msg = JSON.parse(event.data as string) as Record<string, unknown>
        handlers.forEach((h) => h(msg))
      } catch {
        // ignore non-JSON frames
      }
    }

    socket.onopen = () => {
      reconnectAttempt = 0
      resolve()
    }

    socket.onerror = (e) => {
      console.error('[signaling] WebSocket error', e)
      reject(e)
    }

    socket.onclose = () => {
      socket = null
      const delay = Math.min(RECONNECT_BASE_MS * 2 ** reconnectAttempt, RECONNECT_MAX_MS)
      reconnectAttempt++
      console.warn(`[signaling] WebSocket closed, reconnecting in ${delay}ms`)
      reconnectTimer = setTimeout(() => {
        reconnectTimer = null
        connect()
      }, delay)
    }
  })
}

function send(msg: Record<string, unknown>): void {
  if (!socket || socket.readyState !== WebSocket.OPEN) {
    console.warn('[signaling] WebSocket not open, cannot send', msg)
    return
  }
  socket.send(JSON.stringify(msg))
}

function onMessage(handler: MessageHandler): () => void {
  handlers.push(handler)
  return () => {
    const idx = handlers.indexOf(handler)
    if (idx !== -1) handlers.splice(idx, 1)
  }
}

export const signaling = { connect, send, onMessage }
