from openai import OpenAI
from pydantic import BaseModel
from typing import Literal
import json
from dotenv import load_dotenv
import os

load_dotenv()


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class APIDecision(BaseModel):
    """Schema for API routing decision"""
    endpoint: Literal[
        "search_movie",
        "discover_movies", 
        "movie_details",
        "search_person",
        "genre_list"
    ]
    reasoning: str
    required_params: list[str]


class RouterAgent:
    def __init__(self):
        self.system_prompt = """You are a TMDB API router. Your job is to analyze user queries and determine:
        1. Which TMDB endpoint to call
        2. What parameters are needed
        
        Available endpoints:
        - search_movie: When user wants to search movies by title
        - discover_movies: When user wants movies with filters (genre, year, actor, etc.)
        - movie_details: When user wants details about a specific movie
        - search_person: When user wants to find a person/actor
        - genre_list: When user asks about genres
        
        Return your decision in JSON format following this schema:
        {
            "endpoint": "<chosen_endpoint>",
            "reasoning": "<explanation>",
            "required_params": ["<param1>", "<param2>", ...]
        }
        """

    def route(self, user_query: str) -> APIDecision:
        """Determine which API endpoint to call"""
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_query}
            ],
            temperature=0.1
        )
        
        result = json.loads(response.choices[0].message.content)
        return APIDecision(**result)


if __name__ == "__main__":
    router = RouterAgent()
    decision = router.route("Find action movies from 2023 with Keanu Reeves")
    print(decision)
