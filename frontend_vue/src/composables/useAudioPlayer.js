let audioPlayer = null

export function useAudioPlayer() {
  if (!audioPlayer) {
    audioPlayer = new Audio()
    audioPlayer.controls = true
    audioPlayer.style.display = 'none'
    document.body.appendChild(audioPlayer)
  }

  function playAudio(src) {
    audioPlayer.src = src
    audioPlayer.play()
  }

  async function autoPlayAudioList(audioUrls = []) {
    if (!audioUrls.length) return

    let currentIdx = 0
    audioPlayer.src = audioUrls[currentIdx]

    try {
      await audioPlayer.play()
    } catch (error) {
      console.log('Auto-play prevented by browser. User interaction required.')
    }

    audioPlayer.onended = async function () {
      currentIdx += 1
      if (currentIdx < audioUrls.length) {
        audioPlayer.src = audioUrls[currentIdx]
        try {
          await audioPlayer.play()
        } catch (error) {
          console.error(error)
        }
      } else {
        audioPlayer.onended = null
      }
    }
  }

  return {
    playAudio,
    autoPlayAudioList
  }
}