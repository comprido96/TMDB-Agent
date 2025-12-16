from agents.router_agent import APIDecision, RouterAgent
from agents.param_extractor import ParameterExtractor, ExtractedParams
from api.tmdb_client import TMDBClient
from api.response_parser import ResponseParser
from agents.answer_generator import AnswerGenerator
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
        decision: APIDecision = self.router.route(user_query)
        print(f"   Decision: {decision.endpoint}")
        print(f"   Reasoning: {decision.reasoning}")

        # Step 2: Parameter Extractor
        print("2️⃣ Parameter Extractor: Extracting parameters...")
        params = self.extractor.extract(user_query, decision.endpoint)
        print(f"   Extracted: {params.model_dump()}")

        # Step 3: API Execution
        print("3️⃣ API Executor: Calling TMDB API...")
        api_response = self.tmdb_client.make_request(decision.endpoint, params)
        # api_response = self._execute_api_call(decision.endpoint, params)
        print(f"   API Response:\n{api_response}")

        # Step 4: Response Parsing
        print("4️⃣ Response Parser: Normalizing data...")
        normalized_data = self.parser.parse_response(decision.endpoint, api_response)
        print(f"   Normalized Data:\n{normalized_data}")

        # Step 5: Answer Generation
        print("5️⃣ Answer Generator: Creating structured answer...")
        final_answer = self.generator.generate_answer(
            user_query, 
            normalized_data, 
            decision.endpoint
        )
        print(f"   Final Answer:\n{final_answer.model_dump()}")

        return {
            "query": user_query,
            "endpoint_used": decision.endpoint,
            "extracted_params": params.model_dump(),
            "api_response_sample": normalized_data[:2] if isinstance(normalized_data, list) else normalized_data,
            "final_answer": final_answer.model_dump()
        }


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
