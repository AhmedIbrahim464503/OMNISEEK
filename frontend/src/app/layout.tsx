import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import Providers from './providers';
import Navigation from '@/components/Navigation';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'OMNISEEK | Multi-Modal Semantic Search Engine',
  description: 'Enterprise-grade AI Embedding & Temporal Search System.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full">
      <body className={`${inter.className} h-full overflow-hidden bg-background text-foreground`}>
        <Providers>
          <div className="flex h-screen w-screen overflow-hidden">
            {/* Sidebar Navigation */}
            <Navigation />
            
            {/* Main Application Content */}
            <main className="flex-1 flex flex-col min-w-0 overflow-y-auto bg-background">
              {children}
            </main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
