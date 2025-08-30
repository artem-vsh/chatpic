from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from datetime import datetime
import logging
import os
from dotenv import load_dotenv
import io, sys
# from PIL import Image

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import model_integration
import model_integration_image


from PIL import Image
import io

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Movie Question API",
    description="A FastAPI backend for movie questions and image generation",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for hackathon/development use
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MovieQuestionRequest(BaseModel):
    question: str

class ImageGenerationRequest(BaseModel):
    text: str

class MovieQuestionResponse(BaseModel):
    model_response: str
    status: str
    question_received: str
    timestamp: str

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/ask-movie-question", response_model=MovieQuestionResponse)
async def ask_movie_question(request: MovieQuestionRequest):
    """
    Process movie questions and return AI-generated responses
    
    TODO: Integrate with Gemini API here
    - Use google.generativeai library
    - Configure with GEMINI_API_KEY from environment
    - Send request.question to the model
    - Parse and return the actual response
    """
    try:
        logger.info(f"Received movie question: {request.question}")

        response = model_integration.generate_text(request.question)

        # mock_response = f"This is a mock response about your movie question: '{request.question}'. Replace this with actual Gemini API integration."
        
        return MovieQuestionResponse(
            model_response=response,
            status="success",
            question_received=request.question,
            timestamp=datetime.now().isoformat()
        )
    
    except Exception as e:
        logger.error(f"Error processing movie question: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/generate-image")
async def generate_image(request: ImageGenerationRequest):
    """
    Generate images based on text prompts
    
    TODO: Integrate with Gemini API for image generation
    - Use google.generativeai library
    - Configure with GEMINI_API_KEY from environment
    - Use appropriate Gemini model for image generation
    - Return actual generated image
    """
    try:
        logger.info(f"Received image generation request: {request.text}")


        image_data = model_integration_image.generate_image(request.text)

        # logger.info(f"Generated image data: {image_data}")

        # Convert to PIL Image if needed
        image = Image.open(io.BytesIO(image_data))
        
        # Process the image if needed (resize, format conversion, etc.)
        # image = image.resize((400, 300))  # Example processing
        
        # Convert back to bytes
        img_buffer = io.BytesIO()
        image.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        return Response(
            content=img_buffer.getvalue(),
            media_type="image/png",
            headers={"Content-Disposition": "inline; filename=generated_image.png"}
        )
    
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating image")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)