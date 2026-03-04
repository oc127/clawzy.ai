"use client";

import { useEffect, useState } from "react";
import { getCredits, getPlans, type CreditsInfo } from "@/lib/api";

interface Plan {
  id: string;
  name: string;
  price_monthly: number;
  credits_included: number;
  max_agents: number;
}

// 用户友好的套餐名称
const PLAN_NAMES: Record<string, string> = {
  free: "🦐 小虾米",
  starter: "🦞 小龙虾",
  pro: "🦞 大龙虾",
  business: "🦞 超级龙虾",
};

export default function BillingPage() {
  const [credits, setCredits] = useState<CreditsInfo | null>(null);
  const [plans, setPlans] = useState<Plan[]>([]);

  useEffect(() => {
    getCredits().then(setCredits);
    getPlans().then(setPlans);
  }, []);

  return (
    <div className="p-8 max-w-4xl">
      <h1 className="text-2xl font-bold text-white mb-8">能量 & 套餐</h1>

      {/* 能量余额 */}
      {credits && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 mb-8">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">当前能量</p>
              <p className="text-4xl font-bold text-white mt-1">
                ⚡ {credits.balance}
              </p>
            </div>
            <div className="text-right">
              <p className="text-gray-500 text-sm">本月已用</p>
              <p className="text-2xl font-semibold text-gray-300 mt-1">
                {credits.used_this_period}
              </p>
            </div>
          </div>
          <div className="mt-4 pt-4 border-t border-gray-800">
            <p className="text-sm text-gray-500">
              当前套餐: <span className="text-white font-medium">{PLAN_NAMES[credits.plan] || credits.plan}</span>
            </p>
          </div>
        </div>
      )}

      {/* 套餐列表 */}
      <h2 className="text-lg font-semibold text-white mb-4">选择套餐</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {plans.map((plan) => (
          <div
            key={plan.id}
            className={`bg-gray-900 border rounded-xl p-6 ${
              credits?.plan === plan.id
                ? "border-blue-500"
                : "border-gray-800"
            }`}
          >
            <h3 className="text-lg font-bold text-white">
              {PLAN_NAMES[plan.id] || plan.name}
            </h3>
            <p className="text-3xl font-bold text-white mt-2">
              ${plan.price_monthly}
              <span className="text-sm text-gray-500 font-normal">/月</span>
            </p>
            <ul className="mt-4 space-y-2 text-sm text-gray-400">
              <li>⚡ {plan.credits_included.toLocaleString()} 能量/月</li>
              <li>🦞 最多 {plan.max_agents} 只龙虾</li>
            </ul>
            {credits?.plan === plan.id ? (
              <div className="mt-4 py-2 text-center text-sm text-blue-400 border border-blue-500 rounded-lg">
                当前套餐
              </div>
            ) : (
              <button className="mt-4 w-full py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg transition">
                {plan.price_monthly === 0 ? "当前" : "升级"}
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
