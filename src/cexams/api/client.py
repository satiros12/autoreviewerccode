"""
OpenRouter API client for exam evaluation
"""

import json
import logging
from typing import Any, Dict

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """Client for OpenRouter AI API"""

    def __init__(
        self,
        api_key: str,
        model: str = "deepseek/deepseek-chat",
        max_retries: int = 3,
        backoff_factor: float = 1.0,
    ):
        """
        Initialize OpenRouter client

        Args:
            api_key: OpenRouter API key
            model: AI model to use
            max_retries: Maximum number of retry attempts
            backoff_factor: Backoff factor for exponential retry
        """
        self.api_key = api_key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://cexams.local",
            "X-Title": "CExams AI Reviewer",
        }

        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic"""
        session = requests.Session()
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=self.backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def call_api(self, prompt: str, system_prompt: str = "") -> str:
        """
        Call OpenRouter API with given prompt

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)

        Returns:
            AI response text
        """
        if system_prompt is None:
            system_prompt = (
                "You are an expert C programming evaluator. "
                "Analyze code and provide detailed evaluations in JSON format."
            )

        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 2000,
        }

        try:
            logger.info("Calling OpenRouter AI API...")
            response = self.session.post(self.base_url, headers=self.headers, json=data, timeout=60)
            response.raise_for_status()

            result = response.json()
            ai_response = result["choices"][0]["message"]["content"]
            logger.info("AI API call successful")

            return ai_response

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            raise
        except KeyError as e:
            logger.error(f"Unexpected API response format: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in AI API call: {e}")
            raise

    @staticmethod
    def parse_ai_response(response_text: str) -> Dict[str, Any]:
        """
        Parse AI response JSON

        Args:
            response_text: AI response text

        Returns:
            Parsed JSON as dictionary
        """
        try:
            # Clean the response - sometimes AI adds markdown code blocks
            cleaned_response = response_text.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()

            result = json.loads(cleaned_response)
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.error(f"Response text: {response_text[:500]}...")
            raise
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            raise
