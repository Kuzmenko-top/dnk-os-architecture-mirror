import React from 'react';
import WhiteboardEditor from '@/components/whiteboard/WhiteboardEditor';

export const metadata = {
  title: 'DNK OS | Whiteboard & Moodboard',
  description: 'SOTA Infinite Freehand Canvas & Multi-Agent Design Auditor assimilating tldraw.',
};

export default function WhiteboardPage() {
  return (
    <main className="w-screen h-screen flex flex-col bg-slate-950 overflow-hidden">
      <WhiteboardEditor />
    </main>
  );
}
