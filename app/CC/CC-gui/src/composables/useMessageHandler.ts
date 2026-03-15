import { signaling } from '../api/signaling'
import { useSessionStore } from '../stores/sessionStore'
import { useWebRTC } from './useWebRTC'
import { ref, onUnmounted } from 'vue'

const pendingOfferSdp = ref<string | null>(null)

export function useMessageHandler() {
  const store = useSessionStore()
  const { addIceCandidate, endCallInternal } = useWebRTC()

  const unsubscribe = signaling.onMessage((msg) => {
    const type = msg.type as string

    switch (type) {
      case 'offer': {
        const data = msg.data as { sdp: string }
        pendingOfferSdp.value = data.sdp
        store.callState = 'ringing'
        break
      }

      case 'ice-candidate': {
        const data = msg.data as { candidate: RTCIceCandidateInit }
        addIceCandidate(data.candidate)
        break
      }

      case 'call-start': {
        const data = msg.data as { phone: string }
        store.callerPhone = data.phone
        break
      }

      case 'call-end': {
        endCallInternal()
        break
      }

      case 'progress': {
        const step = msg.step as string
        const status = msg.status as 'running' | 'done'
        store.progressSteps[step] = status
        break
      }

      case 'business_payload': {
        const data = msg.data as Record<string, unknown>
        store.customer = data.customer as typeof store.customer
        store.bill = data.bill as typeof store.bill
        store.nbo = data.nbo as typeof store.nbo
        store.nboFallback = (data.nbo_fallback as boolean) ?? false
        store.nboFallbackReason = (data.nbo_fallback_reason as string) ?? null
        store.callState = 'data_loaded'
        break
      }

      case 'order_result': {
        const data = msg.data as Record<string, unknown>
        store.order = data.order as typeof store.order
        store.notification = data.notification as typeof store.notification
        store.callState = 'order_complete'
        break
      }

      case 'error': {
        store.errorMessage = msg.message as string
        store.errorStep = msg.step as string
        const step = msg.step as string
        if (step && store.progressSteps[step] !== undefined) {
          store.progressSteps[step] = 'error'
        }
        store.callState = 'error'
        break
      }
    }
  })

  onUnmounted(unsubscribe)

  return { pendingOfferSdp }
}
