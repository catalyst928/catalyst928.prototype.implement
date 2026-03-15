<template>
  <div class="card">
    <h3 class="card-title">Order Confirmation</h3>
    <div class="field">
      <span class="field-label">Order ID</span>
      <span class="field-value">{{ order.order_id }}</span>
    </div>
    <div class="field">
      <span class="field-label">Status</span>
      <span class="badge badge-blue">{{ capitalize(order.state) }}</span>
    </div>
    <div class="field">
      <span class="field-label">Order Date</span>
      <span class="field-value">{{ formatDateTime(order.order_date) }}</span>
    </div>

    <div v-if="notification" class="notification-section">
      <h3 class="card-title">Notification</h3>
      <div class="field">
        <span class="field-label">Message ID</span>
        <span class="field-value">{{ notification.message_id }}</span>
      </div>
      <div class="field">
        <span class="field-label">Status</span>
        <span class="badge" :class="notification.status === 'sent' ? 'badge-green' : 'badge-red'">
          {{ capitalize(notification.status) }}
        </span>
      </div>
      <div class="field">
        <span class="field-label">Sent At</span>
        <span class="field-value">{{ formatDateTime(notification.sent_at) }}</span>
      </div>
      <div v-if="notification.status === 'failed'" class="warning-inline">
        Notification Failed — the order itself was placed successfully.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Order, Notification } from '../stores/sessionStore'

defineProps<{ order: Order; notification: Notification | null }>()

function capitalize(s: string): string {
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : ''
}

function formatDateTime(iso: string): string {
  const d = new Date(iso)
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  return `${String(d.getDate()).padStart(2, '0')} ${months[d.getMonth()]} ${d.getFullYear()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
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

.badge-blue { background: #dbeafe; color: #1e40af; }
.badge-green { background: #dcfce7; color: #166534; }
.badge-red { background: #fee2e2; color: #991b1b; }

.notification-section {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--color-border);
}

.warning-inline {
  margin-top: 8px;
  background: #fef3c7;
  border: 1px solid #fde68a;
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 0.8rem;
  color: #92400e;
}
</style>
