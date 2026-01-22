# SparkyAI 🤖✨

An AI-powered portfolio chatbot that serves as an interactive resume. Instead of reading a static document, recruiters and visitors can have conversations with an AI that knows everything about my professional background.

![SparkyAI Demo](docs/demo.gif)

## ✨ Features

### 🎯 Interactive Resume
- Natural language Q&A about skills, experience, and projects
- Instant, accurate responses powered by RAG (Retrieval-Augmented Generation)
- Handles both specific questions and general inquiries

### 🧠 Real AI Agent Architecture
- **LangGraph** state machine with conditional routing
- Multi-node pipeline: Intent Classification → RAG Retrieval → Response Generation
- Fallback handling for low-confidence queries
- Not a simple chatbot - a production-grade AI system

### 👁️ Real-Time Visualization
- **Agent Graph**: D3.js force-directed visualization of the reasoning process
- **Embedding Explorer**: 2D t-SNE projection of semantic space
- **Trace Timeline**: See exactly how long each step takes
- Watch the AI "think" in real-time via WebSocket streaming

### 🔒 Production-Ready
- Rate limiting and budget protection
- Prompt injection detection
- Comprehensive observability (Langfuse)
- CI/CD with GitHub Actions

## 🛠️ Tech Stack

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **D3.js** - Data visualization
- **Tailwind CSS** - Utility-first styling
- **Zustand** - State management

### Backend
- **FastAPI** - High-performance Python API
- **LangGraph** - Stateful AI agents
- **LangChain** - LLM orchestration
- **OpenAI** - GPT-4o-mini & embeddings

### Infrastructure
- **Vercel** - Frontend hosting
- **Railway** - Backend hosting
- **Upstash Redis** - Session management (free tier)
- **Langfuse** - LLM observability

## 📦 Project Structure

```
sparky-ai/
├── packages/
│   ├── agent-core/          # LangGraph agent logic
│   │   ├── agent_core/
│   │   │   ├── nodes/       # Graph nodes (greeter, intent, rag, response)
│   │   │   ├── utils/       # Security, sanitization
│   │   │   ├── graph.py     # Main state machine
│   │   │   ├── state.py     # State schema
│   │   │   ├── prompts.py   # Prompt templates
│   │   │   └── config.py    # Settings
│   │   └── pyproject.toml
│   │
│   ├── server/              # FastAPI server
│   │   ├── server/
│   │   │   ├── middleware/  # Security headers
│   │   │   ├── utils/       # Redis, budget tracking
│   │   │   ├── main.py      # API routes & WebSocket
│   │   │   └── websocket.py # Connection manager
│   │   └── pyproject.toml
│   │
│   └── web/                 # Next.js frontend
│       ├── src/
│       │   ├── app/         # Pages
│       │   ├── components/  # React components
│       │   │   ├── chat/    # Chat widget
│       │   │   ├── ui/      # Reusable UI
│       │   │   └── visualizations/  # D3.js components
│       │   ├── hooks/       # Custom hooks
│       │   ├── stores/      # Zustand stores
│       │   └── types/       # TypeScript types
│       └── package.json
│
├── knowledge/               # RAG knowledge base
│   ├── resume/             # Professional info
│   ├── projects/           # Project details
│   └── meta/               # Contact, FAQ
│
├── scripts/
│   └── generate_embeddings.py  # Create vector embeddings
│
├── infrastructure/
│   └── docker/             # Docker configs
│
└── .github/
    └── workflows/          # CI/CD pipelines
```

## 🚀 Quick Start

> **📖 For detailed setup instructions, see [SETUP.md](./SETUP.md)**

### Prerequisites
- Python 3.11+
- Node.js 18+
- OpenAI API key
- Upstash Redis account (free tier)

### 1. Clone & Install

```bash
git clone https://github.com/yourusername/sparky-ai.git
cd sparky-ai

# Install frontend dependencies
cd packages/web && npm install && cd ../..

# Install backend dependencies (from project root)
pip install -e packages/agent-core
pip install -e packages/server
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

Required keys:
- `OPENAI_API_KEY` - For GPT-4o-mini and embeddings
- `UPSTASH_REDIS_REST_URL` (optional) - For session persistence
- `UPSTASH_REDIS_REST_TOKEN` (optional)

### 3. Generate Embeddings

```bash
python scripts/generate_embeddings.py
```

This creates vector embeddings from the `knowledge/` markdown files.

### 4. Run Development Servers

```bash
# Terminal 1: Backend
cd packages/server
uvicorn server.main:app --reload --port 8000

# Terminal 2: Frontend
cd packages/web
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000)

## 🎨 Customization

### Switching to Buzzy (EasyBee Demo)

The codebase supports a dual-persona architecture. To switch from SparkyAI to Buzzy:

```bash
# In .env
AGENT_CONFIG=buzzy
```

Then update the `knowledge/` folder with EasyBee-specific content.

### Adding Knowledge

1. Add markdown files to `knowledge/` folder
2. Run `python scripts/generate_embeddings.py`
3. Restart the backend

### Modifying the Agent

The LangGraph agent is in `packages/agent-core/agent_core/graph.py`. Key customization points:

- `prompts.py` - Modify AI responses
- `nodes/intent_classifier.py` - Add new intent categories
- `nodes/rag_retriever.py` - Tune retrieval parameters

## 📊 Visualization Guide

### Agent Graph (`/how-it-works`)

Shows the LangGraph state machine as a force-directed graph:
- 🔵 Blue = Active node
- 🟢 Green = Complete
- ⚪ Gray = Pending
- 🔴 Red = Error

### Embedding Explorer

Visualizes the semantic space:
- Each dot is a knowledge chunk
- Query appears and animates to its position
- Lines connect to retrieved chunks
- Brighter = higher similarity

## 🔧 API Reference

### REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check with dependency status |
| POST | `/chat` | Non-streaming chat (rate limited) |
| GET | `/graph/structure` | Agent graph for D3.js |
| GET | `/embeddings/knowledge` | All 2D-projected points |

### WebSocket

Connect to `/ws/{session_id}` for real-time streaming.

**Events received:**
- `connected` - Connection established
- `node_enter` - Agent entering a node
- `node_complete` - Node finished processing
- `rag_results` - Retrieval results with projections
- `token` - Streaming response token
- `complete` - Processing finished

## 💰 Cost Optimization

| Component | Cost | Notes |
|-----------|------|-------|
| OpenAI GPT-4o-mini | ~$0.001/request | Very cheap |
| OpenAI Embeddings | One-time | Generated at build |
| Upstash Redis | Free tier | 10k commands/day |
| Vercel | Free tier | Hobby plan |
| Railway | $5/month | Or free tier |

**Total: $5-15/month** for a production deployment.

## 🧪 Testing

```bash
# Backend tests
pytest packages/agent-core/tests -v
pytest packages/server/tests -v

# Frontend
cd packages/web && npm run lint && npm run type-check
```

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- [LangGraph](https://github.com/langchain-ai/langgraph) for the agent framework
- [D3.js](https://d3js.org/) for beautiful visualizations
- [Anthropic Claude](https://anthropic.com) for helping build this

---

Built with ❤️ by Roshan Shetty
