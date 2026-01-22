# SparkyAI 🤖✨

A production-ready AI agent framework powered by LangGraph and RAG. Build intelligent chatbots that can answer questions about any domain using natural language - whether it's a portfolio assistant, customer support bot, documentation helper, or knowledge base interface.

![SparkyAI Demo](docs/demo.gif)

## ✨ Features

### 🎯 Intelligent Conversational AI
- Natural language Q&A powered by RAG (Retrieval-Augmented Generation)
- Instant, accurate responses from your custom knowledge base
- Handles both specific questions and general inquiries
- Easily adaptable to any domain or use case

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

### Production-Ready Features
- **Real-time WebSocket streaming** for live visualization updates
- **Token-aware conversation management** prevents context overflow
- **Circuit breaker pattern** for resilient OpenAI integration
- **MaximAI quality evaluation** for automated response scoring
- **Cloudflare Turnstile CAPTCHA** for privacy-friendly rate limiting

### Quality & Performance
- **Comprehensive testing** with 130+ tests, 85%+ coverage
- **Locust load testing** validates 100+ concurrent users
- **Type-safe** throughout with TypeScript and Python type hints
- **Custom Langfuse dashboards** for complete observability
- **Performance monitoring** with sub-500ms P50 response time

## 🧪 Testing

### Unit Tests
```bash
# Backend tests
cd packages/agent-core && pytest tests/ -v
cd packages/server && pytest tests/ -v

# Frontend tests
cd packages/web && npm test
```

### E2E Tests
```bash
cd packages/web
npx playwright test
npx playwright test --ui  # With UI
```

### Load Testing
```bash
# Install Locust
pip install locust

# Run load test
locust -f scripts/locustfile.py --host=http://localhost:8000

# Then open http://localhost:8089
```

## 📊 Monitoring & Analytics

### Langfuse Dashboards
SparkyAI includes 5 custom Langfuse dashboards:
- Production Metrics (response times, throughput)
- Response Quality (MaximAI evaluation scores)
- Cost Analysis (token usage, API costs)
- User Behavior (intents, session metrics)
- Error Tracking (failures, circuit breaker)

See [docs/LANGFUSE_DASHBOARDS.md](docs/LANGFUSE_DASHBOARDS.md) for setup.

### Performance Reports
```bash
# Generate performance report
python scripts/performance_report.py --days 7 --output report.html
```

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- [LangGraph](https://github.com/langchain-ai/langgraph) for the agent framework
- [D3.js](https://d3js.org/) for beautiful visualizations
- [Langfuse](https://langfuse.com) for LLM observability
- [Cloudflare](https://cloudflare.com) for Turnstile CAPTCHA

---

Built with ❤️ by Roshan Shetty
