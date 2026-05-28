from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

def split_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """
    Splits text into chunks of specified size with an overlap.
    """
    if not text:
        return []
        
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        # Determine end position
        end = start + chunk_size
        
        # If we are not at the end of the text, try to snap to the nearest space or newline
        # so we don't cut words in half
        if end < text_len:
            # Look backward up to 100 characters for a natural break
            for lookback in range(100):
                if text[end - lookback] in [' ', '\n', '.', ',']:
                    end = end - lookback
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
            
        # Move forward, subtracting overlap
        start += (chunk_size - chunk_overlap)
        
        # Guard against infinite loops if chunk_size <= chunk_overlap
        if chunk_size <= chunk_overlap:
            start = end
            
    logger.info(f"Split text into {len(chunks)} distinct chunks.")
    return chunks