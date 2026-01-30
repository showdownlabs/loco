# LOCO: Technical Presentation
## How It Works Under the Hood

---

## **The Problem We Solved**

1. **Security vulnerability** in opencode (potential for malicious RPC calls)
2. **Poor UX** - TUI takes over terminal, feels disconnected from your shell
3. **Vendor lock-in** - tied to specific LLM providers

---

## **The Solution: Architecture Overview**

LOCO is a **lightweight CLI that acts as a universal adapter** between you and ANY LLM.

```
┌─────────────┐
│   You       │  "Add authentication"
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│  LOCO (Python CLI)                  │
│  • Conversation management          │
│  • Tool execution (read/write/bash) │
│  • Streaming UI (Rich + Markdown)   │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  LiteLLM (Universal Router)         │
│  • Translates to provider formats   │
│  • Handles auth & retries           │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Any LLM Provider                   │
│  OpenAI | Bedrock | Ollama | etc.   │
└─────────────────────────────────────┘
```

---

## **Key Technical Components**

### **1. Core Loop** (`src/loco/chat.py`)
- Manages conversation state (message history)
- Streams LLM responses using **LiteLLM**
- Parses tool calls from LLM response
- Executes tools and feeds results back

### **2. Tool System** (`src/loco/tools/`)
- **6 built-in tools**: read, write, edit, bash, glob, grep
- Each tool follows OpenAI function calling spec
- Tools execute locally (NO external servers = secure)

### **3. Provider Abstraction** (`config.json`)
```json
{
  "models": {
    "gpt4": "openai/gpt-4o",
    "sonnet": "bedrock/us.anthropic.claude-sonnet-4",
    "local": "ollama/llama3"
  }
}
```
**LiteLLM** handles all provider differences transparently

---

## **Security Model**

✅ **No external servers** - direct API calls only  
✅ **Local tool execution** - you control what runs  
✅ **No telemetry** - your code stays private  
✅ **Open source** - fully auditable  

Compare to opencode's RPC vulnerability → LOCO eliminates the attack surface.

---

## **The UX Innovation**

**Terminal-native design:**
- Stays in your shell session (no TUI takeover)
- Rich markdown rendering with syntax highlighting
- Bash mode (`!` prefix or `Shift+Tab`) for quick commands
- Streaming responses (see AI "think" in real-time)

```bash
> Read chat.py and explain streaming

[Streams markdown with syntax highlighting...]

💭 1,245 tokens (in: 980, out: 265) • $0.0034
```

---

## **Extensibility**

1. **Skills** - Reusable prompts (code-reviewer, debugger)
2. **Commands** - Custom workflows (`/commit`, `/pr`)
3. **Agents** - Subagents with restricted tools/models
4. **Hooks** - Pre/post tool execution scripts
5. **MCP** - Connect to external data sources (databases, APIs)

All configured via simple Markdown files with YAML frontmatter.

---

## **Why It's LOCO (Crazy) Good**

- **140+ LLM providers** via single interface
- Built in **~2,800 lines of Python**
- Compatible with Claude Desktop skills/commands
- Works with **local models** (Ollama) or cloud
- MIT licensed - use it anywhere

---

## **Demo**

```bash
# Install
pipx install git+https://github.com/showdownlabs/loco.git

# Run with any model
loco -m gpt4           # Use alias
loco -m ollama/llama3  # Use local model

# Natural language → working code
> Create a FastAPI endpoint for user authentication
```

**Questions?**
