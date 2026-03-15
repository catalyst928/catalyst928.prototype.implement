<template>
  <div class="card">
    <h3 class="card-title">Customer</h3>
    <div class="field">
      <span class="field-label">Name</span>
      <span class="field-value">{{ customer.name }}</span>
    </div>
    <div class="field">
      <span class="field-label">Category</span>
      <span class="badge" :class="badgeClass">{{ capitalize(customer.customer_category) }}</span>
    </div>
    <div class="field">
      <span class="field-label">Product</span>
      <span class="field-value">{{ customer.product_name }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Customer } from '../stores/sessionStore'

const props = defineProps<{ customer: Customer }>()

const badgeClass = computed(() => {
  const cat = props.customer.customer_category?.toLowerCase()
  if (cat === 'gold') return 'badge-gold'
  if (cat === 'silver') return 'badge-silver'
  if (cat === 'bronze') return 'badge-bronze'
  return 'badge-default'
})

function capitalize(s: string): string {
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : ''
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

.badge {
  border-radius: 9999px;
  padding: 2px 10px;
  font-size: 0.75rem;
  font-weight: 600;
}

.badge-gold {
  background: #fef3c7;
  color: #92400e;
}

.badge-silver {
  background: #f3f4f6;
  color: #4b5563;
}

.badge-bronze {
  background: #fed7aa;
  color: #9a3412;
}

.badge-default {
  background: #e5e7eb;
  color: #374151;
}
</style>
