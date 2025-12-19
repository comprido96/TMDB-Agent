from openai import OpenAI
from typing import Dict, Any
import json
from pydantic import BaseModel, ValidationError
from dotenv import load_dotenv
import os

from agents.base import create_completion

load_dotenv()


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class StructuredAnswer(BaseModel):
    """Schema for final structured answer"""
    answer: str
    data_summary: Dict[str, Any]
    source: str = "TMDB API"
    confidence: float


class AnswerGenerator:
    def __init__(self):
        self.system_prompt = """You are a helpful movie assistant. Your task is to:
        1. Analyze the provided movie data from TMDB API
        2. Generate a concise, informative answer to the user's query
        3. Include key details from the data
        4. Format the response as JSON with the following structure:
        {
            "answer": "<concise_answer>",
            "data_summary": {
                // key-value pairs summarizing the data
            },
            "source": "TMDB API",
            "confidence": <confidence_score_between_0_and_1>
        }
        Be factual and only use information from the provided data. Do not use prior knowledge. Remember that we are in year 2025 currently."""

    def generate_answer(self, user_query: str, api_data: Dict[str, Any], endpoint: str) -> StructuredAnswer:
        """Generate structured final answer"""

        prompt = f"""
        User Query: {user_query}
        API Endpoint Used: {endpoint}
        API Response Data: {json.dumps(api_data, indent=2)}
        
        Generate a helpful answer based on this data.
        """
        response = create_completion(client, system_prompt=self.system_prompt, user_prompt=prompt)
        try:
            return StructuredAnswer(**response)
        except ValidationError as e:
            raise RuntimeError(f"Invalid LLM output schema: {e}")


if __name__ == "__main__":
    generator = AnswerGenerator()
    mock_data = {"results": [{"title": "Test Movie", "overview": "A test movie overview.", "release_date": "2023-01-01", "vote_average": 7}]}
    answer = generator.generate_answer("Find movies", mock_data, "search_movie")
    print(answer)
