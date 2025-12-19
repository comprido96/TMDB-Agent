import json
from typing import Dict


def create_completion(client, system_prompt: str, user_prompt: str) -> Dict:
        """Helper function to create a chat completion and parse JSON response"""
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1
        )

        result = json.loads(response.choices[0].message.content)
        return result
