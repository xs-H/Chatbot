from snownlp import SnowNLP 
text = '你好'
s = SnowNLP(text)
sen = s.sentiments

def use_pos():
    reference_audio = 'E:happy.mp3'# 这里写开心的参考音频的地址
    reference_text = '开心音频的文本内容'
    return reference_audio, reference_text

def use_angry():
    reference_audio = 'E:angry.mp3' # 这里写愤怒的参考音频的地址，也就是原本的那个
    reference_text = '愤怒文本的文本内容'
    return reference_audio, reference_text

actions = {
    (lambda x:x<0.5) : use_angry(), 
    (lambda x:x>=0.5) : use_pos()
}

for condition, action in actions.items():
    if condition(sen):
        reference_audio, reference_text = action
        break

prompt_speech_16k = load_wav(reference_audio, 16000)
for i, j in enumerate(cosyvoice.inference_zero_shot(text, reference_text, prompt_speech_16k, stream=False)):
    torchaudio.save('zero_shot_{}.wav'.format(i), j['tts_speech'], cosyvoice.sample_rate)

