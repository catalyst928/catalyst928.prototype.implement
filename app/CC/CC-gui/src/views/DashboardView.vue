<template>
  <div class="dashboard">
    <!-- Header -->
    <header class="header">
      <h1 class="header-title">CC-gui — Agent Dashboard</h1>
      <span v-if="store.callerPhone" class="caller-info">Caller: {{ formatPhone(store.callerPhone) }}</span>
    </header>

    <!-- Incoming Call Banner -->
    <IncomingCallBanner
      v-if="store.callState === 'ringing'"
      @answer="handleAnswer"
    />

    <div class="layout">
      <!-- Left Sidebar -->
      <aside class="sidebar">
        <VideoPanel v-if="showVideo" />
        <div v-else class="video-placeholder">
          <span class="placeholder-text">No Video</span>
        </div>

        <ProgressTracker />

        <CallControls
          v-if="showCallControls"
          @end-call="handleEndCall"
        />
      </aside>

      <!-- Main Content -->
      <main class="main-content">
        <!-- Idle state -->
        <div v-if="store.callState === 'idle'" class="idle-state">
          <div class="idle-indicator" />
          <p class="idle-text">Waiting for incoming call</p>
        </div>

        <!-- Error Banner -->
        <Transition name="fade">
          <ErrorBanner
            v-if="store.callState === 'error'"
            :step="store.errorStep"
            :message="store.errorMessage"
          />
        </Transition>

        <!-- Data Cards (visible from data_loaded onward) -->
        <template v-if="showDataCards">
          <Transition name="slide">
            <div v-if="store.customer && store.bill" class="data-row">
              <CustomerCard :customer="store.customer" />
              <BillSummaryCard :bill="store.bill" />
            </div>
          </Transition>

          <Transition name="slide">
            <NboFallbackNotice
              v-if="store.nboFallback"
              :reason="store.nboFallbackReason"
            />
          </Transition>

          <Transition name="slide">
            <NboList
              v-if="store.nbo"
              :items="store.nbo.recommendation_item"
            />
          </Transition>

          <!-- Order Action Bar (hidden after order_complete) -->
          <OrderActionBar
            v-if="store.callState === 'data_loaded' || store.callState === 'ordering'"
            @place-order="handlePlaceOrder"
          />

          <!-- Order Result -->
          <Transition name="slide">
            <OrderResultCard
              v-if="store.order"
              :order="store.order"
              :notification="store.notification"
            />
          </Transition>
        </template>

        <!-- Active call but no data yet -->
        <div v-if="store.callState === 'call_active' && !store.customer" class="loading-state">
          <p class="loading-text">Retrieving customer data…</p>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import { useSessionStore } from '../stores/sessionStore'
import { signaling } from '../api/signaling'
import { useWebRTC } from '../composables/useWebRTC'
import { useMessageHandler } from '../composables/useMessageHandler'
import { placeOrder } from '../api/orderApi'

import IncomingCallBanner from '../components/IncomingCallBanner.vue'
import VideoPanel from '../components/VideoPanel.vue'
import ProgressTracker from '../components/ProgressTracker.vue'
import CallControls from '../components/CallControls.vue'
import CustomerCard from '../components/CustomerCard.vue'
import BillSummaryCard from '../components/BillSummaryCard.vue'
import NboList from '../components/NboList.vue'
import NboFallbackNotice from '../components/NboFallbackNotice.vue'
import OrderActionBar from '../components/OrderActionBar.vue'
import OrderResultCard from '../components/OrderResultCard.vue'
import ErrorBanner from '../components/ErrorBanner.vue'

const store = useSessionStore()
const { answerCall, endCall } = useWebRTC()
const { pendingOfferSdp } = useMessageHandler()

// Connect to signaling on mount
signaling.connect()

const showVideo = computed(() =>
  ['call_active', 'data_loaded', 'ordering', 'order_complete'].includes(store.callState)
)

const showCallControls = computed(() =>
  ['call_active', 'data_loaded', 'ordering', 'order_complete'].includes(store.callState)
)

const showDataCards = computed(() =>
  ['data_loaded', 'ordering', 'order_complete', 'call_ended'].includes(store.callState)
)

// Auto-reset timer
let resetTimer: ReturnType<typeof setTimeout> | null = null

watch(() => store.callState, (state) => {
  if (resetTimer) {
    clearTimeout(resetTimer)
    resetTimer = null
  }
  if (state === 'call_ended' || state === 'error') {
    resetTimer = setTimeout(() => {
      store.reset()
    }, 10_000)
  }
})

async function handleAnswer() {
  if (pendingOfferSdp.value) {
    await answerCall(pendingOfferSdp.value)
    pendingOfferSdp.value = null
  }
}

async function handleEndCall() {
  await endCall()
}

async function handlePlaceOrder() {
  if (!store.customer || !store.selectedOfferId) return
  store.callState = 'ordering'

  const resp = await placeOrder(store.customer.id, store.selectedOfferId)
  if (resp.error) {
    store.errorMessage = resp.error.message
    store.errorStep = resp.error.step
    store.callState = 'error'
  }
  // Success case is handled by WebSocket order_result message
}

function formatPhone(phone: string): string {
  const digits = phone.replace(/\D/g, '')
  if (digits.length === 11) {
    return `${digits.slice(0, 3)}-${digits.slice(3, 7)}-${digits.slice(7)}`
  }
  if (digits.length === 10) {
    return `${digits.slice(0, 3)}-${digits.slice(3, 6)}-${digits.slice(6)}`
  }
  if (digits.length === 12) {
    return `+${digits.slice(0, 2)}-${digits.slice(2, 5)}-${digits.slice(5, 8)}-${digits.slice(8)}`
  }
  return phone
}
</script>

<style scoped>
.dashboard {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  background: var(--color-primary);
  color: #fff;
  padding: 12px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-title {
  font-size: 1.125rem;
  font-weight: 600;
}

.caller-info {
  font-size: 0.9rem;
  opacity: 0.9;
}

.layout {
  display: grid;
  grid-template-columns: 320px 1fr;
  flex: 1;
  min-height: 0;
}

.sidebar {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  border-right: 1px solid var(--color-border);
  background: var(--color-surface);
}

.video-placeholder {
  width: 100%;
  aspect-ratio: 16 / 9;
  background: #1a1a2e;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.placeholder-text {
  color: #6b7280;
  font-size: 0.85rem;
}

.main-content {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
}

.data-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

@media (max-width: 1199px) {
  .data-row {
    grid-template-columns: 1fr;
  }
}

.idle-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
}

.idle-indicator {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--color-neutral);
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.4; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.2); }
}

.idle-text {
  color: var(--color-text-muted);
  font-size: 1.125rem;
}

.loading-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-text {
  color: var(--color-text-muted);
  font-size: 1rem;
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-enter-active {
  transition: all 0.4s ease;
}
.slide-enter-from {
  opacity: 0;
  transform: translateY(12px);
}
</style>
