import requests
import os
from dotenv import load_dotenv
from typing import Dict, Any, Optional
import json

from agents.param_extractor import ExtractedParams

load_dotenv()


class TMDBClient:
    ENDPOINTS = {
        "search_movie": "/search/movie",
        "discover_movies": "/discover/movie",
        "search_person": "/search/person",
        "movie_certifications": "/certification/movie/list",
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
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def _parse_params(self, params: ExtractedParams) -> Dict[str, Any]:
        """Convert ExtractedParams to a dictionary suitable for TMDB API"""
        parsed_params = {}
        parsed_params["sort_by"] = params.sort_by or "popularity.desc"
        if params.query:
            parsed_params["query"] = params.query
        if params.year:
            parsed_params["year"] = params.year
        if params.primary_release_year:
            parsed_params["primary_release_year"] = params.primary_release_year
        if params.with_genres:
            parsed_params["with_genres"] = params.with_genres
        if params.with_people:
            parsed_params["with_people"] = params.with_people
        # if params.person_name:
        #     person_result = self.tmdb_client.search_person(params.person_name)
        #     person_id = self.parser.extract_person_id(person_result)
        #     if person_id:
        #         api_params["with_people"] = person_id
        
        # if params.movie_id:
        #     return self.tmdb_client.movie_details(params.movie_id)
        # # Fallback: search for movie first
        # search_result = self.tmdb_client.search_movie(query=params.query or "")
        # if search_result.get("results"):
        #     movie_id = search_result["results"][0]["id"]
        #     return self.tmdb_client.movie_details(movie_id)
        # return {"error": "Movie not found"}

        return parsed_params


if __name__ == "__main__":
    client = TMDBClient()
    result = client.search_movie("Inception")
    print(json.dumps(result, indent=2))
