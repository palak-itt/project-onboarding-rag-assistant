
# Used tiktokenizer and charater count tools to check how many tokens it amounts to, and how many characters. 
# Basically roughly around 1600 charaters amounter to 360 tokens with cl100k_base embedding model.
# What I am doing here is doing character wise split, so initial 512 seems very less for tokens\. Because Iw as assuming it is tokens.
# Now if i use nomic-embed-text - it has 2k token context window, when run with ollama, so I should look at increasing the character count.
# Design decision change chunk size from 512 to 1024 after 1 st iteration. then from 1024 to 2048 fter 2nd iteration, in similar ration, increase overlap too.
def fixed_chunks(text, size=512, overlap=100):
    step = size-overlap

    return [text[i:i+size] for i in range(0, len(text), step) if text[i: i+size].strip()]


def recursive_chunks(text, size=800, seps=("\n## ", "\n\n", "\n", ". ", " ")):
    """Split on the biggest natural boundary first; only go finer if a piece is still too long."""
    text = text.strip()
    if len(text) <= size:
        return [text] if text else []

    if not seps:
        return [text[i:i + size] for i in range(0, len(text), size)]

    sep, rest = seps[0], seps[1:]

    out, cur = [], ""
    for part in text.split(sep):
        cand = (cur + sep + part) if cur else part
        if len(cand) <= size:
            cur = cand
        else:
            if cur:
                out.append(cur)
            if len(part) > size:
                out.extend(recursive_chunks(part, size, rest))
                cur = ""
            else:
                cur = part
        if cur:
            out.append(cur)
    return out