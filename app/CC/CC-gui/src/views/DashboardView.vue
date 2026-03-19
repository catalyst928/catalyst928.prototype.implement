<template>
  <div class="aicc-shell">
    <!-- Incoming Call Banner (overlay) -->
    <IncomingCallBanner
      v-if="store.callState === 'ringing'"
      @answer="handleAnswer"
    />

    <!-- Top Header Bar -->
    <header class="top-bar">
      <div class="top-bar-left">
        <svg class="brand-icon" width="28" height="28" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="11" stroke="#4f8cf7" stroke-width="2"/>
          <path d="M8 12a4 4 0 1 1 8 0 4 4 0 0 1-8 0z" fill="#4f8cf7"/>
        </svg>
        <span class="brand-title">Catalyst C26.0.928 Contact Center</span>
      </div>
      <div class="top-bar-center">
        <button class="header-btn header-btn-outline">
          Sign Out
        </button>
        <span class="status-badge" :class="statusClass">
          <span class="status-dot" />
          {{ statusLabel }}
        </span>
      </div>
      <div class="top-bar-right">
        <span v-if="store.callerPhone" class="caller-phone-chip">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/>
          </svg>
          {{ formatPhone(store.callerPhone) }}
        </span>
        <span class="header-lang">English</span>
        <div class="agent-avatar">A</div>
        <span class="agent-name">Agent 1</span>
      </div>
    </header>

    <div class="body-layout">
      <!-- Left Navigation Sidebar -->
      <nav class="left-nav">
        <a
          v-for="item in navItems"
          :key="item.id"
          class="nav-item"
          :class="{ active: activeNav === item.id }"
          @click="activeNav = item.id"
        >
          <component :is="item.icon" class="nav-icon" />
          <span class="nav-label">{{ item.label }}</span>
          <svg v-if="item.children" class="nav-chevron" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
        </a>
        <div class="nav-collapse-btn">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
        </div>
      </nav>

      <div class="content-area">
        <!-- Tab Bar -->
        <div class="tab-bar">
          <div class="tab" :class="{ 'tab-active': activeTab === 'home' }" @click="activeTab = 'home'">
            Home Page
            <span class="tab-close">&times;</span>
          </div>
          <div class="tab" :class="{ 'tab-active': activeTab === 'call' }" @click="activeTab = 'call'">
            Call
            <span class="tab-close">&times;</span>
          </div>
        </div>

        <!-- Action Buttons Row -->
        <div class="action-row">
          <button class="action-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 12l2 2 4-4"/></svg>
            Verify Identity
          </button>
          <button class="action-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
            Service Guidance
          </button>
          <button class="action-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M8 13h8"/><path d="M8 17h8"/></svg>
            Smart Form Filling
          </button>
          <button class="action-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 3"/></svg>
            Call Reason
          </button>
        </div>

        <!-- Main Split Panels -->
        <div class="panels">
          <!-- Center Panel: Call Content -->
          <div class="center-panel">
            <div class="call-area">
              <!-- Call header with icons -->
              <div class="call-header">
                <span class="call-dash">&mdash;</span>
                <div class="call-icons">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#6b7280" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#6b7280" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="M7 15l5-5 5 5"/></svg>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#6b7280" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                </div>
              </div>

              <!-- Real-time transfer tab -->
              <div class="transfer-tabs">
                <span class="transfer-tab transfer-tab-active">Customer 360°</span>
              </div>

              <!-- Content dropdown -->
              <div class="content-filter">
                <span class="content-filter-link">All content <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg></span>
              </div>

              <!-- Main call content area -->
              <div class="call-body">
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

                <!-- Active call but no data yet -->
                <div v-if="store.callState === 'call_active' && !store.customer" class="loading-state">
                  <p class="loading-text">Retrieving customer data...</p>
                </div>

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

                  <!-- Order Action Bar -->
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
              </div>

              <!-- Status Bar -->
              <div class="status-bar">
                <span>Number of current sign-in calls: <b>{{ store.callState !== 'idle' ? 1 : 0 }}</b></span>
                <span>Average call duration (s): <b>{{ callDuration }}</b></span>
                <span>Number of current queuing customers: <b>&mdash;</b></span>
              </div>
            </div>
          </div>

          <!-- Right Panel -->
          <div class="right-panel">
            <!-- Floating side icons -->
            <div class="side-icons">
              <div class="side-icon-btn">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6b7280" stroke-width="2"><circle cx="12" cy="8" r="4"/><path d="M20 21a8 8 0 1 0-16 0"/></svg>
              </div>
              <div class="side-icon-btn">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6b7280" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
              </div>
            </div>

            <!-- Video & Progress Section (original left flow) -->
            <div class="right-section">
              <div class="section-header" @click="toggleSection('video')">
                <h3 class="section-title">Call & Progress</h3>
                <svg :class="{ 'chevron-collapsed': !sections.video }" class="section-chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>
              </div>
              <div v-show="sections.video" class="section-body">
                <VideoPanel v-if="showVideo" />
                <div v-else class="video-placeholder">
                  <span class="placeholder-text">No Video</span>
                </div>
                <ProgressTracker />
                <CallControls
                  v-if="showCallControls"
                  @end-call="handleEndCall"
                />
              </div>
            </div>

            <!-- Customer Information Section -->
            <div class="right-section">
              <div class="section-header" @click="toggleSection('customer')">
                <h3 class="section-title">Customer Information</h3>
                <svg :class="{ 'chevron-collapsed': !sections.customer }" class="section-chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>
              </div>
              <div v-show="sections.customer" class="section-body">
                <div class="no-data">No Data Available.</div>
              </div>
            </div>

            <!-- Contact Records Section -->
            <div class="right-section">
              <div class="section-header" @click="toggleSection('contact')">
                <h3 class="section-title">Contact Records</h3>
                <svg :class="{ 'chevron-collapsed': !sections.contact }" class="section-chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>
              </div>
              <div v-show="sections.contact" class="section-body">
                <div class="contact-filters">
                  <select class="filter-select">
                    <option>Media Type</option>
                    <option>Voice</option>
                    <option>Video</option>
                    <option>Chat</option>
                  </select>
                  <button class="filter-btn">More <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg></button>
                </div>
                <div class="no-data">No Data Available.</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, reactive, watch } from 'vue'
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

