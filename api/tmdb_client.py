import requests
import os
from dotenv import load_dotenv
from typing import Dict, Any, Optional
import json
from agents.param_extractor import ExtractedParams

load_dotenv()


REQUEST_TIMEOUT = 10


class TMDBClient:
    ENDPOINTS = {
        "search_movie": "/search/movie",
        "discover_movies": "/discover/movie",
        "search_person": "/search/person",
        "movie_certifications": "/certification/movie/list",
        "genre_list": "/genre/movie/list",
    }

    def __init__(self):
        self.api_key = os.getenv("TMDB_API_READ_ACCESS_TOKEN")
        self.base_url = "https://api.themoviedb.org/3"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def make_request(self, endpoint: str, params: ExtractedParams) -> Dict[str, Any]:
        """Make a request to the TMDB API based on the endpoint and parameters"""

        if endpoint not in self.ENDPOINTS:
            raise ValueError(f"Unknown endpoint: {endpoint}")

        url = f"{self.base_url}{self.ENDPOINTS[endpoint]}"
        params = self._parse_params(params)
        response = requests.get(url, headers=self.headers, params=params, timeout=REQUEST_TIMEOUT)
        try:
            response.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(f"TMDB API error: {e}") from e

        return response.json()

    def _parse_params(self, params: ExtractedParams) -> Dict[str, Any]:
        """Convert ExtractedParams to a dictionary suitable for TMDB API"""
        parsed_params = {}
        parsed_params["sort_by"] = params.sort_by or "popularity.desc"
        if params.query:
            parsed_params["query"] = params.query
        if params.primary_release_year:
            parsed_params["primary_release_year"] = params.primary_release_year
        if params.with_genres:
            parsed_params["with_genres"] = params.with_genres
        if params.with_people:
            parsed_params["with_people"] = params.with_people

        return parsed_params

    def _extract_person_id(self, api_response: Dict[str, Any]) -> Optional[int]:
        """Extract person ID from search results"""
        results = api_response.get("results", [])
        if results:
            return results[0].get("id")
        return None


if __name__ == "__main__":
    client = TMDBClient()
    params = ExtractedParams(query="Inception")
    result = client.make_request("search_movie", params)
    print(json.dumps(result, indent=2))
