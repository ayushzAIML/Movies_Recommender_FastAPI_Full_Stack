"""
🎬 CineMatch — AI-Powered Movie Recommendation Engine
Production-grade Streamlit UI
"""

import requests
import streamlit as st
from typing import Optional, List, Dict, Any

# ═══════════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════════
API_BASE = "http://127.0.0.1:8000"
TMDB_IMG = "https://image.tmdb.org/t/p/w500"
PLACEHOLDER_POSTER = "https://via.placeholder.com/500x750?text=No+Poster"
CATEGORIES = {
    "🔥 Trending": "trending",
    "⭐ Popular": "popular",
    "🏆 Top Rated": "top_rated",
    "🎬 Now Playing": "now_playing",
    "📅 Upcoming": "upcoming",
}

# ─────────────────────────── SESSION STATE ────────────────────
if "selected_movie_id" not in st.session_state:
    st.session_state.selected_movie_id = None

# ─────────────────────────── PAGE CONFIG ──────────────────────
st.set_page_config(
    page_title="CineMatch • Movie Recommendations",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────── CUSTOM CSS ───────────────────────
st.markdown(
    """
<style>
/* ── Global ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── Hide streamlit chrome ── */
#MainMenu, header, footer {visibility: hidden;}
div[data-testid="stDecoration"] {display: none;}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d0d0d 0%, #1a1a2e 100%);
    border-right: 1px solid rgba(255,255,255,0.06);
}
section[data-testid="stSidebar"] .stRadio > label {
    font-weight: 600; letter-spacing: 0.5px;
}

/* ── Hero Brand ── */
.brand-header {
    text-align: center;
    padding: 1.2rem 0 0.8rem;
}
.brand-header h1 {
    font-size: 1.75rem;
    font-weight: 800;
    background: linear-gradient(135deg, #e50914 0%, #ff6b6b 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
}
.brand-header p {
    color: #999; font-size: 0.82rem; margin-top: 2px;
}

/* ── Poster Cards ── */
.poster-card {
    background: #181818;
    border-radius: 12px;
    overflow: hidden;
    transition: transform 0.25s ease, box-shadow 0.25s ease;
    margin-bottom: 1rem;
    border: 1px solid rgba(255,255,255,0.04);
}
.poster-card:hover {
    transform: translateY(-6px);
    box-shadow: 0 12px 32px rgba(229,9,20,0.18);
}
.poster-card img {
    width: 100%;
    aspect-ratio: 2/3;
    object-fit: cover;
    display: block;
}
.poster-card .card-body {
    padding: 0.65rem 0.75rem;
}
.poster-card .card-title {
    font-size: 0.82rem;
    font-weight: 600;
    color: #f0f0f0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.poster-card .card-meta {
    font-size: 0.72rem;
    color: #888;
    margin-top: 2px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.poster-card .card-meta .rating {
    color: #f5c518;
    font-weight: 600;
}

/* ── Detail Hero ── */
.detail-hero {
    position: relative;
    border-radius: 16px;
    overflow: hidden;
    margin-bottom: 1.5rem;
}
.detail-hero img.backdrop {
    width: 100%;
    max-height: 400px;
    object-fit: cover;
    display: block;
    filter: brightness(0.45);
}
.detail-hero .overlay {
    position: absolute;
    bottom: 0; left: 0; right: 0;
    padding: 2rem;
    background: linear-gradient(transparent, rgba(0,0,0,0.92));
}
.detail-hero .overlay h1 {
    font-size: 2rem; font-weight: 800; margin: 0;
    color: #fff;
}
.detail-hero .overlay p {
    color: #ccc; font-size: 0.9rem; margin-top: 6px;
}

/* ── Section headers ── */
.section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 1.8rem 0 0.8rem;
}
.section-header h3 {
    font-size: 1.2rem;
    font-weight: 700;
    color: #f0f0f0;
    margin: 0;
}
.section-header .line {
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, rgba(229,9,20,0.5), transparent);
}

/* ── Badges ── */
.genre-badge {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 20px;
    background: rgba(229,9,20,0.12);
    border: 1px solid rgba(229,9,20,0.3);
    color: #ff6b6b;
    font-size: 0.78rem;
    font-weight: 600;
    margin: 3px 4px 3px 0;
}

/* ── Score bar ── */
.score-bar-wrap {
    margin: 4px 0;
}
.score-bar {
    height: 4px;
    border-radius: 2px;
    background: #333;
    overflow: hidden;
}
.score-bar-fill {
    height: 100%;
    border-radius: 2px;
    background: linear-gradient(90deg, #e50914, #ff6b6b);
}
.score-text {
    font-size: 0.7rem;
    color: #aaa;
    text-align: right;
    margin-top: 1px;
}

/* ── Search input ── */
div[data-testid="stTextInput"] input {
    border-radius: 10px !important;
    border: 1px solid rgba(229,9,20,0.3) !important;
    background: #1a1a1a !important;
    color: #f0f0f0 !important;
    padding: 0.6rem 1rem !important;
    font-size: 0.95rem !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #e50914 !important;
    box-shadow: 0 0 0 2px rgba(229,9,20,0.15) !important;
}

/* ── Buttons ── */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(229,9,20,0.2) !important;
}

/* ── Stat cards ── */
.stat-card {
    background: #181818;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    border: 1px solid rgba(255,255,255,0.06);
    text-align: center;
}
.stat-card .stat-value {
    font-size: 1.5rem;
    font-weight: 800;
    background: linear-gradient(135deg, #e50914, #ff6b6b);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.stat-card .stat-label {
    font-size: 0.78rem;
    color: #888;
    margin-top: 2px;
}

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 4rem 2rem;
    color: #666;
}
.empty-state .emoji {
    font-size: 3rem;
    margin-bottom: 0.5rem;
}
</style>
""",
    unsafe_allow_html=True,
)


# ─────────────────────────── API HELPERS ──────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def api_get(path: str, params: Optional[dict] = None) -> Any:
    """Cached GET to backend API."""
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Backend API is offline. Start it with `uvicorn main:app`")
        return None
    except Exception as e:
        st.error(f"API error: {e}")
        return None


def api_get_live(path: str, params: Optional[dict] = None) -> Any:
    """Non-cached GET (for search / dynamic)."""
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Backend API is offline. Start it with `uvicorn main:app`")
        return None
    except Exception as e:
        st.error(f"API error: {e}")
        return None


# ─────────────────────────── UI COMPONENTS ────────────────────
def render_section_header(title: str):
    st.markdown(
        f"""<div class="section-header">
            <h3>{title}</h3>
            <div class="line"></div>
        </div>""",
        unsafe_allow_html=True,
    )


def render_poster_card(
    title: str,
    poster_url: Optional[str],
    release_date: Optional[str] = None,
    vote_average: Optional[float] = None,
    score: Optional[float] = None,
):
    """Render a single movie poster card."""
    poster = poster_url or PLACEHOLDER_POSTER
    year = release_date[:4] if release_date and len(release_date) >= 4 else "—"

    rating_html = ""
    if vote_average is not None:
        rating_html = f'<span class="rating">⭐ {vote_average:.1f}</span>'

    score_html = ""
    if score is not None:
        pct = min(score * 100, 100)
        score_html = (
            '<div class="score-bar-wrap">'
            f'<div class="score-bar"><div class="score-bar-fill" style="width:{pct}%"></div></div>'
            f'<div class="score-text">{score:.1%} match</div>'
            '</div>'
        )

    html = (
        '<div class="poster-card">'
        f'<img src="{poster}" alt="{title}" loading="lazy" />'
        '<div class="card-body">'
        f'<div class="card-title" title="{title}">{title}</div>'
        '<div class="card-meta">'
        f'<span>{year}</span>'
        f'{rating_html}'
        '</div>'
        f'{score_html}'
        '</div>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def render_poster_grid(
    movies: List[Dict],
    cols: int = 6,
    show_score: bool = False,
    clickable: bool = True,
):
    """Render a responsive grid of movie poster cards."""
    if not movies:
        st.markdown(
            '<div class="empty-state"><div class="emoji">🎬</div>No movies found</div>',
            unsafe_allow_html=True,
        )
        return

    columns = st.columns(cols)
    for i, movie in enumerate(movies):
        with columns[i % cols]:
            render_poster_card(
                title=movie.get("title", "Unknown"),
                poster_url=movie.get("poster_url"),
                release_date=movie.get("release_date"),
                vote_average=movie.get("vote_average"),
                score=movie.get("score") if show_score else None,
            )
            # Clickable button to view details
            tmdb_id = movie.get("tmdb_id")
            if clickable and tmdb_id:
                if st.button("📖 Details", key=f"detail_{tmdb_id}_{i}", use_container_width=True):
                    st.session_state.selected_movie_id = tmdb_id
                    st.rerun()


def render_movie_detail(detail: Dict):
    """Render the movie detail hero section."""
    backdrop = detail.get("backdrop_url")
    poster = detail.get("poster_url") or PLACEHOLDER_POSTER
    title = detail.get("title", "Unknown")
    year = ""
    if detail.get("release_date"):
        year = detail["release_date"][:4]

    # Hero with backdrop
    if backdrop:
        st.markdown(
            f"""<div class="detail-hero">
                <img class="backdrop" src="{backdrop}" alt="{title}" />
                <div class="overlay">
                    <h1>{title}</h1>
                    <p>{year}</p>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

    # Poster + Info
    col_poster, col_info = st.columns([1, 2.5], gap="large")
    with col_poster:
        st.image(poster, use_container_width=True)

    with col_info:
        if not backdrop:
            st.markdown(f"## {title}")
            if year:
                st.caption(year)

        # Genres
        genres = detail.get("genres", [])
        if genres:
            badges = "".join(
                f'<span class="genre-badge">{g.get("name", "")}</span>'
                for g in genres
            )
            st.markdown(badges, unsafe_allow_html=True)

        # Overview
        overview = detail.get("overview")
        if overview:
            st.markdown(f"**Overview**")
            st.write(overview)

        # Stats row
        s1, s2, s3 = st.columns(3)
        with s1:
            tmdb_id = detail.get("tmdb_id", "—")
            st.markdown(
                f'<div class="stat-card"><div class="stat-value">{tmdb_id}</div>'
                f'<div class="stat-label">TMDB ID</div></div>',
                unsafe_allow_html=True,
            )
        with s2:
            rd = detail.get("release_date", "—") or "—"
            st.markdown(
                f'<div class="stat-card"><div class="stat-value">{rd}</div>'
                f'<div class="stat-label">Release Date</div></div>',
                unsafe_allow_html=True,
            )
        with s3:
            gc = len(genres)
            st.markdown(
                f'<div class="stat-card"><div class="stat-value">{gc}</div>'
                f'<div class="stat-label">Genres</div></div>',
                unsafe_allow_html=True,
            )


# ─────────────────────────── PAGES ────────────────────────────
def page_home():
    """Home / Discover page with category carousels."""
    st.markdown(
        '<div class="brand-header"><h1>🎬 CineMatch</h1>'
        "<p>AI-Powered Movie Recommendation Engine</p></div>",
        unsafe_allow_html=True,
    )

    # Category selector
    selected_label = st.selectbox(
        "Browse by category",
        list(CATEGORIES.keys()),
        index=0,
        label_visibility="collapsed",
    )
    category = CATEGORIES[selected_label]

    with st.spinner("Loading movies…"):
        movies = api_get("/home", {"category": category, "limit": 24})

    if movies:
        render_section_header(selected_label)
        render_poster_grid(movies, cols=6)


def page_search():
    """Search & Recommend page — the core experience."""
    st.markdown(
        '<div class="brand-header"><h1>🔍 Search & Recommend</h1>'
        "<p>Type a movie name to get AI-powered recommendations</p></div>",
        unsafe_allow_html=True,
    )

    # ── Search bar ──
    col_input, col_btn = st.columns([5, 1])
    with col_input:
        query = st.text_input(
            "Search",
            placeholder="e.g.  The Dark Knight, Inception, Interstellar …",
            label_visibility="collapsed",
            key="search_query",
        )
    with col_btn:
        search_clicked = st.button("🔍  Search", use_container_width=True, type="primary")

    top_n = st.slider(
        "Number of TF-IDF recommendations",
        min_value=5, max_value=30, value=10,
        key="tfidf_top_n",
    )

    if not query:
        st.markdown(
            '<div class="empty-state">'
            '<div class="emoji">🍿</div>'
            "Enter a movie title above to discover recommendations"
            "</div>",
            unsafe_allow_html=True,
        )
        return

    # ── Step 1: TMDB search ──
    with st.spinner("Searching TMDB…"):
        search_data = api_get_live("/tmdb/search", {"query": query})

    if not search_data or not search_data.get("results"):
        st.warning("No movies found on TMDB for that query.")
        return

    results = search_data["results"]

    # Let user pick from top results
    titles_map = {}
    for r in results[:8]:
        year = (r.get("release_date") or "")[:4]
        label = f"{r.get('title', 'Unknown')} ({year})" if year else r.get("title", "Unknown")
        titles_map[label] = r

    selected_label = st.selectbox(
        "Select the correct movie:",
        list(titles_map.keys()),
        key="movie_select",
    )
    selected = titles_map[selected_label]
    tmdb_id = selected["id"]

    # ── Step 2: Movie details ──
    with st.spinner("Fetching movie details…"):
        detail = api_get(f"/movie/id/{tmdb_id}")

    if detail:
        render_movie_detail(detail)

    # ── Step 3: TF-IDF recommendations ──
    render_section_header("🤖 AI Content-Based Recommendations (TF-IDF)")

    movie_title = selected.get("title", query)
    with st.spinner("Computing TF-IDF similarity…"):
        tfidf_recs = api_get_live("/recommend/tfidf", {"title": movie_title, "top_n": top_n})

    if tfidf_recs:
        render_poster_grid(tfidf_recs, cols=5, show_score=True)
    else:
        st.info(
            f'"{movie_title}" not found in local dataset. '
            "TF-IDF recommendations are only available for movies in the training corpus."
        )

    # ── Step 4: Genre recommendations ──
    render_section_header("🎭 More Like This (Genre-Based)")

    with st.spinner("Finding similar genre movies…"):
        genre_recs = api_get("/recommend/genre", {"tmdb_id": tmdb_id, "limit": 18})

    if genre_recs:
        render_poster_grid(genre_recs, cols=6)
    else:
        st.info("No genre-based recommendations available.")


def page_browse_tmdb():
    """Browse raw TMDB search results as a grid."""
    st.markdown(
        '<div class="brand-header"><h1>🌐 Browse TMDB</h1>'
        "<p>Explore the full TMDB catalogue</p></div>",
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([4, 1, 1])
    with col1:
        q = st.text_input(
            "Search TMDB",
            placeholder="Search any movie…",
            label_visibility="collapsed",
            key="browse_query",
        )
    with col2:
        page_num = st.number_input("Page", min_value=1, max_value=10, value=1, key="browse_page")
    with col3:
        st.button("Search", use_container_width=True, type="primary", key="browse_btn")

    if q:
        with st.spinner("Searching…"):
            data = api_get_live("/tmdb/search", {"query": q, "page": page_num})

        if data and data.get("results"):
            total = data.get("total_results", 0)
            st.caption(f"📊 {total:,} results found  •  Page {page_num}")

            movies = []
            for r in data["results"]:
                movies.append(
                    {
                        "tmdb_id": r.get("id"),
                        "title": r.get("title", "Unknown"),
                        "poster_url": (
                            f"{TMDB_IMG}{r['poster_path']}"
                            if r.get("poster_path")
                            else None
                        ),
                        "release_date": r.get("release_date"),
                        "vote_average": r.get("vote_average"),
                    }
                )

            render_poster_grid(movies, cols=6)
        else:
            st.warning("No results found.")


def page_about():
    """About / How it works page."""
    st.markdown(
        '<div class="brand-header"><h1>ℹ️ About CineMatch</h1>'
        "<p>How the recommendation engine works</p></div>",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown("### 🧠 TF-IDF Content-Based Filtering")
        st.markdown(
            """
            - Analyses movie **overviews**, **taglines**, and **metadata**
            - Builds a TF-IDF (Term Frequency–Inverse Document Frequency) matrix
            - Computes **cosine similarity** between all movie vectors
            - Returns the most similar movies to your query
            - Pre-computed on **~45,000 movies** from the TMDB dataset
            """
        )

    with col2:
        st.markdown("### 🎭 Genre-Based Discovery")
        st.markdown(
            """
            - Fetches **real-time data** from the TMDB API
            - Identifies the primary genre of your selected movie
            - Discovers **popular movies** in the same genre
            - Always up-to-date with the latest releases
            - Sorted by **popularity** for best results
            """
        )

    st.markdown("---")

    st.markdown("### 🏗️ Architecture")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            '<div class="stat-card">'
            '<div class="stat-value">FastAPI</div>'
            '<div class="stat-label">Backend Framework</div>'
            "</div>",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            '<div class="stat-card">'
            '<div class="stat-value">Streamlit</div>'
            '<div class="stat-label">Frontend UI</div>'
            "</div>",
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            '<div class="stat-card">'
            '<div class="stat-value">TMDB</div>'
            '<div class="stat-label">Movie Database</div>'
            "</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    st.markdown("### 🔌 API Endpoints")
    endpoints = {
        "GET /health": "Health check",
        "GET /home": "Home feed (trending / popular / top_rated / now_playing / upcoming)",
        "GET /tmdb/search": "TMDB keyword search",
        "GET /movie/id/{tmdb_id}": "Detailed movie info",
        "GET /recommend/tfidf": "TF-IDF content-based recommendations",
        "GET /recommend/genre": "Genre-based recommendations",
    }
    for endpoint, desc in endpoints.items():
        st.code(endpoint, language=None)
        st.caption(desc)


def page_movie_detail():
    """Standalone movie detail page — triggered when a poster card is clicked."""
    tmdb_id = st.session_state.selected_movie_id

    # Back button
    if st.button("← Back", key="back_btn"):
        st.session_state.selected_movie_id = None
        st.rerun()

    # Fetch movie details
    with st.spinner("Fetching movie details…"):
        detail = api_get(f"/movie/id/{tmdb_id}")

    if not detail:
        st.error("Could not load movie details.")
        return

    render_movie_detail(detail)

    # TF-IDF recommendations
    movie_title = detail.get("title", "")
    render_section_header("🤖 AI Content-Based Recommendations (TF-IDF)")
    with st.spinner("Computing TF-IDF similarity…"):
        tfidf_recs = api_get_live("/recommend/tfidf", {"title": movie_title, "top_n": 10})

    if tfidf_recs:
        render_poster_grid(tfidf_recs, cols=5, show_score=True, clickable=False)
    else:
        st.info(
            f'"{movie_title}" not found in local dataset. '
            "TF-IDF recommendations are only available for movies in the training corpus."
        )

    # Genre recommendations
    render_section_header("🎭 More Like This (Genre-Based)")
    with st.spinner("Finding similar genre movies…"):
        genre_recs = api_get("/recommend/genre", {"tmdb_id": tmdb_id, "limit": 18})

    if genre_recs:
        render_poster_grid(genre_recs, cols=6)


# ─────────────────────────── SIDEBAR ──────────────────────────
with st.sidebar:
    st.markdown(
        '<div class="brand-header">'
        '<h1>🎬 CineMatch</h1>'
        "<p>Movie Recommendation Engine</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    page = st.radio(
        "Navigation",
        ["🏠 Home", "🔍 Search & Recommend", "🌐 Browse TMDB", "ℹ️ About"],
        label_visibility="collapsed",
        key="nav_radio",
    )

    # Clear detail view when navigating via sidebar
    if st.session_state.selected_movie_id is not None:
        if st.button("← Back to browsing", use_container_width=True):
            st.session_state.selected_movie_id = None
            st.rerun()

    st.markdown("---")

    # Health indicator
    try:
        h = requests.get(f"{API_BASE}/health", timeout=3)
        if h.status_code == 200:
            st.success("🟢  API Online", icon="✅")
        else:
            st.error("🔴  API Error", icon="⚠️")
    except Exception:
        st.error("🔴  API Offline", icon="⚠️")
        st.caption("Run: `uvicorn main:app`")

    st.markdown("---")
    st.caption("Built with ❤️ using FastAPI + Streamlit")
    st.caption("Powered by TMDB & TF-IDF")

# ─────────────────────────── ROUTING ──────────────────────────
# If a movie card was clicked, show the detail page instead
if st.session_state.selected_movie_id is not None:
    page_movie_detail()
elif page == "🏠 Home":
    page_home()
elif page == "🔍 Search & Recommend":
    page_search()
elif page == "🌐 Browse TMDB":
    page_browse_tmdb()
elif page == "ℹ️ About":
    page_about()
