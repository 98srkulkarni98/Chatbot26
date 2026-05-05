# Demo for usage of Langchain with LLMs from chat-ai.academiccloud.de
## Overview

This is a simple demo that shows how the API from https://chat-ai.academiccloud.de/v1 can be used. 
It demonstrates how to interact with LLMs (Large Language Models) using Langchain.

For further information about Chat-AI, please also refer to the [Chat-AI.MD](/Chat-AI.md) document.

# Animal Chatbot

A conversational AI chatbot that can switch between a duck and fox persona. The chatbot uses a language model to generate responses and can be interacted with through a web interface.

## Features

- Switch between duck and fox personas
- Web interface built with Streamlit
- FastAPI backend
- Docker support

## Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose (for containerized deployment)
- CHAT_AI_ACCESS_KEY for the language model API

## Local Development Setup

1. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root:
```
CHAT_AI_ACCESS_KEY=your_api_key_here
```

4. Start the FastAPI server:
```bash
cd chatbot
python api.py
```

5. In a new terminal, start the Streamlit app:
```bash
cd chatbot
streamlit run app.py
```

The application will be available at:
- Streamlit Interface: http://localhost:8502
- FastAPI: http://localhost:8000

## Docker Deployment

1. Create a `.env` file in the project root:
```
CHAT_AI_ACCESS_KEY=your_api_key_here
```

2. Build and start the containers:
```bash
docker compose up --build
```

The application will be available at:
- Streamlit Interface: http://localhost:8501
- FastAPI: http://localhost:8000

## Usage

1. Open the Streamlit interface in your browser
2. Start chatting with the bot
3. To switch personas, say:
   - "You are a fox" to switch to fox mode
   - "You are a duck" to switch to duck mode

## Project Structure

```
.
├-- chatbot/
│   ├-- app.py          # Streamlit frontend
│   ├-- api.py          # FastAPI backend
│   ├-- animalbot.py    # Core chatbot logic
│   └-- Dockerfile      # Docker configuration
├-- data/               # Data directory
├-- requirements.txt    # Python dependencies
├-- compose.yml         # Docker Compose configuration
└-- .env               # Environment variables (not in git)
```

## Development

- The frontend is built with Streamlit
- The backend uses FastAPI
- The chatbot logic is in `animalbot.py`
- Docker configuration is in `Dockerfile` and `compose.yml`

## License

This project is licensed under the MIT License - see the LICENSE file for details.

# Animalbot

The animalbot plays the role of a duck. He will only talk about duck related topics. You can tell him to be a fox, in which he will change his personality to being a fox. If you tell him to be a duck, he will change the personality back to duck.

## Example conversation

User: hi

Bot: Quack! Nice to meet you, human! Did you know that we ducks have waterproof feathers? We produce an oil from our uropygial gland that keeps our feathers completely waterproof, allowing us to swim and dive without getting wet!

User: tell me about your feathers

Bot: My feathers! ...

User: you are a fox

Bot: My apologies! As a fox, I'd like to tell you about my silent steps. My fur-covered footpads are specially designed to muffle my steps, allowing me to sneak up on prey with ninja-like silence. It's a vital skill for a hunter like me!

User: what kind of animal yare you?

Bot: I'm a fox! And did you know that, unlike most canines, I can retract my claws, have vertical-slit pupils like cats, and even purr when I'm happy?

User: what? tell me about your claws

Bot: My claws! Unlike most dogs, I have retractable claws that...

## Setting up the Environment Variables

1. Copy the `.env.example` file to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Open the `.env` file in the project directory.
3. Set the `CHAT_AI_ACCESS_KEY` variable to your API key:
   ```
   CHAT_AI_ACCESS_KEY=your_actual_api_key_here
   ```
4. Save the file. The application will use this key by default.

Alternatively, you can set the environment variable at the OS level:

- On Windows (Command Prompt):
  ```cmd
  set CHAT_AI_ACCESS_KEY=your_actual_api_key_here
  ```
- On macOS/Linux (Terminal):
  ```bash
  export CHAT_AI_ACCESS_KEY=your_actual_api_key_here
  ```

## Running AnimalbotInstances

AnimalBot supports running multiple instances using Docker Compose with customizable ports and data directories.

### Basic Usage

Start AnimalBot with default settings:

```bash
docker compose up -d
```

This will:
- Start the API on port 8001
- Start the UI on port 8502
- Use the `./data` directory for storage

### Custom Configuration

Run an instance with custom ports and data directory:

```bash
API_PORT=8003 UI_PORT=8504 DATA_DIR=./data2 API_BASE_URL=http://localhost docker compose -p $(basename "$PWD") up -d
```

This command:
- Uses the current directory name as the project name
- Starts the API on port 8003
- Starts the UI on port 8504
- Uses the `./data2` directory for storage
- Sets the API base URL to http://localhost (change if deploying to a remote server)

### Managing Instances

View logs for the current directory's instance:

```bash
docker compose -p $(basename "$PWD") logs -f
```

Stop the current directory's instance:

```bash
docker compose -p $(basename "$PWD") down
```

List all running Docker Compose projects:

```bash
docker compose ls
```

### Running Multiple Named Instances

For multiple instances, you can use different directories:

```bash
# Create a new instance directory
mkdir -p ~/path/to/animalbot-instance2
cp -r ~/path/to/animalbot/* ~/path/to/animalbot-instance2/

# Start the new instance with custom settings
cd ~/path/to/animalbot-instance2
API_PORT=8003 UI_PORT=8504 API_BASE_URL=http://localhost docker compose -p $(basename "$PWD") up -d
```

Each instance will use its directory name as the Docker Compose project name, keeping services isolated.

### Accessing Your Instances

- First instance API: http://localhost:8001
- First instance UI: http://localhost:8502
- Second instance API: http://localhost:8003  
- Second instance UI: http://localhost:8504

Replace `localhost` with your server's IP or domain name when deploying remotely.
