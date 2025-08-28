# Movie Question API

A FastAPI backend for processing movie questions and generating images using Gemini AI.

## Project Structure

```
project/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
└── README.md          # This file
```

## Setup Instructions

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your Gemini API key:
   ```
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   ```

### 4. Run the Application

```bash
# Development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or using Python directly
python main.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Health Check
- **GET** `/health`
- Returns server health status

### Movie Questions
- **POST** `/ask-movie-question`
- **Body**: `{"question": "your movie question here"}`
- **Response**: 
  ```json
  {
    "model_response": "AI response about the movie",
    "status": "success",
    "question_received": "original question",
    "timestamp": "ISO timestamp"
  }
  ```

### Image Generation
- **POST** `/generate-image`
- **Body**: `{"text": "description for image generation"}`
- **Response**: Generated image (PNG format)

## API Documentation

Once the server is running, visit:
- **Interactive API Docs**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`

## Development Notes

### TODO: Gemini API Integration

The application currently returns mock responses. To integrate with actual Gemini API:

1. **Movie Questions** (in `ask_movie_question` function):
   ```python
   import google.generativeai as genai
   genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
   model = genai.GenerativeModel('gemini-pro')
   response = model.generate_content(request.question)
   model_response = response.text
   ```

2. **Image Generation** (in `generate_image` function):
   ```python
   # Use appropriate Gemini model for image generation
   # Replace placeholder image with actual API response
   ```

### Adding ngrok for External Access

To expose your local server externally (useful for hackathons):

1. Install ngrok: https://ngrok.com/download
2. Run your FastAPI server: `uvicorn main:app --host 0.0.0.0 --port 8000`
3. In another terminal: `ngrok http 8000`
4. Use the provided ngrok URL for external access

### CORS Configuration

The application is configured with permissive CORS settings for development/hackathon use. For production, update the `allow_origins` in the CORS middleware to specific domains.

## Testing

You can test the endpoints using curl:

```bash
# Health check
curl http://localhost:8000/health

# Movie question
curl -X POST "http://localhost:8000/ask-movie-question" \
     -H "Content-Type: application/json" \
     -d '{"question": "What is the best movie of 2023?"}'

# Image generation
curl -X POST "http://localhost:8000/generate-image" \
     -H "Content-Type: application/json" \
     -d '{"text": "a movie poster for a sci-fi adventure"}' \
     --output generated_image.png
```