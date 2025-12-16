import requests
import os
from dotenv import load_dotenv
from typing import Dict, Any, Optional
import json

load_dotenv()


class TMDBClient:
    def __init__(self):
        self.api_key = os.getenv("TMDB_API_READ_ACCESS_TOKEN")
        self.base_url = "https://api.themoviedb.org/3"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def search_movie(self, query: str, **kwargs) -> Dict[str, Any]:
        """Search movies by title"""
        url = f"{self.base_url}/search/movie"
        params = {"query": query, **kwargs}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def discover_movies(self, **kwargs) -> Dict[str, Any]:
        """Discover movies with filters"""
        url = f"{self.base_url}/discover/movie"
        params = {k: v for k, v in kwargs.items() if v is not None}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def movie_details(self, movie_id: int) -> Dict[str, Any]:
        """Get movie details by ID"""
        url = f"{self.base_url}/movie/{movie_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def search_person(self, query: str) -> Dict[str, Any]:
        """Search for a person/actor"""
        url = f"{self.base_url}/search/person"
        params = {"query": query}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_genres(self) -> Dict[str, Any]:
        """Get movie genre list"""
        url = f"{self.base_url}/genre/movie/list"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()


if __name__ == "__main__":
    client = TMDBClient()
    result = client.search_movie("Inception")
    print(json.dumps(result, indent=2))
