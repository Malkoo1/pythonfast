from typing import Optional
from urllib.parse import urlparse

import html2text
import requests
from bs4 import BeautifulSoup


def extract_text_from_url(url: str) -> dict:
    """
    Extract clean text from a website URL
    Returns:
        {
            "text": extracted text,
            "title": page title,
            "url": cleaned URL,
            "word_count": number of words,
            "char_count": number of characters
        }
    """
    try:
        # Validate and clean URL
        parsed = urlparse(url)
        if not parsed.scheme:
            url = f"https://{url}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        # Fetch webpage
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # Remove unwanted elements
        for element in soup(["script", "style", "nav", "footer", "iframe", "noscript"]):
            element.decompose()

        # Get title
        title = soup.title.string if soup.title else "No title found"

        # Convert HTML to clean text
        h = html2text.HTML2Text()
        h.ignore_links = True
        h.ignore_images = True
        h.ignore_emphasis = True
        h.ignore_tables = True
        clean_text = h.handle(str(soup))

        # Clean up whitespace
        clean_text = " ".join(clean_text.split())

        return {
            "text": clean_text,
            "title": title,
            "url": url,
            "word_count": len(clean_text.split()),
            "char_count": len(clean_text),
        }

    except Exception as e:
        raise ValueError(f"Failed to extract text from URL: {str(e)}")
