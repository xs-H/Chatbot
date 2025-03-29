import os
import time
import torch
import torchaudio
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts

print("Loading model...")
config = XttsConfig()
config.load_json(r"C:\Users\lenovo\AppData\Local\tts\tts_models--multilingual--multi-dataset--xtts_v2\config.json")
model = Xtts.init_from_config(config)
model.load_checkpoint(config, checkpoint_dir=r"C:\Users\lenovo\AppData\Local\tts\tts_models--multilingual--multi-dataset--xtts_v2", use_deepspeed=False)
model.cuda()

print("Computing speaker latents...")
gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(audio_path=[r"E:\OneDrive\桌面\入党申请书\zh_combine.mp3"])

print("Inference...")
time_start = time.perf_counter()
out = model.inference(
    "我是朱慧，我在江苏大学就读。如果你有升学意愿，请通过电子邮箱联系我。",
    "zh-cn",
    gpt_cond_latent,
    speaker_embedding,
    temperature=0.7, # Add custom parameters here
)
torchaudio.save("xtts.wav", torch.tensor(out["wav"]).unsqueeze(0), 24000)
time_end = time.perf_counter()

print("Inference done!\n", f"Spending time: {time_end-time_start}")