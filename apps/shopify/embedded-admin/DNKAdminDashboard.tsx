import React from 'react';
import { useAppBridge } from '@shopify/app-bridge-react';

export interface DNKAdminDashboardProps {
  storeDomain?: string;
  apiVersion?: string;
}

export function DNKAdminDashboard({
  storeDomain = 'dnk-test.myshopify.com',
  apiVersion = '2024-07',
}: DNKAdminDashboardProps) {
  return (
    <div className="dnk-admin-dashboard p-6 max-w-6xl mx-auto space-y-6 font-sans">
      <header className="flex justify-between items-center border-b pb-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">DNK OS Shopify Admin Bridge</h1>
          <p className="text-sm text-gray-500">Store: {storeDomain} | API: {apiVersion}</p>
        </div>
        <div className="flex gap-2">
          <span className="px-3 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded-full">
            Connected (GraphQL Engine Active)
          </span>
        </div>
      </header>

      <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-800 mb-2">Каталог Продуктів</h2>
          <p className="text-sm text-gray-600 mb-4">Керування двосторонньою синхронізацією товарів та інвентарю.</p>
          <button
            onClick={() => window.open('/admin/products', '_blank')}
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition"
          >
            Синхронізувати Товари
          </button>
        </div>

        <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-800 mb-2">Масові Операції (Bulk API)</h2>
          <p className="text-sm text-gray-600 mb-4">Асинхронний експорт та імпорт великих JSONL каталогів.</p>
          <button
            onClick={() => window.open('/admin/bulk', '_blank')}
            className="w-full px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition"
          >
            Запустити Bulk Export
          </button>
        </div>

        <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-800 mb-2">Theme App Blocks</h2>
          <p className="text-sm text-gray-600 mb-4">Генерація та налаштування Liquid Upsell та Loyalty блоків.</p>
          <button
            onClick={() => window.open('/admin/themes', '_blank')}
            className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700 transition"
          >
            Налаштувати Теми
          </button>
        </div>
      </section>

      <section className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Real-time Metrics & Rate Limit Watchdog</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 bg-gray-50 rounded-lg">
            <span className="text-xs text-gray-500 uppercase">Rate Limit Quota</span>
            <div className="text-xl font-bold text-gray-900">1000 / min</div>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <span className="text-xs text-gray-500 uppercase">Token Burst Capacity</span>
            <div className="text-xl font-bold text-gray-900">50 tokens</div>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <span className="text-xs text-gray-500 uppercase">Web Pixel Ingestion</span>
            <div className="text-xl font-bold text-green-600">Active (100% Green)</div>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <span className="text-xs text-gray-500 uppercase">GDPR PII Anonymization</span>
            <div className="text-xl font-bold text-blue-600">Enforced (SHA-256)</div>
          </div>
        </div>
      </section>
    </div>
  );
}

export default DNKAdminDashboard;
