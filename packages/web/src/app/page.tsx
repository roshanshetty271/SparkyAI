'use client'

import { useState } from 'react'
import Link from 'next/link'
import { MessageCircle, Sparkles, GitBranch, Eye } from 'lucide-react'
import ChatWidget from '@/components/chat/ChatWidget'

export default function HomePage() {
  const [chatOpen, setChatOpen] = useState(false)

  return (
    <main className="min-h-screen bg-dark-bg">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        {/* Gradient background */}
        <div className="absolute inset-0 bg-gradient-to-br from-accent-purple/10 via-transparent to-accent-cyan/10" />
        
        <div className="relative max-w-6xl mx-auto px-6 py-24">
          {/* Nav */}
          <nav className="flex items-center justify-between mb-20">
            <div className="flex items-center gap-2">
              <Sparkles className="w-6 h-6 text-accent-cyan" />
              <span className="text-xl font-semibold">SparkyAI</span>
            </div>
            
            <div className="flex items-center gap-6">
              <Link 
                href="/how-it-works" 
                className="text-zinc-400 hover:text-white transition-colors"
              >
                How It Works
              </Link>
              <a 
                href="https://github.com/roshanshetty" 
                target="_blank"
                rel="noopener noreferrer"
                className="text-zinc-400 hover:text-white transition-colors"
              >
                GitHub
              </a>
            </div>
          </nav>

          {/* Hero content */}
          <div className="text-center max-w-3xl mx-auto">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-dark-card border border-dark-border mb-8">
              <span className="w-2 h-2 rounded-full bg-accent-green animate-pulse" />
              <span className="text-sm text-zinc-400">AI-Powered Portfolio</span>
            </div>

            <h1 className="text-5xl md:text-6xl font-bold mb-6 leading-tight">
              Don&apos;t read my resume.
              <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-accent-cyan to-accent-purple">
                Talk to it.
              </span>
            </h1>

            <p className="text-xl text-zinc-400 mb-10 max-w-2xl mx-auto">
              I&apos;m Roshan Shetty, a Full-Stack & AI Engineer. Instead of scrolling through 
              a PDF, chat with an AI that knows everything about my skills, projects, and experience.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <button
                onClick={() => setChatOpen(true)}
                className="flex items-center gap-2 px-6 py-3 bg-accent-blue hover:bg-accent-blue/90 
                         text-white font-medium rounded-xl transition-all shadow-lg shadow-accent-blue/20"
              >
                <MessageCircle className="w-5 h-5" />
                Start Chatting
              </button>
              
              <Link
                href="/how-it-works"
                className="flex items-center gap-2 px-6 py-3 bg-dark-card hover:bg-dark-hover
                         border border-dark-border text-white font-medium rounded-xl transition-all"
              >
                <Eye className="w-5 h-5" />
                See How It Works
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 border-t border-dark-border">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-center mb-4">
            More than just a chatbot
          </h2>
          <p className="text-zinc-400 text-center mb-16 max-w-2xl mx-auto">
            Built with production-grade architecture to showcase real engineering skills
          </p>

          <div className="grid md:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="p-6 bg-dark-card border border-dark-border rounded-2xl">
              <div className="w-12 h-12 rounded-xl bg-accent-cyan/10 flex items-center justify-center mb-4">
                <GitBranch className="w-6 h-6 text-accent-cyan" />
              </div>
              <h3 className="text-xl font-semibold mb-2">LangGraph Agents</h3>
              <p className="text-zinc-400">
                Stateful multi-node agent architecture with conditional routing. 
                Watch the AI&apos;s decision process in real-time.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="p-6 bg-dark-card border border-dark-border rounded-2xl">
              <div className="w-12 h-12 rounded-xl bg-accent-purple/10 flex items-center justify-center mb-4">
                <Sparkles className="w-6 h-6 text-accent-purple" />
              </div>
              <h3 className="text-xl font-semibold mb-2">RAG System</h3>
              <p className="text-zinc-400">
                Retrieval-augmented generation with confidence scoring. 
                Explore the embedding space in 2D visualization.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="p-6 bg-dark-card border border-dark-border rounded-2xl">
              <div className="w-12 h-12 rounded-xl bg-accent-green/10 flex items-center justify-center mb-4">
                <Eye className="w-6 h-6 text-accent-green" />
              </div>
              <h3 className="text-xl font-semibold mb-2">D3.js Visualizations</h3>
              <p className="text-zinc-400">
                Real-time force-directed graphs and embedding projections 
                powered by WebSocket streaming.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Tech Stack Section */}
      <section className="py-24 border-t border-dark-border">
        <div className="max-w-6xl mx-auto px-6 text-center">
          <h2 className="text-3xl font-bold mb-4">Built With</h2>
          <p className="text-zinc-400 mb-12">
            The same technologies I use in production
          </p>

          <div className="flex flex-wrap justify-center gap-4">
            {[
              'Next.js 14',
              'TypeScript',
              'Tailwind CSS',
              'D3.js',
              'FastAPI',
              'LangGraph',
              'OpenAI',
              'WebSockets',
              'Upstash Redis',
              'Langfuse',
            ].map((tech) => (
              <span
                key={tech}
                className="px-4 py-2 bg-dark-card border border-dark-border rounded-full text-sm"
              >
                {tech}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 border-t border-dark-border">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-3xl font-bold mb-4">
            Ready to learn more?
          </h2>
          <p className="text-zinc-400 mb-8 max-w-2xl mx-auto">
            Ask me anything about my experience at Aosenuma AI, my projects, 
            or my technical skills. The AI has all the answers.
          </p>
          
          <button
            onClick={() => setChatOpen(true)}
            className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-accent-cyan to-accent-purple
                     text-white font-medium rounded-xl transition-all hover:opacity-90
                     shadow-lg shadow-accent-purple/20"
          >
            <MessageCircle className="w-5 h-5" />
            Chat with SparkyAI
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 border-t border-dark-border">
        <div className="max-w-6xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-zinc-400">
            <Sparkles className="w-4 h-4" />
            <span className="text-sm">SparkyAI by Roshan Shetty</span>
          </div>
          
          <div className="flex items-center gap-6 text-sm text-zinc-400">
            <a href="mailto:roshan@example.com" className="hover:text-white transition-colors">
              Email
            </a>
            <a href="https://linkedin.com/in/roshanshetty" className="hover:text-white transition-colors">
              LinkedIn
            </a>
            <a href="https://github.com/roshanshetty" className="hover:text-white transition-colors">
              GitHub
            </a>
          </div>
        </div>
      </footer>

      {/* Chat Widget */}
      <ChatWidget isOpen={chatOpen} onToggle={() => setChatOpen(!chatOpen)} />
    </main>
  )
}
