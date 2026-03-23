<template>
  <div class="chat-messages" ref="containerRef">
    <ChatMessageItem
      v-for="item in messages"
      :key="item.id"
      :item="item"
      @play-audio="$emit('play-audio', $event)"
    />
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import ChatMessageItem from './ChatMessageItem.vue'

const props = defineProps({
  messages: Array
})

defineEmits(['play-audio'])

const containerRef = ref(null)

watch(
  () => props.messages,
  async () => {
    await nextTick()
    containerRef.value.scrollTop = containerRef.value.scrollHeight
  },
  { deep: true }
)
</script>