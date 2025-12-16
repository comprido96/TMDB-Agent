from typing import Dict, Any, List, Optional
from datetime import datetime


class ResponseParser:
    def normalize_movie(self, movie_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize movie data to consistent schema"""
        return {
            "id": movie_data.get("id"),
            "title": movie_data.get("title"),
            "release_date": movie_data.get("release_date"),
            "overview": movie_data.get("overview", "")[:200] + "..." if movie_data.get("overview") else "",
            "popularity": round(movie_data.get("popularity", 0), 2),
            "vote_average": movie_data.get("vote_average"),
            "vote_count": movie_data.get("vote_count"),
            "poster_path": f"https://image.tmdb.org/t/p/w500{movie_data.get('poster_path', '')}" if movie_data.get("poster_path") else None
        }

    def normalize_movies_list(self, api_response: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
        """Normalize list of movies"""
        movies = api_response.get("results", [])
        normalized = []
        
        for movie in movies[:limit]:
            normalized.append(self.normalize_movie(movie))
        
        return normalized

    def normalize_person(self, person_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize person data"""
        return {
            "id": person_data.get("id"),
            "name": person_data.get("name"),
            "known_for_department": person_data.get("known_for_department"),
            "popularity": round(person_data.get("popularity", 0), 2),
            "known_for": [
                item.get("title") or item.get("name") 
                for item in person_data.get("known_for", [])[:3]
            ]
        }

    def extract_person_id(self, api_response: Dict[str, Any]) -> Optional[int]:
        """Extract person ID from search results"""
        results = api_response.get("results", [])
        if results:
            return results[0].get("id")
        return None


if __name__ == "__main__":
    parser = ResponseParser()
    mock_movie = {"id": 1, "title": "Test", "overview": "Test overview"}
    normalized = parser.normalize_movie(mock_movie)
    print(normalized)
