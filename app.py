import os
import torch
import chromadb
import streamlit as st

from transformers import ClapProcessor, ClapModel


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="SoundFind | Semantic Audio Search",
    page_icon="S",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ============================================================
# SVG ICONS
# ============================================================

def icon(name, size=20):
    icons = {
        "search": f"""
        <svg width="{size}" height="{size}" viewBox="0 0 24 24"
             fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="7"></circle>
            <line x1="16.5" y1="16.5" x2="21" y2="21"></line>
        </svg>
        """,

        "sound": f"""
        <svg width="{size}" height="{size}" viewBox="0 0 24 24"
             fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round">
            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
            <path d="M15.5 8.5a5 5 0 0 1 0 7"></path>
            <path d="M18.5 5.5a9 9 0 0 1 0 13"></path>
        </svg>
        """,

        "database": f"""
        <svg width="{size}" height="{size}" viewBox="0 0 24 24"
             fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round">
            <ellipse cx="12" cy="5" rx="8" ry="3"></ellipse>
            <path d="M4 5v7c0 1.7 3.6 3 8 3s8-1.3 8-3V5"></path>
            <path d="M4 12v7c0 1.7 3.6 3 8 3s8-1.3 8-3v-7"></path>
        </svg>
        """,

        "brain": f"""
        <svg width="{size}" height="{size}" viewBox="0 0 24 24"
             fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round">
            <path d="M9.5 3a3.5 3.5 0 0 0-3 5.5A3.5 3.5 0 0 0 7 15a3.5 3.5 0 0 0 3 5.5"></path>
            <path d="M14.5 3a3.5 3.5 0 0 1 3 5.5A3.5 3.5 0 0 1 17 15a3.5 3.5 0 0 1-3 5.5"></path>
            <path d="M9 7h2"></path>
            <path d="M13 7h2"></path>
            <path d="M9 12h2"></path>
            <path d="M13 12h2"></path>
            <path d="M10 17h4"></path>
            <path d="M12 3v18"></path>
        </svg>
        """,

        "music": f"""
        <svg width="{size}" height="{size}" viewBox="0 0 24 24"
             fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round">
            <path d="M9 18V5l11-2v13"></path>
            <circle cx="6" cy="18" r="3"></circle>
            <circle cx="17" cy="16" r="3"></circle>
        </svg>
        """,

        "upload": f"""
        <svg width="{size}" height="{size}" viewBox="0 0 24 24"
             fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 16V4"></path>
            <polyline points="7 9 12 4 17 9"></polyline>
            <path d="M5 20h14"></path>
        </svg>
        """,

        "file": f"""
        <svg width="{size}" height="{size}" viewBox="0 0 24 24"
             fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
        </svg>
        """
    }

    return icons.get(name, "")


