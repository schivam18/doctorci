# openai_client.py

import os
from openai import OpenAI
import tiktoken


def calculate_cost(prompt_tokens, completion_tokens):
    # Rates per 1K tokens for 'gpt-4o-mini'
    rate_per_1k_prompt_tokens = 0.00015  # $0.150 per 1M input tokens
    rate_per_1k_completion_tokens = 0.0006  # $0.600 per 1M output tokens

    prompt_cost = (prompt_tokens / 1000) * rate_per_1k_prompt_tokens
    completion_cost = (completion_tokens / 1000) * rate_per_1k_completion_tokens
    total_cost = prompt_cost + completion_cost
    return total_cost


class OpenAIClient:
    def __init__(self, api_key=None):
        # Use the given API key or fetch from environment variable
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "<your OpenAI API key if not set as env var>")
        self.model = 'gpt-4o-mini'  # Fixed model
        # Initialize the OpenAI client
        self.client = OpenAI(api_key=self.api_key)

    def get_chat_completion(self, messages, max_tokens=150):
        # Estimate tokens for messages and completion
        prompt_tokens = self.num_tokens_from_messages(messages)
        # For estimation, assume max_tokens will be used for the completion
        completion_tokens_estimated = max_tokens
        estimated_cost = calculate_cost(prompt_tokens, completion_tokens_estimated)
        print(f"Estimated cost for this request: ${estimated_cost:.6f}")

        # Make request to OpenAI ChatCompletion API
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens
        )

        # Extract the assistant's reply
        response_message = completion.choices[0].message

        # Get actual token usage from response
        usage = completion.usage
        actual_cost = calculate_cost(usage.prompt_tokens, usage.completion_tokens)
        print(f"Actual cost for this request: ${actual_cost:.6f}")

        return response_message

    def num_tokens_from_messages(self, messages):
        """Returns the number of tokens used by a list of messages."""
        try:
            encoding = tiktoken.encoding_for_model(self.model)
        except KeyError:
            # If the model is not recognized, default to 'o200k_base' encoding
            print("Warning: model not found. Using o200k_base encoding.")
            encoding = tiktoken.get_encoding("o200k_base")

        tokens_per_message = 3  # Every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_name = 1  # If there's a name, the role is omitted

        num_tokens = 0
        for message in messages:
            num_tokens += tokens_per_message
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == 'name':
                    num_tokens += tokens_per_name
        num_tokens += 3  # Every reply is primed with <|start|>assistant<|message|>
        return num_tokens
