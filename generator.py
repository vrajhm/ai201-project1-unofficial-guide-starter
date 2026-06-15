from groq import Groq

from config import GROQ_API_KEY, GROQ_MODEL

SYSTEM_PROMPT = """You are a helpful campus guide assistant. Answer the user's question using ONLY the provided context documents.

Rules:
- Use only facts explicitly stated in the context. Do not use outside knowledge.
- If the context does not contain enough information, respond exactly: "I don't have enough information on that."
- Be concise and specific.
- When you use information from a source, mention the source filename in your answer."""


def format_context(chunks: list[dict]) -> str:
    parts = []
    for chunk in chunks:
        parts.append(f"[Source: {chunk['source']}]\n{chunk['text']}")
    return "\n\n---\n\n".join(parts)


def generate_response(question: str, chunks: list[dict]) -> str:
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set. Add it to your .env file.")

    context = format_context(chunks)
    client = Groq(api_key=GROQ_API_KEY)

    completion = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}",
            },
        ],
        temperature=0.1,
    )
    return completion.choices[0].message.content.strip()
