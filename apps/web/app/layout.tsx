// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_app_layout"
// purpose: "Root layout for DNK OS Web App with Google Stitch 2.0 Dark Obsidian theme"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "2.0.0"
// updated_at: "2026-08-30"
// --- END DNK-MRH-HEADER ---

import React from 'react';
import type { Metadata } from 'next';
import './globals.css';
import '../styles/shopify-tokens.css';
import CommandBar from '@/components/navigation/CommandBar';

export const metadata: Metadata = {
  title: '🧬 DNK OS (v2.0 Agentic Media & E-Com Operating System)',
  description: '🧬 DNK OS — Official Visual Shell & Agentic Media & E-Com Operating System',
  icons: {
    icon: '/favicon.ico',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark" data-theme="dark">
      <body className="bg-[#0b0d14] text-slate-100 antialiased selection:bg-purple-500 selection:text-white">
        <CommandBar />
        {children}
      </body>
    </html>
  );
}
