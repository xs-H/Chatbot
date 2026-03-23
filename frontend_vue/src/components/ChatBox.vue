<template>
  <div class="chat-box" :class="{ expanded: chatStarted }">
    <p v-if="!chatStarted">你可以问我任何问题...</p>

    <ChatMessages
      v-if="messages.length > 0"
      :messages="messages"
      @play-audio="$emit('play-audio', $event)"
    />

    <ChatInput
      :model-value="inputText"
      :is-recording="isRecording"
      @update:model-value="$emit('update:input-text', $event)"
      @send="$emit('send')"
      @toggle-recording="$emit('toggle-recording')"
    />
  </div>
</template>

<script setup>
import ChatMessages from './ChatMessages.vue'
import ChatInput from './ChatInput.vue'

defineProps({
  chatStarted: Boolean,
  messages: {
    type: Array,
    default: () => []
  },
  inputText: {
    type: String,
    default: ''
  },
  isRecording: Boolean
})

defineEmits(['update:input-text', 'send', 'toggle-recording', 'play-audio'])
</script>