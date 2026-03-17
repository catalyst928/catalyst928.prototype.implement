<template>
  <div class="card">
    <h3 class="card-title">Bill Summary</h3>
    <div class="field">
      <span class="field-label">Balance</span>
      <span class="field-value large">{{ formatCurrency(bill.bucket_balance, bill.bucket_balance_unit) }}</span>
    </div>
    <div class="field">
      <span class="field-label">Bill Amount</span>
      <span class="field-value large">{{ formatCurrency(bill.bill_amount, bill.bill_amount_unit) }}</span>
    </div>
    <div class="field">
      <span class="field-label">Due Date</span>
      <span class="field-value">{{ formatDate(bill.due_date) }}</span>
    </div>
    <div class="field usage-field">
      <span class="field-label">Plan Usage</span>
      <span class="field-value">{{ bill.plan_usage_pct != null ? bill.plan_usage_pct + '%' : '—' }}</span>
    </div>
    <div class="usage-bar">
      <div class="usage-fill" :class="usageColor" :style="{ width: (bill.plan_usage_pct ?? 0) + '%' }" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Bill } from '../stores/sessionStore'

const props = defineProps<{ bill: Bill }>()

const usageColor = computed(() => {
  const pct = props.bill.plan_usage_pct
  if (pct == null) return 'fill-green'
  if (pct > 90) return 'fill-red'
  if (pct >= 70) return 'fill-amber'
  return 'fill-green'
})

function formatCurrency(value: number | null, unit: string | null): string {
  if (value == null || unit == null) return '—'
  return `${unit} ${value.toFixed(2)}`
}

function formatDate(iso: string | null): string {
  if (!iso) return '—'
  const d = new Date(iso)
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  return `${String(d.getDate()).padStart(2, '0')} ${months[d.getMonth()]} ${d.getFullYear()}`
}
</script>

<style scoped>
.card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 20px;
}

.card-title {
  font-size: 0.85rem;
  text-transform: uppercase;
  color: var(--color-text-muted);
  font-weight: 600;
  letter-spacing: 0.05em;
  margin-bottom: 12px;
}

.field {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
}

.field-label {
  color: var(--color-text-muted);
  font-size: 0.875rem;
}

.field-value {
  font-weight: 500;
}

.large {
  font-size: 1.25rem;
  font-weight: 700;
}

.usage-field {
  margin-bottom: 4px;
}

.usage-bar {
  width: 100%;
  height: 8px;
  background: var(--color-border);
  border-radius: 4px;
  overflow: hidden;
}

.usage-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease;
}

.fill-green { background: var(--color-success); }
.fill-amber { background: var(--color-warning); }
.fill-red { background: var(--color-error); }
</style>
