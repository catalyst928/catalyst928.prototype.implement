<template>
  <div class="notice">
    <svg width="18" height="18" viewBox="0 0 20 20" fill="var(--color-info)">
      <circle cx="10" cy="10" r="9" fill="none" stroke="var(--color-info)" stroke-width="2" />
      <text x="10" y="14" text-anchor="middle" fill="var(--color-info)" font-size="12" font-weight="bold">i</text>
    </svg>
    <span>{{ message }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ reason: string | null }>()

const message = computed(() => {
  if (props.reason === 'model_inactive') return 'AI model inactive — fallback used'
  if (props.reason === 'ollama_unavailable') return 'NBO engine unavailable — fallback used'
  return 'Fallback recommendations used'
})
</script>

<style scoped>
.notice {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  padding: 10px 16px;
  font-size: 0.875rem;
  color: #1e40af;
}
</style>
