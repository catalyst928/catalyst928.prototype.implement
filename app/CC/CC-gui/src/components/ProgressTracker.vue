<template>
  <div class="progress-tracker" aria-live="polite">
    <div v-for="(step, index) in steps" :key="step.key" class="step">
      <div class="step-indicator">
        <span v-if="step.status === 'pending'" class="icon icon-pending" />
        <span v-else-if="step.status === 'running'" class="icon icon-running">
          <svg width="20" height="20" viewBox="0 0 20 20">
            <circle cx="10" cy="10" r="8" fill="none" stroke="var(--color-info)" stroke-width="2" stroke-dasharray="40 12" class="spinner" />
          </svg>
        </span>
        <span v-else-if="step.status === 'done'" class="icon icon-done">
          <svg width="20" height="20" viewBox="0 0 20 20">
            <circle cx="10" cy="10" r="9" fill="var(--color-success)" />
            <path d="M6 10l3 3 5-6" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </span>
        <span v-else class="icon icon-error">
          <svg width="20" height="20" viewBox="0 0 20 20">
            <circle cx="10" cy="10" r="9" fill="var(--color-error)" />
            <path d="M7 7l6 6M13 7l-6 6" stroke="#fff" stroke-width="2" stroke-linecap="round" />
          </svg>
        </span>
        <div v-if="index < steps.length - 1" class="connector" :class="{ 'connector-done': step.status === 'done' }" />
      </div>
      <span class="step-label" :class="{ 'step-muted': step.status === 'pending', 'step-error': step.status === 'error' }">
        {{ step.label }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useSessionStore, type StepStatus } from '../stores/sessionStore'

const store = useSessionStore()

const stepDefs = [
  { key: 'query_customer', label: 'Query Customer' },
  { key: 'query_bill', label: 'Query Bill' },
  { key: 'get_ai_model_status', label: 'Check AI Model' },
  { key: 'get_nbo', label: 'Get Recommendations' },
  { key: 'verify_identity', label: 'Verify Identity' },
  { key: 'create_order', label: 'Create Order' },
  { key: 'send_notification', label: 'Send Notification' },
]

const steps = computed(() =>
  stepDefs.map((d) => ({
    ...d,
    status: store.progressSteps[d.key] as StepStatus,
  }))
)
</script>

<style scoped>
.progress-tracker {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.step {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.step-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
}

.icon {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon-pending {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 2px solid var(--color-neutral);
}

.icon-running svg {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.connector {
  width: 2px;
  height: 20px;
  background: var(--color-border);
}

.connector-done {
  background: var(--color-success);
}

.step-label {
  font-size: 0.85rem;
  line-height: 20px;
  color: var(--color-text);
}

.step-muted {
  color: var(--color-neutral);
}

.step-error {
  color: var(--color-error);
}
</style>
