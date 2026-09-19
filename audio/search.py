import torch
import chromadb

from transformers import ClapProcessor, ClapModel


# -----------------------------
# Load CLAP
# -----------------------------

MODEL_NAME = "laion/clap-htsat-unfused"

processor = ClapProcessor.from_pretrained(
    MODEL_NAME
)

model = ClapModel.from_pretrained(
    MODEL_NAME
)

model.eval()


# -----------------------------
# Connect to ChromaDB
# -----------------------------

client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = client.get_collection(
    name="audio_collection"
)


# -----------------------------
# Search function
# -----------------------------

def search_audio(query):

    # Convert text to CLAP input
    inputs = processor(
        text=[query],
        return_tensors="pt",
        padding=True
    )

    # Generate text embedding
    with torch.no_grad():

        output = model.get_text_features(
            **inputs
        )

        if hasattr(output, "pooler_output"):
            embedding = output.pooler_output
        else:
            embedding = output

    embedding = (
        embedding
        .squeeze()
        .cpu()
        .numpy()
        .tolist()
    )

    # Search ChromaDB
    results = collection.query(
        query_embeddings=[embedding],
        n_results=3
    )

    print("\n==============================")
    print("QUERY:", query)
    print("==============================")

    for i, metadata in enumerate(
        results["metadatas"][0]
    ):

        print(
            f"\n{i + 1}. "
            f"{metadata['filename']}"
        )

        print(
            "Path:",
            metadata["path"]
        )


# -----------------------------
# Main program
# -----------------------------

while True:

    query = input(
        "\nEnter search query "
        "(type 'exit' to stop): "
    )

    if query.lower() == "exit":
        break

    search_audio(query)
