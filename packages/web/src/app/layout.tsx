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
  metadataBase: new URL('https://roshan.dev'), // Replace with actual domain
  openGraph: {
    title: 'SparkyAI | Roshan Shetty',
    description: 'Chat with an AI that knows my professional background',
    type: 'website',
    url: 'https://roshan.dev',
    siteName: 'SparkyAI',
    images: [
      {
        url: '/og-image.png', // Ensure this exists in public/ eventually
        width: 1200,
        height: 630,
        alt: 'SparkyAI Portfolio',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'SparkyAI | Roshan Shetty',
    description: 'Chat with an AI that knows my professional background',
    creator: '@roshanshetty', // Replace if exists
  },
  icons: {
    icon: '/favicon.ico',
  },
}

export const viewport = {
  themeColor: '#0a0a0b', // Matches dark mode background
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
