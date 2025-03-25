import os
import time
import torch
import torchaudio
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts

print("Loading model...")
config = XttsConfig(max_ref_len=10, num_gpt_outputs=8, gpt_cond_len=12)
config.load_json(r"C:\Users\lenovo\AppData\Local\tts\tts_models--multilingual--multi-dataset--xtts_v2\config.json")
model = Xtts.init_from_config(config)
model.load_checkpoint(config, checkpoint_dir=r"C:\Users\lenovo\AppData\Local\tts\tts_models--multilingual--multi-dataset--xtts_v2", use_deepspeed=False)
model.cuda()

print("Computing speaker latents...")
gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(audio_path=[r"E:\OneDrive\桌面\入党申请书\nz.mp3", r"E:\OneDrive\桌面\入党申请书\nz2.mp3"])

print("Inference...")
time_start = time.perf_counter()
out = model.inference(
    "哼？你这是谁啊！小爷我又不是不认识的路人随便搭讪的好不好。对了，我是灵珠转世的小英雄。",
    "zh-cn",
    gpt_cond_latent,
    speaker_embedding,
    temperature=0.5, # Add custom parameters here
    length_penalty=1.0,
    enable_text_splitting=False,
    speed=1.0,
    top_p=0.8,
    top_k=60
)
torchaudio.save("xtts.wav", torch.tensor(out["wav"]).unsqueeze(0), 24000)
time_end = time.perf_counter()

print("Inference done!\n", f"Spending time: {time_end-time_start}")