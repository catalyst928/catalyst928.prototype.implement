<template>
  <div class="card">
    <h3 class="card-title">Recommendations</h3>
    <div
      v-for="item in sortedItems"
      :key="item.id"
      class="nbo-row"
      :class="{ selected: selectedId === item.offering_id }"
      role="radio"
      :aria-checked="selectedId === item.offering_id"
      tabindex="0"
      @click="select(item.offering_id)"
      @keydown.enter="select(item.offering_id)"
      @keydown.space.prevent="select(item.offering_id)"
    >
      <span class="radio">
        <span v-if="selectedId === item.offering_id" class="radio-dot" />
      </span>
      <span class="rank">#{{ item.priority }}</span>
      <div class="nbo-info">
        <span class="nbo-name">{{ item.name }}</span>
        <span class="nbo-desc" :title="item.description">{{ truncate(item.description, 120) }}</span>
      </div>
      <span class="nbo-price">{{ formatCurrency(item.price, item.price_unit) }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useSessionStore, type NboItem } from '../stores/sessionStore'

const props = defineProps<{ items: NboItem[] }>()
const store = useSessionStore()

const selectedId = computed(() => store.selectedOfferId)

const sortedItems = computed(() =>
  [...props.items].sort((a, b) => a.priority - b.priority)
)

function select(offeringId: string) {
  store.selectedOfferId = offeringId
}

function truncate(text: string, max: number): string {
  return text.length > max ? text.slice(0, max) + '…' : text
}

function formatCurrency(value: number, unit: string): string {
  return `${unit} ${value.toFixed(2)}`
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

.nbo-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  cursor: pointer;
  border-left: 3px solid transparent;
  transition: background 0.15s, border-color 0.15s;
}

.nbo-row:hover {
  background: #f9fafb;
}

.nbo-row.selected {
  background: #eff6ff;
  border-left-color: var(--color-info);
}

.nbo-row:focus-visible {
  outline: 2px solid var(--color-info);
  outline-offset: -2px;
}

.radio {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid var(--color-neutral);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.selected .radio {
  border-color: var(--color-info);
}

.radio-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--color-info);
}

.rank {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--color-text-muted);
  min-width: 24px;
}

.nbo-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.nbo-name {
  font-weight: 600;
  font-size: 0.95rem;
}

.nbo-desc {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nbo-price {
  font-weight: 700;
  font-size: 1rem;
  white-space: nowrap;
}
</style>
