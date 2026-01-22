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

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- OpenAI API key

### Installation

```bash
# Clone repository
git clone https://github.com/roshanshetty271/SparkyAI.git
cd sparky-ai

# Install frontend dependencies
cd packages/web && npm install
```

### Configuration

Create a `.env` file with your OpenAI API key:

```bash
OPENAI_API_KEY=your-key-here
```

### Run

```bash
# Start frontend (from packages/web)
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000)

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

## 🎨 Key Highlights

- **Real-time WebSocket streaming** for live visualization updates
- **Token-aware conversation management** prevents context overflow
- **Circuit breaker pattern** for resilient OpenAI integration
- **Comprehensive testing** with 70%+ coverage
- **Type-safe** throughout with TypeScript and Python type hints

## 🧪 Testing

```bash
# Run tests
npm test
```

## 💰 Cost Optimization

| Component | Cost | Notes |
|-----------|------|-------|
| OpenAI GPT-4o-mini | ~$0.001/request | Very cheap |
| OpenAI Embeddings | One-time | Generated at build |
| Upstash Redis | Free tier | 10k commands/day |
| Vercel | Free tier | Hobby plan |

**Total: ~$5-15/month** for a production deployment.

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- [LangGraph](https://github.com/langchain-ai/langgraph) for the agent framework
- [D3.js](https://d3js.org/) for beautiful visualizations
- [Anthropic Claude](https://anthropic.com) for helping build this

---

Built with ❤️ by Roshan Shetty
