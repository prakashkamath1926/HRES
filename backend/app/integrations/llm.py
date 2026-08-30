import json
import logging
import os
import concurrent.futures
from typing import Type, TypeVar, Callable, Generator
from pydantic import BaseModel
from litellm import completion
from backend.app.core.config import settings

logger = logging.getLogger("hres.llm")

T = TypeVar("T", bound=BaseModel)

# Models
XKIRO_MODEL = "openai/qwen/qwen3.6-27b:free"
GROQ_MODEL = "groq/llama-3.1-8b-instant"

class LLMService:
    @staticmethod
    def _call_provider(provider: str, prompt: str, json_mode: bool) -> str:
        messages = [{"role": "user", "content": prompt}]
        kwargs = {"messages": messages}
        
        if provider == "groq":
            if not getattr(settings, "GROQ_API_KEY", None):
                raise ValueError("GROQ_API_KEY is not set.")
            os.environ["GROQ_API_KEY"] = settings.GROQ_API_KEY
            kwargs["model"] = GROQ_MODEL
        else:
            if not getattr(settings, "KIRO_API_KEY", None):
                raise ValueError("KIRO_API_KEY is not set.")
            kwargs["model"] = XKIRO_MODEL
            kwargs["api_key"] = settings.KIRO_API_KEY
            kwargs["api_base"] = "https://api.xkiro.com/v1"

        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
            
        response = completion(**kwargs)
        return response.choices[0].message.content.strip()

    @staticmethod
    def generate(prompt: str, json_mode: bool = False) -> str:
        providers = []
        if getattr(settings, "GROQ_API_KEY", None):
            providers.append("groq")
        if getattr(settings, "KIRO_API_KEY", None):
            providers.append("xkiro")

        if not providers:
            raise ValueError("No LLM API keys configured (KIRO or GROQ).")

        if len(providers) == 1:
            return LLMService._call_provider(providers[0], prompt, json_mode)

        # Race both and return the fastest successful result
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_to_provider = {
                executor.submit(LLMService._call_provider, p, prompt, json_mode): p
                for p in providers
            }
            errors = []
            for future in concurrent.futures.as_completed(future_to_provider):
                try:
                    return future.result()
                except Exception as e:
                    provider = future_to_provider[future]
                    logger.warning(f"{provider.capitalize()} API failed: {e}")
                    errors.append(str(e))
            
            raise ValueError(f"All LLM providers failed. Errors: {errors}")

    @staticmethod
    def stream_chat(messages: list[dict], system_prompt: str | None = None) -> Generator[str, None, None]:
        """Stream chat completions falling back to available providers."""
        providers = []
        if getattr(settings, "GROQ_API_KEY", None):
            providers.append("groq")
        if getattr(settings, "KIRO_API_KEY", None):
            providers.append("xkiro")

        if not providers:
            yield "[Error: No API keys configured. Set KIRO_API_KEY or GROQ_API_KEY in your .env file.]"
            return

        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        last_error = None
        for provider in providers:
            try:
                kwargs = {
                    "messages": full_messages,
                    "stream": True,
                    "temperature": 0.7,
                    "max_tokens": 1024
                }
                
                if provider == "groq":
                    os.environ["GROQ_API_KEY"] = settings.GROQ_API_KEY
                    kwargs["model"] = GROQ_MODEL
                else:
                    kwargs["model"] = XKIRO_MODEL
                    kwargs["api_key"] = settings.KIRO_API_KEY
                    kwargs["api_base"] = "https://api.xkiro.com/v1"
                
                stream = completion(**kwargs)
                
                for chunk in stream:
                    if chunk.choices and len(chunk.choices) > 0:
                        content = chunk.choices[0].delta.content
                        if content:
                            yield content
                return  # If successful, don't try the next provider
            except Exception as e:
                logger.warning(f"Streaming failed for {provider}: {e}")
                last_error = str(e)
                
        yield f"[Connection error: {last_error}]"

    @classmethod
    def generate_structured(
        cls,
        prompt: str,
        schema_class: Type[T],
        fallback_factory: Callable[[], T]
    ) -> T:
        schema_json = json.dumps(schema_class.model_json_schema(), indent=2)
        full_prompt = (
            f"{prompt}\n\n"
            f"You MUST return your response as a JSON object matching this schema:\n"
            f"{schema_json}\n\n"
            f"Do not include any extra explanation or markdown block indicators."
        )

        try:
            response_text = cls.generate(full_prompt, json_mode=True)
            if response_text.startswith("```"):
                lines = response_text.splitlines()
                if lines[0].startswith("```json"):
                    lines = lines[1:]
                elif lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                response_text = "\n".join(lines).strip()

            parsed_data = json.loads(response_text)
            return schema_class.model_validate(parsed_data)
        except Exception as e:
            logger.warning(f"LLM generation failed or returned invalid JSON. Using fallback. Error: {e}")
            return fallback_factory()
