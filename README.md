# Chatpic

An intelligent chatbot application that combines text generation with visual output. Users can send prompts to receive AI-generated responses and corresponding images based on the generated text.

## Features

- **Text Generation**: Natural language processing using LangGraph and Neo4j integration
- **Image Generation**: AI-powered image creation from text prompts
- **Movie Database Integration**: Specialized endpoints for movie-related questions with Neo4j graph database support
- **Real-time Processing**: FastAPI backend with CORS support for seamless frontend integration
- **Modern UI**: Clean, responsive web interface built with Tailwind CSS

## Architecture

### Backend (`/backend/`)
- **FastAPI**: RESTful API server with automatic documentation
- **Neo4j Integration**: Graph database for movie data queries using Cypher
- **LangGraph**: Agent-based text generation workflow
- **Multiple AI Models**: Support for SambaNova, DeepSeek, and Google Gemini models
- **Galileo Integration**: AI observability and monitoring

### Frontend
- **Single Page Application**: Modern HTML/CSS/JavaScript interface
- **Tailwind CSS**: Utility-first styling framework
- **Responsive Design**: Works across desktop and mobile devices
- **Real-time Updates**: Dynamic content loading and image display

## API Endpoints

- `GET /health` - Health check endpoint
- `POST /ask-movie-question` - Process movie-related questions and return AI responses
- `POST /generate-image` - Generate images from text prompts

## Tech Stack

### Backend Dependencies
- FastAPI - Modern, fast web framework for building APIs
- Neo4j - Graph database for movie data
- LangGraph - Framework for building stateful multi-actor applications
- OpenAI/SambaNova APIs - AI model integrations
- Galileo - AI observability platform
- Google Generative AI - Image and text generation
- Python-dotenv - Environment variable management

### Frontend
- Vanilla JavaScript - No framework dependencies
- Tailwind CSS - Utility-first CSS framework
- Modern fetch API - For backend communication

## Getting Started

### Prerequisites
- Python 3.8+
- Neo4j database instance
- API keys for SambaNova, OpenAI, and Google AI services

### Installation

1. Clone the repository
2. Install backend dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Copy `template.env` to `.env`
   - Configure your API keys and database credentials

4. Start the backend server:
   ```bash
   cd backend
   python main.py
   ```

5. Open `index.html` in your browser or serve it via a web server

## Environment Variables

Create a `.env` file based on `template.env` with the following variables:
- `SAMBANOVA_API_KEY` - SambaNova API key
- `NEO4J_URI` - Neo4j database URI
- `NEO4J_USERNAME` - Neo4j username
- `NEO4J_PASSWORD` - Neo4j password
- `GEMINI_API_KEY` - Google Gemini API key
- `MODEL_FAST` - Fast model identifier (default: Meta-Llama-3.3-70B-Instruct)
- `MODEL` - Primary model identifier (default: Deepseek-V3.1)

## Usage

1. Open the web interface
2. Enter a prompt in the text area
3. Click "Send" or press Enter
4. View the AI-generated text response
5. See the corresponding generated image based on the text

The application supports both general prompts and movie-specific questions, leveraging the Neo4j database for enhanced movie-related responses.
