\# This block is not meant to run. Save the content as cli\_qa\_prd.md.



"""

CLI Q\&A Tool - PRD (Product Requirements Document)



What it does:

&#x20; A command-line tool that takes a multi-paragraph text and a question,

&#x20; then uses an LLM to answer the question with paragraph-level citations.



Input:

&#x20; 1. Multi-line text from user (terminated by typing 'END' on a new line)

&#x20; 2. A question about the text



Output:

&#x20; An answer that references specific paragraphs using \[Paragraph X] format.



Done when / acceptance tests:

&#x20; - User can paste text and ask questions in the terminal

&#x20; - Answers include \[Paragraph X] citations

&#x20; - Uses OpenRouter API (qwen/qwen3.5-flash-02-23 model)

&#x20; - API key loaded from .env file and never printed

&#x20; - A question answered by Paragraph 1 cites \[Paragraph 1]

&#x20; - A question absent from the text returns: The text does not provide this information.

&#x20; - An empty text input shows a friendly error instead of calling the API

&#x20; - python3 -m py\_compile cli\_qa.py succeeds

"""

