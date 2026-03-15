<template>
  <div class="call-controls">
    <button class="btn-end" aria-label="End call" @click="$emit('endCall')">
      End Call
    </button>
  </div>
</template>

<script setup lang="ts">
defineEmits<{ endCall: [] }>()
</script>

<style scoped>
.call-controls {
  padding: 12px 0;
}

.btn-end {
  width: 100%;
  background: var(--color-error);
  color: #fff;
  border: none;
  border-radius: 24px;
  padding: 10px 24px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}

.btn-end:hover {
  opacity: 0.9;
}

.btn-end:focus-visible {
  outline: 2px solid var(--color-info);
  outline-offset: 2px;
}
</style>
