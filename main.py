from agents.router_agent import RouterAgent, APIDecision
from agents.param_extractor import ParameterExtractor, ExtractedParams
from api.tmdb_client import TMDBClient
from api.response_parser import ResponseParser
from agents.answer_generator import AnswerGenerator, StructuredAnswer
from typing import Dict, Any
import json


class TMDBMovieAgent:
    """Main orchestrator for the multi-agent pipeline"""
    
    def __init__(self):
        self.router = RouterAgent()
        self.extractor = ParameterExtractor()
        self.tmdb_client = TMDBClient()
        self.parser = ResponseParser()
        self.generator = AnswerGenerator()

    def process_query(self, user_query: str) -> Dict[str, Any]:
        """Process user query through the full pipeline"""
        
        print(f"\n🔍 Processing query: '{user_query}'")

        # Step 1: Router Agent
        print("1️⃣ Router Agent: Determining endpoint...")
        decision = self.router.route(user_query)
        print(f"   Decision: {decision.endpoint}")
        print(f"   Reasoning: {decision.reasoning}")

        # Step 2: Parameter Extractor
        print("2️⃣ Parameter Extractor: Extracting parameters...")
        params = self.extractor.extract(user_query, decision.endpoint)
        print(f"   Extracted: {params.model_dump()}")

        # Step 3: API Execution
        print("3️⃣ API Executor: Calling TMDB API...")
        api_response = self._execute_api_call(decision.endpoint, params)

        # Step 4: Response Parsing
        print("4️⃣ Response Parser: Normalizing data...")
        normalized_data = self._parse_response(decision.endpoint, api_response)

        # Step 5: Answer Generation
        print("5️⃣ Answer Generator: Creating structured answer...")
        final_answer = self.generator.generate_answer(
            user_query, 
            normalized_data, 
            decision.endpoint
        )

        return {
            "query": user_query,
            "endpoint_used": decision.endpoint,
            "extracted_params": params.model_dump(),
            "api_response_sample": normalized_data[:2] if isinstance(normalized_data, list) else normalized_data,
            "final_answer": final_answer.model_dump()
        }

    def _execute_api_call(self, endpoint: str, params: ExtractedParams) -> Dict[str, Any]:
        """Execute the appropriate API call"""
        
        if endpoint == "search_movie":
            return self.tmdb_client.search_movie(query=params.query or "")

        elif endpoint == "discover_movies":
            api_params = {}
            if params.year:
                api_params["primary_release_year"] = params.year
            if params.with_genres:
                api_params["with_genres"] = params.with_genres
            
            # Handle person search if needed
            if params.person_name:
                person_result = self.tmdb_client.search_person(params.person_name)
                person_id = self.parser.extract_person_id(person_result)
                if person_id:
                    api_params["with_people"] = person_id
            
            return self.tmdb_client.discover_movies(**api_params)

        elif endpoint == "search_person":
            return self.tmdb_client.search_person(query=params.query or params.person_name or "")
        
        elif endpoint == "movie_details":
            if params.movie_id:
                return self.tmdb_client.movie_details(params.movie_id)
            # Fallback: search for movie first
            search_result = self.tmdb_client.search_movie(query=params.query or "")
            if search_result.get("results"):
                movie_id = search_result["results"][0]["id"]
                return self.tmdb_client.movie_details(movie_id)
            return {"error": "Movie not found"}
        
        elif endpoint == "genre_list":
            return self.tmdb_client.get_genres()
        
        else:
            raise ValueError(f"Unknown endpoint: {endpoint}")

    def _parse_response(self, endpoint: str, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and normalize API response"""

        if endpoint in ["search_movie", "discover_movies"]:
            movies = self.parser.normalize_movies_list(api_response)
            return {
                "movies": movies,
                "total_results": api_response.get("total_results", 0),
                "page": api_response.get("page", 1)
            }
        
        elif endpoint == "movie_details":
            return self.parser.normalize_movie(api_response)
        
        elif endpoint == "search_person":
            persons = api_response.get("results", [])
            normalized = []
            for person in persons[:3]:
                normalized.append(self.parser.normalize_person(person))
            return {
                "persons": normalized,
                "total_results": api_response.get("total_results", 0)
            }
        
        elif endpoint == "genre_list":
            return api_response
        
        return api_response


if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv
    
    load_dotenv()
    
    agent = TMDBMovieAgent()
    
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        example_queries = [
            "Find action movies from 2023",
            "Search for movies with Leonardo DiCaprio",
            "What are the details of the movie Inception?",
            "Find comedy movies from 2022",
            "Who is Tom Hanks and what movies is he known for?"
        ]
        print("\n🎬 TMDB Movie Agent - Example Queries:")
        for i, q in enumerate(example_queries, 1):
            print(f"{i}. {q}")
        
        choice = input("\nEnter query number or type your own: ")
        
        if choice.isdigit() and 1 <= int(choice) <= len(example_queries):
            query = example_queries[int(choice) - 1]
        else:
            query = choice if choice else example_queries[0]
    
    try:
        result = agent.process_query(query)
        
        print("\n" + "="*50)
        print("🎉 FINAL RESULT")
        print("="*50)
        print(f"Query: {result['query']}")
        print(f"Endpoint used: {result['endpoint_used']}")
        print(f"\n📊 Extracted Parameters:")
        for key, value in result['extracted_params'].items():
            if value:
                print(f"  - {key}: {value}")
        
        print(f"\n🤖 AI Answer:")
        print(result['final_answer']['answer'])
        
        print(f"\n📈 Data Summary:")
        print(json.dumps(result['final_answer']['data_summary'], indent=2))
        
        print(f"\n🔗 Source: {result['final_answer']['source']}")
        print(f"📊 Confidence: {result['final_answer']['confidence']}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("Please check your API keys in .env file")