// UI state
const activeNav = ref('call')
const activeTab = ref('call')
const callDuration = ref(0)
let durationInterval: ReturnType<typeof setInterval> | null = null

const sections = reactive({
  video: true,
  customer: true,
  contact: true,
})

function toggleSection(key: keyof typeof sections) {
  sections[key] = !sections[key]
}

// Navigation items
const navItems = [
  { id: 'home', label: 'Home Page', children: false, icon: NavIconHome },
  { id: 'chat', label: 'Online Chat', children: false, icon: NavIconChat },
  { id: 'call', label: 'Call', children: false, icon: NavIconCall },
  { id: 'social', label: 'Social Media', children: true, icon: NavIconSocial },
  { id: 'outbound', label: 'Outbound Call', children: true, icon: NavIconOutbound },
  { id: 'survey', label: 'Survey', children: true, icon: NavIconSurvey },
  { id: 'message', label: 'Message', children: false, icon: NavIconMessage },
  { id: 'case', label: 'Case 2.0', children: true, icon: NavIconCase },
  { id: 'kb', label: 'Knowledge Base', children: true, icon: NavIconKB },
  { id: 'training', label: 'Business Training', children: true, icon: NavIconTraining },
  { id: 'inspection', label: 'Inspection', children: true, icon: NavIconInspection },
  { id: 'text', label: 'Text Analysis', children: true, icon: NavIconText },
  { id: 'monitoring', label: 'Monitoring', children: true, icon: NavIconMonitoring },
  { id: 'ivr', label: 'IVR Analysis', children: true, icon: NavIconIVR },
  { id: 'report', label: 'Report', children: false, icon: NavIconReport },
  { id: 'history', label: 'Contact History', children: true, icon: NavIconHistory },
  { id: 'customer-center', label: 'Customer Center', children: true, icon: NavIconCustomer },
  { id: 'config', label: 'Configuration Center', children: false, icon: NavIconConfig },
]

const statusClass = computed(() => {
  const s = store.callState
  if (s === 'idle') return 'status-idle'
  if (s === 'ringing') return 'status-ringing'
  if (s === 'error') return 'status-error'
  return 'status-busy'
})

const statusLabel = computed(() => {
  const s = store.callState
  if (s === 'idle') return 'Idle'
  if (s === 'ringing') return 'Ringing'
  if (s === 'error') return 'Error'
  if (s === 'call_ended') return 'Wrap-up'
  return 'Busy'
})

const showVideo = computed(() =>
  ['call_active', 'data_loaded', 'ordering', 'order_complete'].includes(store.callState)
)

const showCallControls = computed(() =>
  ['call_active', 'data_loaded', 'ordering', 'order_complete'].includes(store.callState)
)

