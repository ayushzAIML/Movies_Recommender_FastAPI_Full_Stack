from fastapi import FastAPI , HTTPException , Query 
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os
from pydantic import BaseModel , Field 
from typing import List , Optional , Annotated , Any , Dict , Tuple
import pandas as pd
import httpx
import numpy as np
import pickle



app = FastAPI(title="Movie Recommendation System API", version="0.1.0")
load_dotenv()
api = os.getenv("TMDB_API_KEY")

TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_IMG_500 = "https://image.tmdb.org/t/p/w500"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


"""

path and global vars

"""
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DF_PATH = os.path.join(BASE_DIR, "df.pkl")
INDICES_PATH = os.path.join(BASE_DIR, "indices.pkl")
TFIDF_MATRIX_PATH = os.path.join(BASE_DIR, "tfidf_matrix.pkl")
TFIDF_PATH = os.path.join(BASE_DIR, "tfidf.pkl")


df : Optional[pd.DataFrame] = None
indices_obj : Any = None
tfidf_matrix : Any = None
tfidf_obj : Any = None

TITLE_TO_IDX : Optional[Dict[str, int]] = None

class TMDBMovieCard(BaseModel):
    tmdb_id: Annotated[int,Field(...,description="The TMDB ID of the movie")]
    title: Annotated[str,Field(...,description="The title of the movie")]
    release_date: Annotated[Optional[str],Field(None,description="The release date of the movie in YYYY-MM-DD format")]
    poster_url: Annotated[Optional[str],Field(None,description="the url of the movie posters")]
    vote_average : Annotated[Optional[float],Field(None,description="the average rating of the movie on TMDB")]

class TMDBMovieDetails(BaseModel):
    tmdb_id: Annotated[int,Field(...,description="The TMDB ID of the movie")]
    title: Annotated[str,Field(...,description="The title of the movie")]
    release_date: Annotated[Optional[str],Field(None,description="The release date of the movie in YYYY-MM-DD format")]
    overview: Annotated[Optional[str],Field(None,description="A brief summary of the movie's plot")]
    poster_url: Annotated[Optional[str],Field(None,description="the url of the movie posters")]
    backdrop_url: Annotated[Optional[str],Field(None,description="the url of the movie backdrop")]
    genres: Annotated[List[Dict[str, Any]],Field(...,description="A list of genres associated with the movie")]


class Recommendation(BaseModel):
     title : Annotated[str,Field(...,description="The title of the recommended movie")]
     score: Annotated[float,Field(...,description="The similarity score of the recommended movie with the input movie")]
     tmdb : Annotated[Optional[TMDBMovieCard],Field(None,description="The TMDB movie card information for the recommended movie")]


class SearchBundleResponse(BaseModel):
    query : Annotated[str,Field(...,description="The search query used to find the movie")]
    movie_details : Annotated[TMDBMovieDetails,Field(None,description="The detailed information of the movie found based on the search query")]
    tfidf_recommendations : Annotated[List[Recommendation],Field(...,description="A list of recommended movies based on TF-IDF similarity")]
    genre_recommendations : Annotated[List[TMDBMovieCard],Field(...,description="A list of recommended movies based on genre similarity")]


"""
utility functions for tmdb api interactions and data normalization
"""
def _norm_title(t :str) ->str:
    return str(t).strip().lower()


def make_img_url(path:Optional[str]) -> Optional[str]:
    if not path:
        return None
    return f"{TMDB_IMG_500}{path}"


"""
used to bring moviuee detailz
"""