def render_html(html):
    """
    Collapse markup to a single line before handing it to
    st.markdown. Streamlit's Markdown renderer treats HTML lines
    indented 4+ spaces as an indented code block, and a blank line
    in the middle of a block (which the multi-line SVG strings in
    icon() introduce, since each one starts and ends with its own
    blank line) breaks raw-HTML detection for everything after it.
    Joining every fragment onto one line sidesteps both failure
    modes; browsers don't care about whitespace between tags.
    """
    st.markdown(" ".join(html.split()), unsafe_allow_html=True)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background: #f7f8fc;
    }

    .block-container {
        max-width: 1100px;
        padding-top: 2.5rem;
        padding-bottom: 4rem;
    }

    /* ---------------- HEADER ---------------- */

    .brand-container {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 3px;
    }

    .brand-icon {
        width: 42px;
        height: 42px;
        border-radius: 12px;
        background: #111827;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .brand {
        font-size: 2rem;
        font-weight: 800;
        color: #111827;
        letter-spacing: -0.04em;
    }

    .subtitle {
        color: #6b7280;
        font-size: 1rem;
        margin-left: 54px;
        margin-bottom: 30px;
    }

    /* ---------------- STATS ---------------- */

    .stats-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 18px;
        min-height: 105px;
    }

    .stats-icon {
        color: #6366f1;
        margin-bottom: 8px;
    }

    .stats-number {
        font-size: 1.35rem;
        font-weight: 750;
        color: #111827;
    }

    .stats-label {
        color: #6b7280;
        font-size: 0.78rem;
        margin-top: 3px;
    }

    /* ---------------- SEARCH ---------------- */

    .section-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #111827;
        margin-top: 30px;
        margin-bottom: 10px;
    }

    .search-help {
        color: #6b7280;
        font-size: 0.85rem;
        margin-bottom: 8px;
    }

    /* ---------------- SUGGESTIONS ---------------- */

    .suggestion-label {
        color: #6b7280;
        font-size: 0.8rem;
        font-weight: 600;
        margin-top: 10px;
        margin-bottom: 5px;
    }

    /* ---------------- RESULTS ---------------- */

    .result-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 15px;
        padding: 20px;
        margin-top: 15px;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.035);
    }

    .result-header {
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .result-icon {
        width: 38px;
        height: 38px;
        border-radius: 10px;
        background: #eef2ff;
        color: #4f46e5;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .result-rank {
        color: #6366f1;
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }

    .filename {
        color: #111827;
        font-size: 1rem;
        font-weight: 700;
        margin-top: 2px;
    }

    .path {
        color: #9ca3af;
        font-size: 0.75rem;
        margin-top: 4px;
    }

    /* ---------------- EMPTY STATE ---------------- */

    .empty-state {
        text-align: center;
        padding: 65px 20px;
        color: #9ca3af;
    }

    .empty-icon {
        width: 55px;
        height: 55px;
        margin: auto;
        border-radius: 15px;
        background: white;
        border: 1px solid #e5e7eb;
        color: #6366f1;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 15px;
    }

    .empty-title {
        color: #374151;
        font-weight: 650;
        font-size: 1rem;
    }

    .empty-text {
        margin-top: 5px;
        font-size: 0.85rem;
    }

    /* ---------------- BUTTONS ---------------- */

    .stButton > button {
        border-radius: 9px;
        border: 1px solid #e5e7eb;
        font-weight: 600;
        min-height: 42px;
    }

    .stButton > button:hover {
        border-color: #6366f1;
        color: #4f46e5;
    }

    /* ---------------- AUDIO PLAYER ---------------- */

    audio {
        width: 100%;
        margin-top: 14px;
    }

    /* ---------------- HIDE STREAMLIT ---------------- */

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# LOAD CLAP
# ============================================================

MODEL_NAME = "laion/clap-htsat-unfused"


@st.cache_resource
def load_clap():
    processor = ClapProcessor.from_pretrained(MODEL_NAME)
    model = ClapModel.from_pretrained(MODEL_NAME)
    model.eval()
    return processor, model


with st.spinner("Loading audio intelligence..."):
    processor, model = load_clap()


# ============================================================
# LOAD DATABASE
# ============================================================

@st.cache_resource
def load_database():
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_collection(name="audio_collection")
    return collection


collection = load_database()

total_files = collection.count()


# ============================================================
# HEADER
# ============================================================

render_html(
    f"""
    <div class="brand-container">
        <div class="brand-icon">
            {icon("sound", 23)}
        </div>
        <div class="brand">
            SoundFind
        </div>
    </div>

    <div class="subtitle">
        Semantic audio search powered by multimodal embeddings
    </div>
    """
)


# ============================================================
# STATS
# ============================================================

col1, col2, col3 = st.columns(3)

with col1:
    render_html(
        f"""
        <div class="stats-card">
            <div class="stats-icon">
                {icon("database", 20)}
            </div>
            <div class="stats-number">
                {total_files}
            </div>
            <div class="stats-label">
                Audio files indexed
            </div>
        </div>
        """
    )

with col2:
    render_html(
        f"""
        <div class="stats-card">
            <div class="stats-icon">
                {icon("brain", 20)}
            </div>
            <div class="stats-number">
                CLAP
            </div>
            <div class="stats-label">
                Multimodal embedding model
            </div>
        </div>
        """
    )

with col3:
    render_html(
        f"""
        <div class="stats-card">
            <div class="stats-icon">
                {icon("search", 20)}
            </div>
            <div class="stats-number">
                Top 3
            </div>
            <div class="stats-label">
                Semantic matches per query
            </div>
        </div>
        """
    )


# ============================================================
# SEARCH
# ============================================================

render_html('<div class="section-title">Search your sound library</div>')

render_html(
    '<div class="search-help">'
    'Describe the sound you want to find in natural language.'
    '</div>'
)

col1, col2 = st.columns([5, 1])

with col1:
    query = st.text_input(
        "Search query",
        placeholder="Try: heavy rain with thunder",
        label_visibility="collapsed"
    )

with col2:
    search_button = st.button("Search", use_container_width=True)


# ============================================================
# SUGGESTIONS
# ============================================================

render_html('<div class="suggestion-label">Suggested searches</div>')

suggestions = [
    "Dog barking",
    "Heavy rain",
    "People clapping",
    "Keyboard typing"
]

cols = st.columns(4)

for i, suggestion in enumerate(suggestions):
    with cols[i]:
        if st.button(suggestion, use_container_width=True):
            query = suggestion
            search_button = True


# ============================================================
# TEXT EMBEDDING
# ============================================================

def create_text_embedding(text):
    inputs = processor(text=[text], return_tensors="pt", padding=True)

    with torch.no_grad():
        output = model.get_text_features(**inputs)

    if hasattr(output, "pooler_output"):
        embedding = output.pooler_output
    elif hasattr(output, "text_embeds"):
        embedding = output.text_embeds
    else:
        embedding = output

    return embedding.squeeze().cpu().numpy().tolist()


# ============================================================
# SEARCH
# ============================================================

if search_button and query:
    with st.spinner("Searching semantic audio space..."):
        query_embedding = create_text_embedding(query)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(3, total_files)
        )

    render_html(
        f"""
        <div class="section-title">
            Search results
        </div>

        <div class="search-help">
            Showing the closest matches for
            <strong>"{query}"</strong>
        </div>
        """
    )

    result_files = results["metadatas"][0]
    distances = results.get("distances", [[]])[0]

    for i, metadata in enumerate(result_files):
        filename = metadata["filename"]
        path = metadata["path"]
        distance = distances[i] if i < len(distances) else None

        render_html(
            f"""
            <div class="result-card">
                <div class="result-header">
                    <div class="result-icon">
                        {icon("music", 19)}
                    </div>
                    <div>
                        <div class="result-rank">
                            Match {i + 1}
                        </div>
                        <div class="filename">
                            {filename}
                        </div>
                        <div class="path">
                            {path}
                        </div>
                    </div>
                </div>
            </div>
            """
        )

        if os.path.exists(path):
            st.audio(path, format="audio/wav")
        else:
            st.warning(f"Audio file not found: {path}")

        if distance is not None:
            st.caption(f"Vector distance: {distance:.4f}")


# ============================================================
# EMPTY STATE
# ============================================================

elif not query:
    render_html(
        f"""
        <div class="empty-state">
            <div class="empty-icon">
                {icon("sound", 25)}
            </div>
            <div class="empty-title">
                Your audio library is ready
            </div>
            <div class="empty-text">
                Describe a sound above to discover matching audio.
            </div>
        </div>
        """
    )
