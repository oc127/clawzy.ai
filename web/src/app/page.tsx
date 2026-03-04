import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Nav */}
      <nav className="flex items-center justify-between px-8 py-6 max-w-6xl mx-auto">
        <div className="text-xl font-bold flex items-center gap-2">
          🦞 Clawzy
        </div>
        <div className="flex gap-4">
          <Link
            href="/login"
            className="px-5 py-2 text-sm text-gray-300 hover:text-white transition"
          >
            登录
          </Link>
          <Link
            href="/register"
            className="px-5 py-2 text-sm bg-blue-600 hover:bg-blue-700 rounded-lg font-medium transition"
          >
            免费注册
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <main className="max-w-4xl mx-auto px-8 pt-20 pb-32 text-center">
        <div className="text-7xl mb-6">🦞</div>
        <h1 className="text-5xl font-bold leading-tight mb-6">
          你的 AI 龙虾
          <br />
          <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            下载即用，无需配置
          </span>
        </h1>
        <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-10">
          不用申请 API Key，不用写代码，不用部署服务器。
          注册就能拥有一只 24/7 在线的 AI 龙虾，帮你聊天、写作、做事。
        </p>
        <Link
          href="/register"
          className="inline-block px-8 py-4 bg-blue-600 hover:bg-blue-700 text-lg font-semibold rounded-xl transition"
        >
          免费领一只龙虾 →
        </Link>
        <p className="text-sm text-gray-600 mt-4">注册送 500 能量，无需绑卡</p>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-24 text-left">
          <FeatureCard
            icon="⚡"
            title="90 秒上手"
            desc="注册 → 龙虾自动上线 → 直接开聊。无需任何配置。"
          />
          <FeatureCard
            icon="🧠"
            title="10+ 种大脑"
            desc="从闪电快到超级聪明，按需切换。省能量或要质量，你说了算。"
          />
          <FeatureCard
            icon="🔒"
            title="数据独立"
            desc="每只龙虾都有独立的记忆和工作空间，你的数据只属于你。"
          />
        </div>

        {/* Pricing preview */}
        <div className="mt-24">
          <h2 className="text-3xl font-bold mb-8">简单透明的定价</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <PriceCard
              name="🦐 小虾米"
              price="免费"
              features={["500 能量（一次性）", "1 只龙虾"]}
            />
            <PriceCard
              name="🦞 小龙虾"
              price="$9/月"
              features={["3,000 能量/月", "1 只龙虾", "所有大脑可选"]}
              highlight
            />
            <PriceCard
              name="🦞 大龙虾"
              price="$19/月"
              features={["8,000 能量/月", "3 只龙虾", "优先支持"]}
            />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800 py-8 text-center text-sm text-gray-600">
        Clawzy.ai — OpenClaw as a Service
      </footer>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  desc,
}: {
  icon: string;
  title: string;
  desc: string;
}) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
      <div className="text-3xl mb-3">{icon}</div>
      <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
      <p className="text-sm text-gray-400 leading-relaxed">{desc}</p>
    </div>
  );
}

function PriceCard({
  name,
  price,
  features,
  highlight,
}: {
  name: string;
  price: string;
  features: string[];
  highlight?: boolean;
}) {
  return (
    <div
      className={`rounded-xl p-6 ${
        highlight
          ? "bg-blue-600/10 border-2 border-blue-500"
          : "bg-gray-900 border border-gray-800"
      }`}
    >
      <h3 className="text-lg font-bold text-white">{name}</h3>
      <p className="text-3xl font-bold text-white mt-2">{price}</p>
      <ul className="mt-4 space-y-2">
        {features.map((f) => (
          <li key={f} className="text-sm text-gray-400">
            {f}
          </li>
        ))}
      </ul>
    </div>
  );
}
