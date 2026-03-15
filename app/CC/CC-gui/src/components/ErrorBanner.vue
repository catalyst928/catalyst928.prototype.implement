<template>
  <div class="error-banner" role="alert">
    <svg width="20" height="20" viewBox="0 0 20 20">
      <circle cx="10" cy="10" r="9" fill="var(--color-error)" />
      <path d="M10 6v5M10 13.5v.5" stroke="#fff" stroke-width="2" stroke-linecap="round" />
    </svg>
    <div class="error-content">
      <span v-if="step" class="error-step">{{ stepLabel(step) }}</span>
      <span class="error-message">{{ message }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ step: string | null; message: string }>()

const stepLabels: Record<string, string> = {
  query_customer: 'Query Customer',
  query_bill: 'Query Bill',
  get_ai_model_status: 'Check AI Model',
  get_nbo: 'Get Recommendations',
  verify_identity: 'Verify Identity',
  create_order: 'Create Order',
  send_notification: 'Send Notification',
}

function stepLabel(step: string): string {
  return stepLabels[step] ?? step
}
</script>

<style scoped>
.error-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #fee2e2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  padding: 12px 16px;
}

.error-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.error-step {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  color: #991b1b;
  letter-spacing: 0.05em;
}

.error-message {
  font-size: 0.875rem;
  color: #991b1b;
}
</style>
