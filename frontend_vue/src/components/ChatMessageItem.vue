<template>
  <!-- 用户消息 -->
  <div v-if="item.sender === 'user'" class="user-message-container">
    <div class="user-message">{{ item.text }}</div>
  </div>

  <!-- AI消息 -->
  <div v-else-if="item.sender === 'ai'" class="ai-message-container">
    <img class="ai-avatar" src="/images/character.jpg" alt="哪吒" />

    <div class="ai-message-content">
      <div class="ai-name">哪吒</div>
      <div class="ai-message">{{ item.text }}</div>

      <div v-if="item.audioUrls?.length" class="audio-wrapper">
        <button
          v-for="(audio, index) in item.audioUrls"
          :key="audio"
          class="audio-button"
          @click="$emit('play-audio', audio)"
        >
          <i class="fas fa-play"></i>
          播放{{ item.audioUrls.length > 1 ? index + 1 : '' }}
        </button>
      </div>
    </div>
  </div>

  <!-- loading -->
  <div
    v-else
    :class="[
      item.sender === 'loading' && 'loading-indicator',
      item.sender === 'tts-loading' && 'tts-loading-indicator',
      item.sender === 'asr-loading' && 'asr-loading-indicator'
    ]"
  >
    {{ item.text }}
  </div>
</template>

<script setup>
defineProps({
  item: Object
})

defineEmits(['play-audio'])
</script>