import os
import torch
import librosa

from transformers import ClapProcessor, ClapModel


# CLAP model
MODEL_NAME = "laion/clap-htsat-unfused"

print("Loading CLAP model...")

processor = ClapProcessor.from_pretrained(MODEL_NAME)
model = ClapModel.from_pretrained(MODEL_NAME)

model.eval()

print("CLAP loaded successfully!")


# Get the first audio file from data/
files = [
    f for f in os.listdir("data")
    if f.lower().endswith((".wav", ".mp3", ".flac", ".ogg"))
]

if not files:
    print("No audio files found!")
    exit()

audio_file = os.path.join("data", files[0])

print("\nTesting audio:")
print(audio_file)


# Load audio
audio, sample_rate = librosa.load(
    audio_file,
    sr=48000,
    mono=True
)

print("Audio loaded!")
print("Sample rate:", sample_rate)
print("Audio length:", len(audio))


# Convert audio into CLAP input
inputs = processor(
    audio=audio,
    sampling_rate=sample_rate,
    return_tensors="pt"
)


# Generate embedding
with torch.no_grad():
    # Assigned to 'output' to fix the NameError in your next lines
    output = model.get_audio_features(**inputs)
    
    if hasattr(output, "pooler_output"):
        embedding = output.pooler_output
    else:
        embedding = output


print("\nSUCCESS!")
print("Embedding shape:", embedding.shape)
print("Output Type:", type(output))
print("Embedding created successfully!")
