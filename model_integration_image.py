import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

try:
    from google import genai
    from google.genai import types
except Exception as exc:  # pragma: no cover - import-time failure surface early
    raise ImportError(
        "google-genai is required for image generation. Install with `pip install google-genai`."
    ) from exc


_genai_client: Optional["genai.Client"] = None


def _get_genai_client() -> "genai.Client":
    global _genai_client
    if _genai_client is not None:
        return _genai_client

    # Prefer explicit API key; the client also reads `GOOGLE_API_KEY` from env if not provided.
    api_key = (
        os.environ.get("GOOGLE_API_KEY")
        or os.environ.get("GOOGLE_GENAI_API_KEY")
        or os.environ.get("GENAI_API_KEY")
    )

    if api_key:
        _genai_client = genai.Client(api_key=api_key)
    else:
        _genai_client = genai.Client()

    return _genai_client


def generate_image(input: str) -> bytes:
    """Generate an image from a text prompt using Gemini and return raw bytes.

    Args:
        input: The text prompt describing the desired image.

    Returns:
        Raw image bytes suitable to send to a frontend or save to disk.

    Raises:
        RuntimeError: If the API returns no image data.
    """

    if not input or not input.strip():
        raise ValueError("Prompt `input` must be a non-empty string.")

    client = _get_genai_client()

    # Use the Gemini image generation preview model.
    response = client.models.generate_content(
        model="gemini-2.0-flash-preview-image-generation",
        contents=input,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        ),
    )

    # The response may contain multiple parts; return the first inline image data.
    for candidate in getattr(response, "candidates", []) or []:
        content = getattr(candidate, "content", None)
        if not content:
            continue
        for part in getattr(content, "parts", []) or []:
            inline_data = getattr(part, "inline_data", None)
            if inline_data and getattr(inline_data, "data", None):
                return inline_data.data

    raise RuntimeError("No image data returned from Gemini image generation.")


if __name__ == "__main__":
    resp = generate_image("Beautiful kitty")
    
    from PIL import Image
    import io

    # Display the generated image using PIL
    image = Image.open(io.BytesIO(resp))
    image.show()
