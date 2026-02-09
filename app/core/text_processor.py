import re

def format_easy_to_read(text: str) -> str:
    """
    process the generated text for easy_to_read mode.
    Separates each sentence into a different line with space between them.
    Args:
        text (str): The input text to format.
    Returns:
        str: The formatted text.
    """
    # To split sentences, we can use regex to find sentence-ending punctuation.
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    
    # Filter out any empty sentences
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # Join sentences with double newlines for spacing
    formatted_text = '\n\n'.join(sentences)
    
    return formatted_text