# The system prompt is the instruction sent once at the start of every
# request that tells the model HOW to behave. Putting "only use this
# context" here (rather than just hoping the model behaves) is what
# makes this actually RAG instead of just a chatbot that ignores your
# documents.
SYSTEM_PROMPT_TEMPLATE = """You are a helpful assistant that answers questions using ONLY the context provided below.

Rules:
- If the answer is not contained in the context, say "I don't have enough information to answer that." Do not use outside knowledge or make anything up.
- Keep answers concise and directly grounded in the context.

Context:
{context}
"""


def build_system_prompt(chunks):
    # chunks is a list of text strings (from retrieve_top_chunks). Joining
    # them with blank lines keeps each chunk visually separate for the
    # model, similar to separate paragraphs.
    context = "\n\n".join(chunks)
    return SYSTEM_PROMPT_TEMPLATE.format(context=context)


if __name__ == "__main__":
    # Quick manual check: does the template fill in correctly?
    example_chunks = ["Chunk one text.", "Chunk two text."]
    print(build_system_prompt(example_chunks))
