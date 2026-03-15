<template>
  <div class="action-bar">
    <button
      class="btn-order"
      :disabled="!selectedOfferId || isOrdering"
      :class="{ loading: isOrdering }"
      aria-label="Place order for selected recommendation"
      @click="$emit('placeOrder')"
    >
      {{ isOrdering ? 'Placing Order…' : 'Place Order' }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useSessionStore } from '../stores/sessionStore'

defineEmits<{ placeOrder: [] }>()

const store = useSessionStore()
const selectedOfferId = computed(() => store.selectedOfferId)
const isOrdering = computed(() => store.callState === 'ordering')
</script>

<style scoped>
.action-bar {
  display: flex;
  justify-content: flex-end;
  padding: 8px 0;
}

.btn-order {
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: 24px;
  padding: 10px 32px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}

.btn-order:hover:not(:disabled) {
  opacity: 0.9;
}

.btn-order:disabled {
  opacity: 0.4;
  cursor: default;
}

.btn-order.loading {
  opacity: 0.7;
}

.btn-order:focus-visible {
  outline: 2px solid var(--color-info);
  outline-offset: 2px;
}
</style>
