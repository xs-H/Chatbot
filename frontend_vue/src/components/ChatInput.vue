<template>
  <div class="chat-input">
    <i class="icon fa-regular fa-image"></i>
    <i class="icon fa-solid fa-paperclip"></i>

    <textarea
      ref="textareaRef"
      :value="modelValue"
      placeholder="在这里输入内容..."
      @input="handleInput"
      @keydown="handleKeydown"
    ></textarea>

    <i
      class="icon fa-solid"
      :class="isRecording ? 'fa-stop recording' : 'fa-microphone'"
      @click="$emit('toggle-recording')"
    ></i>

    <i class="icon fa-solid fa-paper-plane" @click="$emit('send')"></i>

    <span v-show="isRecording" class="recording-indicator">录音中</span>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  isRecording: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:model-value', 'send', 'toggle-recording'])
const textareaRef = ref(null)

function adjustTextareaHeight() {
  const el = textareaRef.value
  if (!el) return
  el.style.height = 'auto'
  const newHeight = Math.min(Math.max(el.scrollHeight, 40), 120)
  el.style.height = `${newHeight}px`
}

function handleInput(event) {
  emit('update:model-value', event.target.value)
  adjustTextareaHeight()
}

function handleKeydown(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    emit('send')
  }
}

watch(
  () => props.modelValue,
  async () => {
    await nextTick()
    adjustTextareaHeight()
  }
)

onMounted(() => {
  adjustTextareaHeight()
})
</script>