async def tmdb_get(path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Docstring for tmdb_get
    
    :param path: Description
    :type path: str
    :param params: Description
    :type params: Optional[Dict[str, Any]]
    :return: Description
    :rtype: Dict[str, Any]

    network errors -> 502
    tmdb apu error -> 502 with details
    """

    if not api:
        raise HTTPException(
            status_code=503,
            detail="TMDB_API_KEY is not configured on the server"
        )

    q = dict(params or {})
    q["api_key"] = api

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(f"{TMDB_BASE}{path}", params=q)
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=502,
            detail=f"TMDB request error:{type(e).__name__} | {repr(e)}"
        )
    
    if r.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"TMDB API error: {r.status_code} : {r.text}"
        )
    return r.json()


"""
used to convert tmdb search results into movie cards
"""

async def tmdb_cards_from_results(
        results: List[dict] , limit: int = 20
) -> List[TMDBMovieCard]:
    out: List[TMDBMovieCard] = []

    for res in results[:limit]:
        out.append(
            TMDBMovieCard(
                tmdb_id = int(res["id"]),
                title= res.get("title") or res.get("name") or "",
                poster_url= make_img_url(res.get("poster_path")),
                release_date= res.get("release_date") or res.get("first_air_date") or None,
                vote_average= res.get("vote_average")
            )
        )
    return out



"""
used to get detailed movie information from tmdb based on movie id
"""
async def tmdb_movie_details(movie_id:int) -> TMDBMovieDetails:
    data = await tmdb_get(f"/movie/{movie_id}",{"language":"en-US"})
    return TMDBMovieDetails(
        tmdb_id = int(data["id"]),
        title= data.get("title") or data.get("name") or "",
        poster_url= make_img_url(data.get("poster_path")),
        backdrop_url= make_img_url(data.get("backdrop_path")),
        release_date= data.get("release_date") or data.get("first_air_date") or None,
        overview= data.get("overview"),
        genres= data.get("genres",[]) or [],
    )



"""
raw tmdb response for keyword search, used to find movie id based on search query

"""
async def tmdb_search_movie(query:str, page:int=1) -> Dict[str, Any]:
    return await tmdb_get(
        "/search/movie",
        {"query": query , 
         "page": page , 
         "language":"en-US",
         "include_adult": False},
         )

"""
very first search result from tmdb search, used to find movie id based on search query, used in search bundle endpoint
"""
async def tmdb_search_first(query:str) -> Optional[dict]:
    data = await tmdb_search_movie(query, page=1)
    results = data.get("results", [])
    return results[0] if results else None


"""
indices_pkl can be:
takes data from dict(title -> index)
returns pandas seriesss (index=title , value = index) if indices_pkl is a pandas series
we normalize into title_to_idx
"""

def build_title_to_idx_map(indices : Any) -> Dict[str,int]:


    title_to_idx : Dict[str, int] = {}

    if isinstance(indices, dict):
        for title , idx in indices.items():
            title_to_idx[_norm_title(title)] = int(idx)
        return title_to_idx
    
    """
    pandas series or sikmilar mapping
    """
    try:
        for title , idx in indices.items():
            title_to_idx[_norm_title(title)] = int(idx)
        return title_to_idx
    except Exception as e:
        raise RuntimeError(
            f"Failed to build title_to_idx map: {e}"
        )


def get_local_idx_by_title(title:str) -> int:
    global TITLE_TO_IDX

    if TITLE_TO_IDX is None:
        raise HTTPException(
            status_code=500,
            detail="Internal server error: title_to_idx map not initialized"
        )
    
    key = _norm_title(title)
    if key in TITLE_TO_IDX:
        return int(TITLE_TO_IDX[key])
    raise HTTPException(
        status_code=404,
        detail=f"Movie with title '{title}' not found in local dataset"
    )


def tfidf_recommend_titles(
        query_title : str, top_k: int = 10
) -> List[Tuple[str, float]]:
    """
    returns list of (title , score) tuples for top_k recommendations based on tfidf similarity
    """
    global df , tfidf_matrix
    if df is None or tfidf_matrix is None:
        raise HTTPException(
            status_code=500,
            detail="Internal server error: TF-IDF data not loaded"
        )
    
    idx = get_local_idx_by_title(query_title)

    qv = tfidf_matrix[idx]
    scores = (tfidf_matrix @qv.T).toarray().flatten()

    order =np.argsort(-scores)

    out : List[Tuple[str, float]] = []
    for i in order:
        if int(i) == int(idx):
            continue
        try:
            title_i = str(df.iloc[int(i)]["title"])
        except Exception:
            continue
        out.append((title_i, float(scores[int(i)])))
        if len(out) >= top_k:
            break
    return out




"""
uses tmdb search by title too fetch poster for a local title.
if not found , returns none(never crashes at the endpoint)
"""

async def attach_tmdb_card_by_title(title: str) -> Optional[TMDBMovieCard]:
    try:
        m = await tmdb_search_first(title)
        if not m:
            return None
        return TMDBMovieCard(
            tmdb_id=int(m["id"]),
            title=m.get("title") or title,
            poster_url=make_img_url(m.get("poster_path")),
            release_date=m.get("release_date") or None,
            vote_average=m.get("vote_average"),
        )
    
    except Exception:
        return None
    

@app.on_event("startup")
def load_pickles():
    global df , indices_obj , tfidf_matrix , tfidf_obj , TITLE_TO_IDX

    with open(DF_PATH,"rb") as f:
        df = pickle.load(f)

    with open(INDICES_PATH,"rb") as f:
        indices_obj = pickle.load(f)
    

    with open(TFIDF_MATRIX_PATH,"rb") as f:
        tfidf_matrix = pickle.load(f)

    with open(TFIDF_PATH,"rb") as f:
        tfidf_obj = pickle.load(f)

    TITLE_TO_IDX = build_title_to_idx_map(indices_obj)

    if df is None or "title" not in df.columns:
        raise RuntimeError("Dataframe not loaded properly or missing 'title' column")
    
@app.get("/health")
def health():
    return {"status":"ok"}

@app.get("/home", response_model=List[TMDBMovieCard])
async def home(
    category: str = Query("popular"),
    limit: int = Query(24, ge=1, le=50),
):
    """
    Home feed for Streamlit (posters).
    category:
      - trending (trending/movie/day)
      - popular, top_rated, upcoming, now_playing  (movie/{category})
    """
    try:
        if category == "trending":
            data = await tmdb_get("/trending/movie/day", {"language": "en-US"})
            return await tmdb_cards_from_results(data.get("results", []), limit=limit)

        if category not in {"popular", "top_rated", "upcoming", "now_playing"}:
            raise HTTPException(status_code=400, detail="Invalid category")

        data = await tmdb_get(f"/movie/{category}", {"language": "en-US", "page": 1})
        return await tmdb_cards_from_results(data.get("results", []), limit=limit)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Home route failed: {e}")


# ---------- TMDB KEYWORD SEARCH (MULTIPLE RESULTS) ----------
@app.get("/tmdb/search")
async def tmdb_search(
    query: str = Query(..., min_length=1),
    page: int = Query(1, ge=1, le=10),
):
    """
    Returns RAW TMDB shape with 'results' list.
    Streamlit will use it for:
      - dropdown suggestions
      - grid results
    """
    return await tmdb_search_movie(query=query, page=page)


# ---------- MOVIE DETAILS (SAFE ROUTE) ----------
@app.get("/movie/id/{tmdb_id}", response_model=TMDBMovieDetails)
async def movie_details_route(tmdb_id: int):
    return await tmdb_movie_details(tmdb_id)


# ---------- GENRE RECOMMENDATIONS ----------
@app.get("/recommend/genre", response_model=List[TMDBMovieCard])
async def recommend_genre(
    tmdb_id: int = Query(...),
    limit: int = Query(18, ge=1, le=50),
):
    """
    Given a TMDB movie ID:
    - fetch details
    - pick first genre
    - discover movies in that genre (popular)
    """
    details = await tmdb_movie_details(tmdb_id)
    if not details.genres:
        return []

    genre_id = details.genres[0]["id"]
    discover = await tmdb_get(
        "/discover/movie",
        {
            "with_genres": genre_id,
            "language": "en-US",
            "sort_by": "popularity.desc",
            "page": 1,
        },
    )
    cards = await tmdb_cards_from_results(discover.get("results", []), limit=limit)
    return [c for c in cards if c.tmdb_id != tmdb_id]


# ---------- TF-IDF ONLY (debug/useful) ----------
@app.get("/recommend/tfidf")
async def recommend_tfidf(
    title: str = Query(..., min_length=1),
    top_n: int = Query(10, ge=1, le=50),
):
    recs = tfidf_recommend_titles(title, top_k=top_n)
    return [{"title": t, "score": s} for t, s in recs]


# ---------- BUNDLE: Details + TF-IDF recs + Genre re