const showDataCards = computed(() =>
  ['data_loaded', 'ordering', 'order_complete', 'call_ended'].includes(store.callState)
)

// Call duration timer
watch(() => store.callState, (state) => {
  if (state === 'call_active') {
    callDuration.value = 0
    durationInterval = setInterval(() => { callDuration.value++ }, 1000)
  } else if (state === 'idle' || state === 'call_ended') {
    if (durationInterval) { clearInterval(durationInterval); durationInterval = null }
  }
})

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
      callDuration.value = 0
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

/* ── Inline Nav Icon Components ── */
function NavIconHome() { return null }
function NavIconChat() { return null }
function NavIconCall() { return null }
function NavIconSocial() { return null }
function NavIconOutbound() { return null }
function NavIconSurvey() { return null }
function NavIconMessage() { return null }
function NavIconCase() { return null }
function NavIconKB() { return null }
function NavIconTraining() { return null }
function NavIconInspection() { return null }
function NavIconText() { return null }
function NavIconMonitoring() { return null }
function NavIconIVR() { return null }
function NavIconReport() { return null }
function NavIconHistory() { return null }
function NavIconCustomer() { return null }
function NavIconConfig() { return null }
</script>

<style scoped>
/* ════════════════════════════════════
   AICC-Style Shell Layout
   ════════════════════════════════════ */

.aicc-shell {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
  background: var(--color-bg);
}

/* ── Top Header Bar ── */
.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 48px;
  padding: 0 16px;
  background: #fff;
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
  z-index: 10;
}

.top-bar-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.brand-icon {
  flex-shrink: 0;
}

.brand-title {
  font-size: 1rem;
  font-weight: 700;
  color: var(--color-text);
  white-space: nowrap;
}

.top-bar-center {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-btn-outline {
  background: #fff;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  padding: 4px 14px;
  font-size: 0.8rem;
  color: var(--color-text);
  cursor: pointer;
  font-weight: 500;
}
.header-btn-outline:hover {
  background: #f9fafb;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8rem;
  font-weight: 500;
  padding: 3px 12px;
  border-radius: 4px;
  border: 1px solid var(--color-border);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-idle .status-dot { background: var(--color-neutral); }
.status-busy .status-dot { background: #ef4444; }
.status-ringing .status-dot { background: #f59e0b; animation: blink 1s infinite; }
.status-error .status-dot { background: #ef4444; }

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.top-bar-right {
  display: flex;
  align-items: center;
  gap: 14px;
}

.caller-phone-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 0.8rem;
  color: var(--color-success);
  font-weight: 500;
}

.header-lang {
  font-size: 0.8rem;
  color: var(--color-text-muted);
}

.agent-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--color-primary);
  color: #fff;
  font-size: 0.75rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.agent-name {
  font-size: 0.8rem;
  color: var(--color-text);
  font-weight: 500;
}

/* ── Body Layout ── */
.body-layout {
  display: flex;
  flex: 1;
  min-height: 0;
}

/* ── Left Navigation ── */
.left-nav {
  width: 200px;
  flex-shrink: 0;
  background: #fff;
  border-right: 1px solid var(--color-border);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  padding: 4px 0;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  font-size: 0.85rem;
  color: var(--color-text);
  cursor: pointer;
  text-decoration: none;
  border-left: 3px solid transparent;
  transition: background 0.15s, border-color 0.15s;
  user-select: none;
}

.nav-item:hover {
  background: #f3f4f6;
}

.nav-item.active {
  background: #eff6ff;
  border-left-color: var(--color-primary);
  color: var(--color-primary);
  font-weight: 600;
}

.nav-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  color: var(--color-text-muted);
}

.nav-item.active .nav-icon {
  color: var(--color-primary);
}

.nav-label {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nav-chevron {
  flex-shrink: 0;
  color: var(--color-text-muted);
}

.nav-collapse-btn {
  margin-top: auto;
  display: flex;
  justify-content: flex-end;
  padding: 8px 12px;
  color: var(--color-text-muted);
  cursor: pointer;
}

/* ── Content Area ── */
.content-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

/* ── Tab Bar ── */
.tab-bar {
  display: flex;
  align-items: stretch;
  background: #fff;
  border-bottom: 1px solid var(--color-border);
  padding: 0 8px;
  height: 36px;
  flex-shrink: 0;
}

.tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 16px;
  font-size: 0.8rem;
  color: var(--color-text-muted);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  user-select: none;
  transition: color 0.15s;
}

.tab:hover {
  color: var(--color-text);
}

.tab-active {
  color: var(--color-text);
  font-weight: 500;
  border-bottom-color: var(--color-primary);
}

.tab-close {
  font-size: 1rem;
  line-height: 1;
  color: var(--color-text-muted);
  opacity: 0.5;
}
.tab-close:hover {
  opacity: 1;
}

/* ── Action Buttons Row ── */
.action-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  background: #fff;
  border-bottom: 1px solid var(--color-border);
  justify-content: flex-end;
  flex-shrink: 0;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #fff;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  padding: 6px 14px;
  font-size: 0.8rem;
  color: var(--color-text);
  cursor: pointer;
  font-weight: 500;
  transition: background 0.15s, border-color 0.15s;
}

.action-btn:hover {
  background: #f9fafb;
  border-color: #d1d5db;
}

/* ── Main Split Panels ── */
.panels {
  flex: 1;
  display: flex;
  min-height: 0;
  gap: 0;
}

/* ── Center Panel ── */
.center-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  padding: 12px;
}

