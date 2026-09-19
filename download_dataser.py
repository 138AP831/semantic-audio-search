import csv
import os
import urllib.request


DATA_DIR = "data"
METADATA_FILE = "esc50.csv"

METADATA_URL = (
    "https://raw.githubusercontent.com/"
    "karolpiczak/ESC-50/master/meta/esc50.csv"
)

AUDIO_BASE_URL = (
    "https://raw.githubusercontent.com/"
    "karolpiczak/ESC-50/master/audio/"
)


# Create data folder
os.makedirs(DATA_DIR, exist_ok=True)


# ------------------------------------------------------------
# Download metadata
# ------------------------------------------------------------

print("Downloading ESC-50 metadata...")

urllib.request.urlretrieve(
    METADATA_URL,
    METADATA_FILE
)

print("Metadata downloaded.")


# ------------------------------------------------------------
# Categories for the demo
# ------------------------------------------------------------

categories = [
    "dog",
    "cat",
    "rain",
    "thunderstorm",
    "clapping",
    "laughing",
    "keyboard_typing",
    "footsteps",
    "engine",
    "sea_waves"
]


# ------------------------------------------------------------
# Read metadata
# ------------------------------------------------------------

with open(
    METADATA_FILE,
    newline=""
) as file:

    rows = list(
        csv.DictReader(file)
    )


# ------------------------------------------------------------
# Download one file from each category
# ------------------------------------------------------------

downloaded = 0


for category in categories:

    match = next(
        (
            row
            for row in rows
            if row["category"] == category
        ),
        None
    )

    if match is None:

        print(
            f"Category not found: {category}"
        )

        continue


    filename = match["filename"]

    url = AUDIO_BASE_URL + filename

    destination = os.path.join(
        DATA_DIR,
        filename
    )


    # Don't download again if it already exists
    if os.path.exists(destination):

        print(
            f"Already exists: {filename}"
        )

        downloaded += 1
        continue


    print(
        f"Downloading {category}: {filename}"
    )


    urllib.request.urlretrieve(
        url,
        destination
    )

    downloaded += 1


# ------------------------------------------------------------
# Finished
# ------------------------------------------------------------

print()
print("==============================")
print("DATASET DOWNLOAD COMPLETE")
print("==============================")
print(
    f"Audio files available: {downloaded}"
)
print(
    f"Location: {DATA_DIR}/"
)
