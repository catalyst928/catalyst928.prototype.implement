import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'

export type GuiCallState =
  | 'idle'
  | 'ringing'
  | 'call_active'
  | 'data_loaded'
  | 'ordering'
  | 'order_complete'
  | 'call_ended'
  | 'error'

export interface Customer {
  id: string
  name: string
  customer_category: string
  product_name: string
}

export interface Bill {
  bucket_balance: number
  bucket_balance_unit: string
  due_date: string
  bill_amount: number
  bill_amount_unit: string
  plan_usage_pct: number
}

export interface NboItem {
  id: string
  priority: number
  offering_id: string
  name: string
  description: string
  price: number
  price_unit: string
}

export interface Nbo {
  id: string
  recommendation_item: NboItem[]
}

export interface Order {
  order_id: string
  state: string
  order_date: string
}

export interface Notification {
  message_id: string
  status: 'sent' | 'failed'
  sent_at: string
}

export type StepStatus = 'pending' | 'running' | 'done' | 'error'

const STEP_KEYS = [
  'query_customer',
  'query_bill',
  'get_ai_model_status',
  'get_nbo',
  'verify_identity',
  'create_order',
  'send_notification',
] as const

function defaultProgressSteps(): Record<string, StepStatus> {
  const steps: Record<string, StepStatus> = {}
  for (const key of STEP_KEYS) {
    steps[key] = 'pending'
  }
  return steps
}

export const useSessionStore = defineStore('session', () => {
  const callState = ref<GuiCallState>('idle')
  const localStream = ref<MediaStream | null>(null)
  const remoteStream = ref<MediaStream | null>(null)
  const callerPhone = ref<string>('')

  const customer = ref<Customer | null>(null)
  const bill = ref<Bill | null>(null)
  const nbo = ref<Nbo | null>(null)
  const nboFallback = ref<boolean>(false)
  const nboFallbackReason = ref<string | null>(null)
  const selectedOfferId = ref<string | null>(null)

  const progressSteps = reactive<Record<string, StepStatus>>(defaultProgressSteps())

  const order = ref<Order | null>(null)
  const notification = ref<Notification | null>(null)

  const errorMessage = ref<string>('')
  const errorStep = ref<string | null>(null)

  function reset() {
    callState.value = 'idle'
    localStream.value = null
    remoteStream.value = null
    callerPhone.value = ''
    customer.value = null
    bill.value = null
    nbo.value = null
    nboFallback.value = false
    nboFallbackReason.value = null
    selectedOfferId.value = null
    order.value = null
    notification.value = null
    errorMessage.value = ''
    errorStep.value = null
    const defaults = defaultProgressSteps()
    for (const key of STEP_KEYS) {
      progressSteps[key] = defaults[key]
    }
  }

  return {
    callState,
    localStream,
    remoteStream,
    callerPhone,
    customer,
    bill,
    nbo,
    nboFallback,
    nboFallbackReason,
    selectedOfferId,
    progressSteps,
    order,
    notification,
    errorMessage,
    errorStep,
    reset,
  }
})
