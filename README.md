# Flavortown Discord Bot

A Discord bot that integrates with the Flavortown API, allowing you to query projects, devlogs, users, and store items directly from Discord.
## Prerequisites
- Python 3.8+
- A Discord bot token (get one from [Discord Developer Portal](https://discord.com/developers/applications))
- A Flavortown API key (get one from your [Flavortown account settings](https://flavortown.hackclub.com/account/settings))

## Installation

1. Clone or download this repository

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root:
   ```bash
   cp .env.example .env
   ```

4. Edit `.env` and add your tokens:
   ```
   DISCORD_TOKEN=your_discord_bot_token_here
   FLAVORTOWN_API_KEY=your_flavortown_api_key_here
   ```

## Running the Bot

```bash
python main.py
```

The bot will connect to Discord and sync all slash commands.

## Available Commands

### Projects
- `/project <project_id>` - Get a specific project by ID
- `/projects <query> [page]` - Search for projects

### Devlogs
- `/devlog <devlog_id>` - Get a specific devlog
- `/devlogs [page]` - Get recent devlogs

### Users
- `/user <user_id>` - Get a user's information
- `/users <query> [page]` - Search for users

### Store
- `/store` - View store items
- `/store_item <item_id>` - Get details about a specific store item

## API Documentation

For more information about the Flavortown API, visit: https://flavortown.hackclub.com/api/v1/docs

## Error Handling

The bot includes error handling for:
- Invalid API keys
- Resource not found errors
- API rate limits
- Network errors

## Project Structure

- `main.py` - Main bot file with all commands
- `flavortown_api.py` - API client wrapper
- `requirements.txt` - Python dependencies
- `.env.example` - Template for environment variables
- `.gitignore` - Git ignore rules
