from TTS.api import TTS

# مدل نمونه انگلیسی (برای تست اینکه کتابخانه درست کار می‌کند)
model_name = "tts_models/multilingual/multi-dataset/xtts_v2"

# مدل را لود می‌کنیم
tts = TTS(model_name)

# متن تست
text = "سلام! این یک تست از کتابخانه کوکی تی تی اس است."

# خروجی صدا
tts.tts_to_file(
    text=text,
    file_path="output.wav"
)

print("Done! File saved as output.wav")
