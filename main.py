from pydantic import BaseModel, Field
from agents.router_agent import RouterAgent
from agents.param_extractor import ParameterExtractor, ExtractedParams
from api.tmdb_client import TMDBClient
from api.response_parser import ResponseParser
from agents.answer_generator import AnswerGenerator
from typing import Dict, Any, Optional
import json


class StepResult(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


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
        route_result = self._safe_route(user_query)
        if not route_result.success:
            return self._error_response(route_result, user_query)

        decision = route_result.data
        print(f"   Decision: {decision.endpoint}")
        print(f"   Reasoning: {decision.reasoning}")

        # Step 2: Parameter Extractor
        print("2️⃣ Parameter Extractor: Extracting parameters...")
        extract_result = self._safe_extract(user_query, decision.endpoint)
        if not extract_result.success:
            return self._error_response(extract_result, user_query)

        params = extract_result.data
        print(f"   Extracted: {params.model_dump()}")

        # Step 2.5: Resolve people names → IDs
        resolve_result = self._resolve_people(params)
        if not resolve_result.success:
            return self._error_response(resolve_result, user_query)

        params = resolve_result.data

        # Step 3: API Execution
        print("3️⃣ API Executor: Calling TMDB API...")
        api_call_result = self._safe_api_call(decision.endpoint, params)
        if not api_call_result.success:
            return self._error_response(api_call_result, user_query)
        api_response = api_call_result.data
        print(f"   API Response:\n{api_response}")

        # Step 4: Response Parsing
        print("4️⃣ Response Parser: Normalizing data...")
        parse_result = self._safe_parse(decision.endpoint, api_response)
        if not parse_result.success:
            return self._error_response(parse_result, user_query)
        
        normalized_data = parse_result.data
        movies = normalized_data.get("movies", [])
        api_response_sample = movies[:2] if "movies" in normalized_data else normalized_data
        print(f"   Normalized Data:\n{normalized_data}")

        # Step 5: Answer Generation
        print("5️⃣ Answer Generator: Creating structured answer...")
        answer_result = self._safe_generate_answer(
            user_query, 
            normalized_data, 
            decision.endpoint
        )
        if not answer_result.success:
            return self._error_response(answer_result, user_query)
        
        final_answer = answer_result.data
        print(f"   Final Answer:\n{final_answer.model_dump()}")

        return {
            "query": user_query,
            "endpoint_used": decision.endpoint,
            "extracted_params": params.model_dump(),
            "api_response_sample": api_response_sample,
            "final_answer": final_answer.model_dump()
        }

    def _error_response(self, step_result: StepResult, user_query: str) -> Dict[str, Any]:
        return {
            "query": user_query,
            "status": "failed",
            "error": step_result.error,
            "metadata": step_result.metadata,
            "confidence": 0.0
        }

    def _safe_route(self, query: str) -> StepResult:
        try:
            decision = self.router.route(query)
            return StepResult(
                success=True,
                data=decision,
                metadata={
                    "endpoint": decision.endpoint,
                    "fallback": "Fallback" in decision.reasoning
                }
            )
        except Exception as e:
            return StepResult(
                success=False,
                error=f"Routing failed: {str(e)}"
            )
    
    def _safe_extract(self, query: str, endpoint: str) -> StepResult:
        try:
            params = self.extractor.extract(query, endpoint)
            return StepResult(
                success=True,
                data=params,
                metadata={"params": params.model_dump()}
            )
        except Exception as e:
            return StepResult(
                success=False,
                error=f"Parameter extraction failed: {str(e)}"
            )

    def _resolve_people(self, params: ExtractedParams) -> StepResult:
        if not params.with_people_names:
            return StepResult(success=True, data=params)

        try:
            people_ids = []

            for name in params.with_people_names.split(","):
                response = self.tmdb_client.make_request(
                    "search_person",
                    ExtractedParams(query=name.strip())
                )
                results = response.get("results", [])
                if results:
                    people_ids.append(str(results[0]["id"]))
            if people_ids:
                params.with_people = ",".join(people_ids)

            return StepResult(success=True, data=params)
        except Exception as e:
            return StepResult(
                success=False,
                error=f"People resolution failed: {str(e)}"
            )

    def _safe_api_call(self, endpoint: str, params: ExtractedParams) -> StepResult:
        try:
            response = self.tmdb_client.make_request(endpoint, params)
            return StepResult(
                success=True,
                data=response,
                metadata={"raw_response": response}
            )
        except Exception as e:
            return StepResult(
                success=False,
                error=f"API call failed: {str(e)}"
            )
    
    def _safe_parse(self, endpoint: str, response: Dict[str, Any]) -> StepResult:
        try:
            normalized_data = self.parser.parse_response(endpoint, response)
            return StepResult(
                success=True,
                data=normalized_data,
                metadata={"normalized_data": normalized_data}
            )
        except Exception as e:
            return StepResult(
                success=False,
                error=f"Response parsing failed: {str(e)}"
            )
    
    def _safe_generate_answer(self, query: str, data: Any, endpoint: str) -> StepResult:
        try:
            answer = self.generator.generate_answer(query, data, endpoint)
            return StepResult(
                success=True,
                data=answer,
                metadata={"final_answer": answer.model_dump()}
            )
        except Exception as e:
            return StepResult(
                success=False,
                error=f"Answer generation failed: {str(e)}"
            )


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
