import tiktoken
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

TOKEN_LIMIT = 8000
COMPRESSION_THRESHOLD = 6000

def count_tokens(messages: list[dict]) -> int:
    encoder = tiktoken.get_encoding("cl100k_base")

    total = 0
    for message in messages:
        content = message.get("content", "")
        total += len(encoder.encode(content))
    return total


def should_compress(token_count: int) -> bool:
    return token_count >= COMPRESSION_THRESHOLD

def split_messages(messages: list[dict]) -> tuple[list[dict], list[dict]]:

    #split the list
    split_point = int(len(messages)* 0.6)

    #everything before split 
    old_messages = messages[:split_point]

    #messages after split 
    recent_messages = messages[split_point:]

    return old_messages, recent_messages

def compress_messages(messages: list[dict]) -> str:
    client = Groq()

    # convert list of message dicts into a readable string
    messages_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
    response = client.chat.completions.create(
        model= "llama-3.3-70b-versatile",
        messages= [
            {
                "role": "system",
                "content": """Summarize this conversation history concisely.
                You must preserve:
                - What the user is building
                - All decisions made so far
                - User preferences observed
                - Current plan state
                - Any open or unanswered questions
                Return only the summary. No extra text."""
            },
            {
                "role": "user",
                "content": messages_text
            }
        ]
    )
    return response.choices[0].message.content

def maybe_compress(messages: list[dict])-> tuple[list[dict], str | None]:

    # first count how many tokens we currently have
    token_count = count_tokens(messages)

    # if we are under threshold, do nothing
    if not should_compress(token_count):
        return messages, None

    # split messages into old and recent
    old_messages, recent_messages = split_messages(messages)

    # compress the old messages into a summary string
    summary = compress_messages(old_messages)

    # wrap summary as a system message so LLM treats it as context
    # not as part of the conversation
    summary_message = {
        "role": "system",
        "content": f"[CONVERSATION SUMMARY]: {summary}"
    }

    # new messages = summary of old + recent messages intact
    compressed = [summary_message] + recent_messages

    return compressed, summary