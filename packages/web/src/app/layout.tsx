import type { Metadata } from 'next'
import { Inter, JetBrains_Mono } from 'next/font/google'
import './globals.css'

const inter = Inter({ 
  subsets: ['latin'],
  variable: '--font-sans',
})

const jetbrainsMono = JetBrains_Mono({ 
  subsets: ['latin'],
  variable: '--font-mono',
})

export const metadata: Metadata = {
  title: 'SparkyAI | Roshan Shetty',
  description: 'AI-powered interactive portfolio. Chat with an AI that knows everything about my professional background.',
  keywords: ['AI', 'portfolio', 'full-stack developer', 'React', 'D3.js', 'LangGraph'],
  authors: [{ name: 'Roshan Shetty' }],
  openGraph: {
    title: 'SparkyAI | Roshan Shetty',
    description: 'Chat with an AI that knows my professional background',
    type: 'website',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="font-sans">
        {children}
      </body>
    </html>
  )
}
