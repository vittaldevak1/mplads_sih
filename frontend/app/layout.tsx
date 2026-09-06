import type { Metadata } from 'next';
import './globals.css';
import Navbar from '@/components/Navbar';

export const metadata: Metadata = {
  title: 'MPLADS Intelligence Platform',
  description: 'AI-powered anomaly detection and inspection prioritization for MPLADS',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased selection:bg-amber-500/20 selection:text-amber-200">
        <Navbar />
        {children}
      </body>
    </html>
  );
}
