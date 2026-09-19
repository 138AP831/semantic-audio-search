import os
import torch
import librosa
import chromadb

from transformers import ClapProcessor, ClapModel


# -----------------------------
# 1. Load CLAP
# -----------------------------

MODEL_NAME = "laion/clap-htsat-unfused"

print("Loading CLAP...")

processor = ClapProcessor.from_pretrained(MODEL_NAME)
model = ClapModel.from_pretrained(MODEL_NAME)

model.eval()

print("CLAP loaded!")


# -----------------------------
# 2. Connect to ChromaDB
# -----------------------------

client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = client.get_or_create_collection(
    name="audio_collection"
)


# -----------------------------
# 3. Process audio files
# -----------------------------

audio_folder = "data"

files = [
    f for f in os.listdir(audio_folder)
    if f.lower().endswith(
        (".wav", ".mp3", ".flac", ".ogg")
    )
]

print("\nFound", len(files), "audio files.")


for filename in files:

    print("\nProcessing:", filename)

    path = os.path.join(
        audio_folder,
        filename
    )

    # Load audio
    audio, sample_rate = librosa.load(
        path,
        sr=48000,
        mono=True
    )

    # Prepare CLAP input
    inputs = processor(
        audio=audio,
        sampling_rate=sample_rate,
        return_tensors="pt"
    )

    # Generate embedding
    with torch.no_grad():

        output = model.get_audio_features(
            **inputs
        )

        if hasattr(output, "pooler_output"):
            embedding = output.pooler_output
        else:
            embedding = output

    # Convert tensor to list
    embedding = (
        embedding
        .squeeze()
        .cpu()
        .numpy()
        .tolist()
    )

    # Store in ChromaDB
    collection.upsert(
        ids=[filename],
        embeddings=[embedding],
        metadatas=[
            {
                "filename": filename,
                "path": path
            }
        ]
    )

    print("Indexed:", filename)


# -----------------------------
# 4. Finished
# -----------------------------

print("\n==============================")
print("INDEXING COMPLETE!")
print("==============================")

print(
    "Total vectors:",
    collection.count()
)
