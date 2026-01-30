# How LiteLLM Works - The Translation Layer

## Key Difference: OpenRouter vs LiteLLM

| **OpenRouter** | **LiteLLM** |
|----------------|-------------|
| Cloud proxy service | Python library (runs locally) |
| You send requests to their servers | You import it and call functions |
| They route to various providers | It transforms locally then calls providers directly |
| `https://openrouter.ai/api/v1/chat/completions` | `litellm.completion()` in your code |

## How LiteLLM Transforms Messages

### Step 1: LOCO Sends Standard OpenAI Format

```python
# In src/loco/chat.py, line 197
response = litellm.completion(
    model="bedrock/us.anthropic.claude-sonnet-4",  # <-- Prefix tells LiteLLM what to do
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Read file.py"}
    ],
    tools=[
        {
            "type": "function",
            "function": {
                "name": "read",
                "description": "Read a file",
                "parameters": {...}
            }
        }
    ],
    stream=True
)
```

### Step 2: LiteLLM Detects Provider from Prefix

LiteLLM uses the model prefix to determine which provider adapter to use:

```
"openai/gpt-4o"           → OpenAIAdapter (passes through)
"bedrock/claude-sonnet"   → BedrockAdapter (transforms)
"anthropic/claude-3"      → AnthropicAdapter (transforms)
"ollama/llama3"           → OllamaAdapter (transforms)
"azure/deployment"        → AzureAdapter (transforms)
```

### Step 3: Provider-Specific Transformation

#### Example: OpenAI → Bedrock/Anthropic

**LOCO sends (OpenAI format):**
```python
{
    "model": "bedrock/us.anthropic.claude-sonnet-4-20250514",
    "messages": [
        {"role": "system", "content": "You are helpful"},
        {"role": "user", "content": "Hello"}
    ],
    "tools": [
        {
            "type": "function",
            "function": {
                "name": "read",
                "parameters": {"file_path": {"type": "string"}}
            }
        }
    ]
}
```

**LiteLLM transforms to (Bedrock format):**
```python
{
    "modelId": "us.anthropic.claude-sonnet-4-20250514",
    "system": "You are helpful",  # System message extracted!
    "messages": [
        {"role": "user", "content": [{"text": "Hello"}]}  # Content is now array
    ],
    "toolConfig": {  # Tools renamed!
        "tools": [
            {
                "toolSpec": {
                    "name": "read",
                    "inputSchema": {
                        "json": {"file_path": {"type": "string"}}
                    }
                }
            }
        ]
    }
}
```

**Bedrock responds (Bedrock format):**
```python
{
    "output": {
        "message": {
            "role": "assistant",
            "content": [
                {
                    "toolUse": {
                        "toolUseId": "abc123",
                        "name": "read",
                        "input": {"file_path": "chat.py"}
                    }
                }
            ]
        }
    },
    "usage": {"inputTokens": 100, "outputTokens": 50}
}
```

**LiteLLM transforms back (OpenAI format for LOCO):**
```python
{
    "choices": [
        {
            "delta": {
                "tool_calls": [
                    {
                        "id": "abc123",
                        "function": {
                            "name": "read",
                            "arguments": '{"file_path": "chat.py"}'
                        }
                    }
                ]
            }
        }
    ],
    "usage": {
        "prompt_tokens": 100,
        "completion_tokens": 50
    }
}
```

## Visual Flow

```
┌─────────────────────────────────────────────────────────────┐
│  LOCO                                                        │
│  Sends OpenAI-formatted request                             │
│  {messages: [...], tools: [...]}                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  LiteLLM (Running Locally in Your Python Process)           │
│                                                              │
│  1. Parse model prefix: "bedrock/..."                       │
│  2. Load BedrockAdapter                                     │
│  3. Transform OpenAI format → Bedrock format                │
│     • "messages" → Bedrock message array                    │
│     • Extract "system" to top-level param                   │
│     • "tools" → "toolConfig.tools"                          │
│     • "tool_calls" → "toolUse" blocks                       │
│                                                              │
│  4. Add AWS credentials (from config or env)                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  AWS Bedrock API                                             │
│  Receives native Bedrock format                             │
│  Processes with Claude Sonnet                               │
│  Returns native Bedrock response                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  LiteLLM (Transform Back)                                    │
│                                                              │
│  1. Receive Bedrock response                                │
│  2. Transform Bedrock format → OpenAI format                │
│     • "toolUse" → "tool_calls"                              │
│     • "inputTokens" → "prompt_tokens"                       │
│     • Message content array → simple string                 │
│                                                              │
│  3. Stream chunks in OpenAI format                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  LOCO                                                        │
│  Receives OpenAI-formatted chunks                           │
│  Processes tool_calls identically for all providers         │
│  {delta: {tool_calls: [...]}}                               │
└─────────────────────────────────────────────────────────────┘
```

## Why This Matters

### ✅ **Provider Agnostic**
LOCO doesn't need to know about Bedrock, Anthropic, Ollama formats. It just uses OpenAI format everywhere.

### ✅ **No Network Proxy**
Unlike OpenRouter, LiteLLM runs in your Python process. No extra hop, no proxy server, no latency.

### ✅ **Direct API Calls**
Your credentials go straight to the provider:
- OpenAI API key → openai.com
- AWS credentials → bedrock.amazonaws.com
- Ollama → localhost:11434

### ✅ **140+ Providers**
LiteLLM has adapters for every major LLM provider. Adding support for a new model is often just changing the prefix.

## Example: Switching Providers is Trivial

```bash
# Use OpenAI
loco -m openai/gpt-4o

# Use Bedrock (same conversation, same tools)
loco -m bedrock/us.anthropic.claude-sonnet-4

# Use local Ollama (same conversation, same tools)
loco -m ollama/llama3

# Use Azure (same conversation, same tools)
loco -m azure/my-deployment
```

**Behind the scenes:**
- LiteLLM detects the prefix
- Loads the appropriate adapter
- Transforms messages in/out
- LOCO sees the same OpenAI format from all of them

## Code Example: How LOCO Uses LiteLLM

```python
# From src/loco/chat.py lines 164-197

def stream_response(conversation, tools=None):
    # LOCO builds standard OpenAI format
    kwargs = {
        "model": conversation.model,  # e.g., "bedrock/claude-sonnet"
        "messages": conversation.get_messages(),  # Standard OpenAI format
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    
    # Add provider config (API keys, regions, etc.)
    if conversation.config:
        provider_config = get_provider_config(conversation.model, conversation.config)
        kwargs.update(provider_config)  # e.g., {"aws_region_name": "us-west-2"}
    
    # Add tools in OpenAI format
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"
    
    # LiteLLM does ALL the transformation magic
    response = litellm.completion(**kwargs)
    
    # Response comes back in OpenAI format (regardless of actual provider)
    for chunk in response:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
        if chunk.choices[0].delta.tool_calls:
            # Same structure for OpenAI, Bedrock, Anthropic, Ollama, etc.
            yield parse_tool_call(chunk.choices[0].delta.tool_calls)
```

## Summary

**LiteLLM is like a universal translator library:**
- You always speak "OpenAI" (the lingua franca)
- It translates to/from "Bedrock", "Anthropic", "Ollama", etc.
- It runs **in your code**, not as a cloud proxy
- It's why LOCO can support 140+ providers with ~2,800 lines of code

**Think of it as:**
```
OpenRouter = Google Translate (cloud service)
LiteLLM    = Babel library (local translation)
```

Both translate languages, but one runs remotely (you send requests to their servers), the other runs locally (you import it and call functions).
