SYSTEM_PROMPT_TEMPLATE = """You are a helpful assistant that answers questions using ONLY the context provided below.

Rules:
- If the answer is not contained in the context, say "I don't have enough information to answer that." Do not use outside knowledge or make anything up.
- Keep answers concise and directly grounded in the context.

Context:
{context}
"""


def build_system_prompt(chunks):
    context = "\n\n".join(chunks)
    return SYSTEM_PROMPT_TEMPLATE.format(context=context)


if __name__ == "__main__":
    example_chunks = ["Chunk one text.", "Chunk two text."]
    print(build_system_prompt(example_chunks))
