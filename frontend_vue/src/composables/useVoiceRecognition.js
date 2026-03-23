import { ref } from 'vue'

const localAsrBaseUrl = 'http://localhost:8001/api/v1'
const asrBaseUrl = localAsrBaseUrl

export function useVoiceRecognition({
  onAsrLoading,
  onAsrLoaded,
  onRecognized,
  onError
}) {
  const isRecording = ref(false)
  let mediaRecorder = null
  let audioChunks = []
  let currentStream = null

  async function checkASRStatus() {
    try {
      const response = await fetch(`${asrBaseUrl}/asr/`)
      const data = await response.json()
      return data.status === 'ok'
    } catch (error) {
      console.error('无法连接到ASR服务:', error)
      return false
    }
  }

  async function sendAudioForRecognition(audioBlob) {
    onAsrLoading?.()

    try {
      const formData = new FormData()
      formData.append('file', audioBlob)

      const response = await fetch(`${asrBaseUrl}/asr/task`, {
        method: 'POST',
        body: formData
      })

      if (response.status === 201) {
        const data = await response.json()
        await pollASRResult(data.task_id)
      } else {
        throw new Error(`服务器返回错误: ${response.status}`)
      }
    } catch (error) {
      console.error('语音识别请求错误:', error)
      onAsrLoaded?.()
      onError?.('语音识别失败，请稍后再试。')
    }
  }

  async function pollASRResult(taskId) {
    try {
      const response = await fetch(`${asrBaseUrl}/asr/task/${taskId}`)

      if (response.status === 200) {
        const data = await response.json()
        onAsrLoaded?.()

        if (data.status === 'done' && data.result && data.result.text) {
          onRecognized?.(data.result.text)
        } else {
          onError?.('语音识别失败或未识别到文字。')
        }
      } else if (response.status === 202) {
        setTimeout(() => pollASRResult(taskId), 1000)
      } else {
        throw new Error(`获取识别结果失败: ${response.status}`)
      }
    } catch (error) {
      console.error('轮询ASR结果错误:', error)
      onAsrLoaded?.()
      onError?.('获取语音识别结果失败，请稍后再试。')
    }
  }

  async function startRecording() {
    try {
      const statusOk = await checkASRStatus()
      if (!statusOk) {
        onError?.('语音识别服务不可用，请稍后再试。')
        return
      }

      currentStream = await navigator.mediaDevices.getUserMedia({ audio: true })
      mediaRecorder = new MediaRecorder(currentStream)
      audioChunks = []

      mediaRecorder.addEventListener('dataavailable', (event) => {
        audioChunks.push(event.data)
      })

      mediaRecorder.addEventListener('stop', async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' })
        await sendAudioForRecognition(audioBlob)

        if (currentStream) {
          currentStream.getTracks().forEach((track) => track.stop())
          currentStream = null
        }

        isRecording.value = false
      })

      mediaRecorder.start()
      isRecording.value = true
    } catch (error) {
      console.error('录音错误:', error)
      onError?.('无法访问麦克风，请检查浏览器权限设置。')
    }
  }

  function stopRecording() {
    if (mediaRecorder && isRecording.value) {
      mediaRecorder.stop()
    }
  }

  async function toggleRecording() {
    if (!isRecording.value) {
      await startRecording()
    } else {
      stopRecording()
    }
  }

  return {
    isRecording,
    toggleRecording
  }
}