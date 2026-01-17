# loco

A Claude Code-inspired CLI for any OpenAI-compatible LLM via LiteLLM.

## Features

- **Multi-provider support**: OpenAI, Amazon Bedrock, OpenRouter, Ollama, LM Studio, and any LiteLLM-supported provider
- **Streaming responses**: Real-time token streaming with markdown rendering
- **Built-in tools**: Read, Write, Edit files and execute Bash commands
- **Secure**: No external server - direct API calls only, config file permissions enforced
- **Model aliases**: Define shortcuts for frequently used models

## Installation

```bash
# From git
pip install git+https://github.com/yourusername/loco.git

# Or for development
git clone https://github.com/yourusername/loco.git
cd loco
pip install -e .
```

## Configuration

Config is stored at `~/.config/loco/config.json`. Created automatically on first run.

```json
{
  "default_model": "openai/gpt-4o",
  "models": {
    "gpt4": "openai/gpt-4o",
    "sonnet": "bedrock/us.anthropic.claude-sonnet-4-20250514",
    "local": "ollama/llama3"
  },
  "providers": {
    "openai": {
      "api_key": "${OPENAI_API_KEY}"
    },
    "bedrock": {
      "aws_region": "us-west-2"
    },
    "openrouter": {
      "api_key": "${OPENROUTER_API_KEY}"
    }
  }
}
```

Environment variables are expanded (`${VAR}` syntax).

## Usage

```bash
# Start with default model
loco

# Use a specific model (alias or full name)
loco --model gpt4
loco --model bedrock/us.anthropic.claude-sonnet-4-20250514

# Start in a specific directory
loco --cwd /path/to/project
```

### Commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/model [name]` | Show or switch current model |
| `/clear` | Clear conversation history |
| `/config` | Show config file path |
| `/quit` | Exit (or Ctrl+C) |

## Supported Providers

Via LiteLLM, loco supports:

- **OpenAI**: `openai/gpt-4o`, `openai/gpt-4o-mini`
- **Amazon Bedrock**: `bedrock/us.anthropic.claude-sonnet-4-20250514`
- **OpenRouter**: `openrouter/anthropic/claude-3.5-sonnet`
- **Ollama**: `ollama/llama3`, `ollama/codellama`
- **LM Studio**: `lm_studio/local-model`
- **Azure OpenAI**: `azure/deployment-name`
- And [many more](https://docs.litellm.ai/docs/providers)

## Tools

loco includes these built-in tools:

- **read**: Read file contents with line numbers
- **write**: Create or overwrite files
- **edit**: Edit files via string replacement
- **bash**: Execute shell commands

## License

MIT
