import { ref, computed } from 'vue'
import { useAudioPlayer } from './useAudioPlayer'

const ttsBaseUrl = 'http://localhost:5001'
const chatApiUrl = 'http://localhost:3000/api/chat'

export function useChat(inputTextRef) {
  const messages = ref([])
  const { playAudio, autoPlayAudioList } = useAudioPlayer()

  const chatStarted = computed(() => messages.value.length > 0)

  function createMessage(sender, text, extra = {}) {
    return {
      id: `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
      sender,
      text,
      ...extra
    }
  }

  function appendUserMessage(text) {
    messages.value.push(createMessage('user', text))
  }

  function appendAiMessage(text, audioUrls = []) {
    messages.value.push(createMessage('ai', text, { audioUrls }))
  }

  function appendStatusMessage(sender, text) {
    messages.value.push(createMessage(sender, text))
  }

  function removeStatusMessage(sender) {
    const index = messages.value.findIndex((item) => item.sender === sender)
    if (index !== -1) {
      messages.value.splice(index, 1)
    }
  }

  function setRecognizedText(text) {
    inputTextRef.value = text
  }

  async function generateTTS(text) {
    try {
      const response = await fetch(`${ttsBaseUrl}/api/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      })

      if (!response.ok) {
        throw new Error(`TTS服务错误: ${response.status}`)
      }

      const data = await response.json()
      return data.audio_files && data.audio_files.length > 0 ? data.audio_files : []
    } catch (error) {
      console.error('TTS生成错误:', error)
      return []
    }
  }

  async function sendMessage() {
    const userMessage = inputTextRef.value.trim()
    if (!userMessage) return

    appendUserMessage(userMessage)
    inputTextRef.value = ''
    appendStatusMessage('loading', '思考中')

    try {
      const chatResponse = await fetch(chatApiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage })
      })

      const chatData = await chatResponse.json()
      removeStatusMessage('loading')

      if (chatData.error) {
        appendAiMessage(`抱歉，出现了错误: ${chatData.error}`)
        return
      }

      const aiReply = chatData.reply
      appendStatusMessage('tts-loading', '生成语音中')

      const audioFiles = await generateTTS(aiReply)
      removeStatusMessage('tts-loading')

      const audioUrls = audioFiles.map(
        (file) => `${ttsBaseUrl}/api/audio/${file.split('/').pop()}`
      )

      appendAiMessage(aiReply, audioUrls)

      if (audioUrls.length > 0) {
        await autoPlayAudioList(audioUrls)
      }
    } catch (error) {
      console.error('Error:', error)
      removeStatusMessage('loading')
      removeStatusMessage('tts-loading')
      appendAiMessage('抱歉，出现了错误，请稍后再试。')
    }
  }

  return {
    messages,
    sendMessage,
    appendAiMessage,
    appendStatusMessage,
    removeStatusMessage,
    setRecognizedText,
    playAudio,
    chatStarted
  }
}