from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
from datetime import datetime
import re


class ExtractedParams(BaseModel):
    """Schema for extracted parameters"""
    query: Optional[str] = None
    year: Optional[int] = None
    genre: Optional[str] = None
    person_name: Optional[str] = None
    movie_id: Optional[int] = None
    with_genres: Optional[str] = None
    with_people: Optional[str] = None


class ParameterExtractor:
    def __init__(self,):
        self.genre_map = {
            "action": 28, "adventure": 12, "animation": 16,
            "comedy": 35, "crime": 80, "documentary": 99,
            "drama": 18, "family": 10751, "fantasy": 14,
            "history": 36, "horror": 27, "music": 10402,
            "mystery": 9648, "romance": 10749, "science fiction": 878,
            "tv movie": 10770, "thriller": 53, "war": 10752,
            "western": 37
        }

    def extract(self, user_query: str, endpoint: str) -> ExtractedParams:
        """Extract parameters based on endpoint type"""
        
        params = ExtractedParams()

        # Extract year using regex
        year_match = re.search(r'\b(20\d{2}|19\d{2})\b', user_query)
        if year_match:
            params.year = int(year_match.group())

        # Extract genre
        query_lower = user_query.lower()
        for genre_name, genre_id in self.genre_map.items():
            if genre_name in query_lower:
                params.genre = genre_name
                params.with_genres = str(genre_id)
                break

        # Extract person name (simple pattern)
        if "with" in query_lower or "starring" in query_lower:
            # This is simplified - in production would use NER
            parts = re.split(r'with|starring|featuring', query_lower, maxsplit=1)
            if len(parts) > 1:
                potential_name = parts[1].strip().split()[0:2]  # First 2 words
                params.person_name = " ".join(potential_name).title()

        # For search endpoints, extract query
        if endpoint in ["search_movie", "search_person"]:
            # Remove common words and extract main query
            stop_words = ["find", "search", "for", "movies", "movie", "about"]
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