.call-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  overflow: hidden;
}

.call-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  border-bottom: 1px solid var(--color-border);
}

.call-dash {
  color: var(--color-text);
  font-size: 1rem;
}

.call-icons {
  display: flex;
  align-items: center;
  gap: 12px;
}

.transfer-tabs {
  padding: 0 16px;
  border-bottom: 1px solid var(--color-border);
}

.transfer-tab {
  display: inline-block;
  padding: 8px 0;
  font-size: 0.85rem;
  color: var(--color-text-muted);
  cursor: pointer;
  border-bottom: 2px solid transparent;
}

.transfer-tab-active {
  color: var(--color-primary);
  font-weight: 500;
  border-bottom-color: var(--color-primary);
}

.content-filter {
  display: flex;
  justify-content: flex-end;
  padding: 8px 16px;
}

.content-filter-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.8rem;
  color: var(--color-primary);
  cursor: pointer;
}

.call-body {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.data-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
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
  font-size: 1rem;
}

.loading-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-text {
  color: var(--color-text-muted);
  font-size: 0.95rem;
}

.status-bar {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 8px 16px;
  background: #fafafa;
  border-top: 1px solid var(--color-border);
  font-size: 0.75rem;
  color: var(--color-text-muted);
  flex-shrink: 0;
}

.status-bar b {
  color: var(--color-text);
}

/* ── Right Panel ── */
.right-panel {
  width: 380px;
  flex-shrink: 0;
  background: var(--color-bg);
  border-left: 1px solid var(--color-border);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  position: relative;
}

.side-icons {
  position: absolute;
  top: 8px;
  right: -36px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 5;
}

.side-icon-btn {
  width: 32px;
  height: 32px;
  background: #fff;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}
.side-icon-btn:hover {
  background: #f3f4f6;
}

.right-section {
  background: #fff;
  border-bottom: 1px solid var(--color-border);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  cursor: pointer;
  user-select: none;
}
.section-header:hover {
  background: #fafafa;
}

.section-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text);
}

.section-chevron {
  transition: transform 0.2s;
  color: var(--color-text-muted);
}

.chevron-collapsed {
  transform: rotate(-90deg);
}

.section-body {
  padding: 0 16px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.no-data {
  text-align: center;
  color: var(--color-text-muted);
  font-size: 0.875rem;
  padding: 24px 0;
}

.contact-filters {
  display: flex;
  align-items: center;
  gap: 12px;
}

.filter-select {
  flex: 1;
  padding: 6px 12px;
  font-size: 0.8rem;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  background: #fff;
  color: var(--color-text);
  appearance: auto;
}

.filter-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: #fff;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  padding: 6px 14px;
  font-size: 0.8rem;
  color: var(--color-text);
  cursor: pointer;
  font-weight: 500;
}
.filter-btn:hover {
  background: #f9fafb;
}

.video-placeholder {
  width: 100%;
  aspect-ratio: 16 / 9;
  background: #1a1a2e;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.placeholder-text {
  color: #6b7280;
  font-size: 0.85rem;
}

/* ── Transitions ── */
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

/* ── Responsive ── */
@media (max-width: 1199px) {
  .left-nav {
    width: 52px;
  }
  .nav-label,
  .nav-chevron {
    display: none;
  }
  .nav-item {
    justify-content: center;
    padding: 10px 0;
  }
  .right-panel {
    width: 300px;
  }
}

@media (max-width: 899px) {
  .right-panel {
    display: none;
  }
  .action-row {
    flex-wrap: wrap;
  }
}
</style>
