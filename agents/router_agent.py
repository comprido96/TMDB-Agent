from openai import OpenAI
from pydantic import BaseModel
from typing import Literal
from dotenv import load_dotenv
import os

from agents.base import create_completion

load_dotenv()


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class APIDecision(BaseModel):
    """Schema for API routing decision"""
    endpoint: Literal[
        "search_movie",
        "discover_movies", 
        "search_person",
        "movie_certifications",
        "genre_list",
    ]
    reasoning: str


class RouterAgent:
    def __init__(self):
        self.system_prompt = """You are a TMDB API router. Your job is to analyze user queries and determine which TMDB endpoint to call.

        Available endpoints:
        - search_movie: When user wants to search movies by title
        - discover_movies: When user wants movies with filters (genre, year, actor, etc.)
        - search_person: When user wants to find a person/actor
        - movie_certifications: Get an up to date list of the officially supported movie certifications on TMDB.
        - genre_list: Get the list of official genres for movies.

        Return your decision in JSON format following this schema:
        {
            "endpoint": "<chosen_endpoint>",
            "reasoning": "<explanation>",
        }
        """

    def route(self, user_query: str) -> APIDecision:
        """Determine which API endpoint to call"""
        response = create_completion(client, system_prompt=self.system_prompt, user_prompt=user_query)
        return APIDecision(**response)


if __name__ == "__main__":
    router = RouterAgent()
    decision = router.route("Find action movies from 2023 with Keanu Reeves")
    print(decision)
