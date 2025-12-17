"""
TODO
1. Mismatch between extracted fields and TMDB API

Example:

with_people: Optional[str]  # names


But TMDB /discover/movie expects person IDs, not names.

You partially acknowledge this elsewhere, but here the pipeline still leaks names downstream.

This is the single biggest technical flaw in the agents layer.

Best fix (recommended)

Rename field to with_people_names

Resolve names → IDs in a dedicated resolution step

Only inject IDs into tmdb_client

If you don’t implement it, document it clearly as a known limitation.
"""


from openai import OpenAI
from pydantic import BaseModel
from typing import Literal, Optional
import re
from dotenv import load_dotenv
import os

from agents.base import create_completion

load_dotenv()


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


GENRE_MAP = {
    "action": 28, "adventure": 12, "animation": 16,
    "comedy": 35, "crime": 80, "documentary": 99,
    "drama": 18, "family": 10751, "fantasy": 14,
    "history": 36, "horror": 27, "music": 10402,
    "mystery": 9648, "romance": 10749, "science fiction": 878,
    "tv movie": 10770, "thriller": 53, "war": 10752,
    "western": 37
}


class ExtractedParams(BaseModel):
    """Schema for extracted parameters"""
    query: Optional[str] = None
    primary_release_year: Optional[int] = None
    with_genres: Optional[str] = None
    with_people_names: Optional[str] = None
    with_people: Optional[str] = None
    sort_by: Optional[str] = None


class SearchMovieAgent:
    def __init__(self):
        self.system_prompt = """You are a parameter extraction agent for TMDB API calls to /search/movie.
        Your job is to extract relevant parameters from user queries. The parameters to extract are:
        - query: The movie title or keywords
        - primary_release_year: The release year of the movie (if mentioned)

        Return the extracted parameters in JSON format following this schema:
        {
            "query": "<movie_title_or_keywords>",
            "primary_release_year": <release_year_or_null>
        }
        """

    def extract(self, user_query: str) -> ExtractedParams:
        """Extract parameters for /search/movie endpoint"""
        response = create_completion(client, system_prompt=self.system_prompt, user_prompt=user_query)

        # minimal safeguard
        return ExtractedParams.model_validate(response, strict=False)


class DiscoverMoviesAgent:
    def __init__(self):
        self.system_prompt = """You are a parameter extraction agent for TMDB API calls to /discover/movie.
        Your job is to extract relevant parameters from user queries. The parameters to extract are:
        - primary_release_year: The release year of the movies (if mentioned)
        - with_genres: The genres of the movies (if mentioned), separated by commas
        - with_people: The name of actors/actresses (if mentioned), separated by commas

        Return the extracted parameters in JSON format following this schema:
        {
            "primary_release_year": <primary_release_year_or_null>,
            "with_genres": "<with_genres_or_null>",
            "with_people": "<with_people or_null>"
        }
        """

    def extract(self, user_query: str) -> ExtractedParams:
        """Extract parameters for /discover/movie endpoint"""
        response = create_completion(client, system_prompt=self.system_prompt, user_prompt=user_query)

        if response.get("with_genres"):
            genres = response.get("with_genres").lower().split(",")
            genre_ids = []
            for genre in genres:
                genre = genre.strip()
                if genre in GENRE_MAP:
                    genre_ids.append(str(GENRE_MAP[genre]))
            response["with_genres"] = ",".join(genre_ids)

        # minimal safeguard
        return ExtractedParams.model_validate(
            {
                "primary_release_year": response.get("primary_release_year"),
                "with_genres": response.get("with_genres"),
                "with_people_names": response.get("with_people"),
            },
            strict=False
        )


class SearchPersonAgent:
    def __init__(self):
        self.system_prompt = """You are a parameter extraction agent for TMDB API calls to /search/person.
        Your job is to extract relevant parameters from user queries. The parameters to extract are:
        - query: The name of the person/actor or known as name (if mentioned)
        Return the extracted parameters in JSON format following this schema:
        {
            "query": "<person_name_or_keywords>"
        }
        """

    def extract(self, user_query: str) -> ExtractedParams:
        """Extract parameters for /search/person endpoint"""
        response = create_completion(client, system_prompt=self.system_prompt, user_prompt=user_query)

        # minimal safeguard
        return ExtractedParams.model_validate(response, strict=False)


EXTRACTORS = {
    "search_movie": SearchMovieAgent,
    "discover_movies": DiscoverMoviesAgent,
    "search_person": SearchPersonAgent,
}

class ParameterExtractor:
    def extract(self, user_query: str, endpoint: str) -> ExtractedParams:
        """Extract parameters based on endpoint type"""

        # Use specialized agents if available
        if endpoint in EXTRACTORS:
            agent = EXTRACTORS[endpoint]()
            params = agent.extract(user_query)
        else: # Else, use simple regex-based extraction as fallback
            params = self._simple_extraction(user_query, endpoint)

        return params

    def _simple_extraction(self, user_query: str, endpoint: str) -> ExtractedParams:
        """A simple regex-based parameter extraction as fallback"""
        params = ExtractedParams()
        # Extract year using regex
        year_match = re.search(r'\b(20\d{2}|19\d{2})\b', user_query)
        if year_match:
            params.primary_release_year = int(year_match.group())

        # Extract genre
        query_lower = user_query.lower()
        genre_ids = []
        for genre_name, genre_id in GENRE_MAP.items():
            if genre_name in query_lower:
                genre_ids.append(str(genre_id))
        if genre_ids:
            params.with_genres = ",".join(genre_ids)

        # Extract person name (simple pattern)
        if "with" in query_lower or "starring" in query_lower:
            # This is simplified - in production would use NER (Named Entity Recognition)
            parts = re.split(r'with|starring|featuring', query_lower, maxsplit=1)
            if len(parts) > 1:
                potential_name = parts[1].strip().split()[0:2]  # First 2 words
                params.person_name = " ".join(potential_name).title()

        # For search endpoints, extract query
        if endpoint in ["search_movie", "search_person"]:
            # Remove common words and extract main query
            stop_words = ["find", "search", "for", "movies", "movie", "about", "who", "is", "the", "a", "an", "in", "on", "at", "of", "and", "with", "starring"]
            words = user_query.lower().split()
            query_words = [w for w in words if w not in stop_words]
            params.query = " ".join(query_words[:3])  # First 3 words as query
        
        return params


if __name__ == "__main__":
    extractor = ParameterExtractor()
    params = extractor.extract(
        "Find action movies from 2023 with Keanu Reeves",
        "discover_movies"
    )
    print(params)
