<template>
  <div class="app-shell">
    <AppSidebar
      :collapsed="sidebarCollapsed"
      @toggle="toggleSidebar"
    />

    <div class="divider"></div>

    <div class="main">
      <TopActions />

      <IntroPanel v-if="!chatStarted" />

      <ChatBox
        :chat-started="chatStarted"
        :messages="messages"
        :input-text="inputText"
        :is-recording="isRecording"
        @update:input-text="inputText = $event"
        @send="sendMessage"
        @toggle-recording="toggleRecording"
        @play-audio="playAudio"
      />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import AppSidebar from './components/AppSidebar.vue'
import TopActions from './components/TopActions.vue'
import IntroPanel from './components/IntroPanel.vue'
import ChatBox from './components/ChatBox.vue'
import { useChat } from './composables/useChat'
import { useVoiceRecognition } from './composables/useVoiceRecognition'
import { useAudioPlayer } from './composables/useAudioPlayer'

const sidebarCollapsed = ref(false)
const inputText = ref('')

const {
  messages,
  sendMessage,
  appendAiMessage,
  appendStatusMessage,
  removeStatusMessage,
  setRecognizedText,
  playAudio,
  chatStarted
} = useChat(inputText)

const { isRecording, toggleRecording } = useVoiceRecognition({
  onAsrLoading: () => appendStatusMessage('asr-loading', '正在识别语音'),
  onAsrLoaded: () => removeStatusMessage('asr-loading'),
  onRecognized: (text) => setRecognizedText(text),
  onError: (text) => appendAiMessage(text)
})

useAudioPlayer()

function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
}
</script>