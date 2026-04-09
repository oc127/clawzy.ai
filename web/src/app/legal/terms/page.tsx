"use client";

import Link from "next/link";
import { useLanguage } from "@/context/language-context";

export default function TermsPage() {
  const { locale } = useLanguage();
  const isJa = locale === "ja";

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b border-[#ebebeb]">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-6 py-4">
          <Link href="/" className="flex items-center gap-2">
            <span className="text-xl">🦞</span>
            <span className="text-lg font-extrabold">
              <span className="text-[#ff385c]">Nippon</span>Claw
            </span>
          </Link>
          <div className="flex gap-4 text-sm text-[#717171]">
            <Link href="/legal/privacy" className="hover:text-[#222]">
              {isJa ? "プライバシーポリシー" : "Privacy"}
            </Link>
            <Link href="/legal/tokushoho" className="hover:text-[#222]">
              {isJa ? "特商法表示" : "Commercial Disclosure"}
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-6 py-12">
        {isJa ? <TermsJa /> : <TermsEn />}
      </main>
    </div>
  );
}

function TermsJa() {
  return (
    <article className="prose prose-gray max-w-none">
      <h1>利用規約</h1>
      <p className="text-sm text-[#717171]">最終更新日：2026年4月9日</p>

      <h2>第1条（適用）</h2>
      <p>
        本利用規約（以下「本規約」）は、NipponClaw（以下「当社」）が提供するAIエージェントプラットフォームサービス（以下「本サービス」）の利用条件を定めるものです。ユーザーは本規約に同意の上、本サービスを利用するものとします。
      </p>

      <h2>第2条（定義）</h2>
      <ul>
        <li>「ユーザー」とは、本サービスのアカウントを作成し、本規約に同意した個人または法人を指します。</li>
        <li>「AIエージェント」とは、ユーザーが本サービス上で作成・運用するAIアシスタントを指します。</li>
        <li>「クレジット」とは、本サービスの利用量を計測する単位を指します。</li>
      </ul>

      <h2>第3条（アカウント登録）</h2>
      <ol>
        <li>ユーザーは、正確な情報を提供してアカウントを登録する必要があります。</li>
        <li>ユーザーは、自己のアカウントの管理について一切の責任を負うものとします。</li>
        <li>アカウントの譲渡または共有は禁止されます。</li>
      </ol>

      <h2>第4条（サービス内容）</h2>
      <p>当社は以下のサービスを提供します：</p>
      <ul>
        <li>AIエージェントの作成・管理・運用</li>
        <li>複数のAIモデル（DeepSeek、Qwen、Claude、GPT-4等）へのアクセス</li>
        <li>AIエージェントとのチャット機能</li>
        <li>ClawHub スキルマーケットプレイス</li>
      </ul>

      <h2>第5条（料金・クレジット）</h2>
      <ol>
        <li>本サービスは、クレジットベースの従量課金制を採用しています。</li>
        <li>各プランに含まれるクレジット数は、プラン説明ページに記載の通りです。</li>
        <li>クレジットの消費量は、使用するAIモデルおよびトークン数に基づいて計算されます。</li>
        <li>未使用クレジットの翌月繰越はできません。</li>
        <li>返金ポリシーは第10条に定めます。</li>
      </ol>

      <h2>第6条（禁止事項）</h2>
      <p>ユーザーは以下の行為を行ってはなりません：</p>
      <ul>
        <li>法令または公序良俗に違反する行為</li>
        <li>当社または第三者の知的財産権を侵害する行為</li>
        <li>本サービスのインフラに過度な負荷をかける行為</li>
        <li>不正アクセスまたはシステムへの攻撃</li>
        <li>AIを利用した違法コンテンツの生成</li>
        <li>本サービスのリバースエンジニアリング</li>
      </ul>

      <h2>第7条（知的財産権）</h2>
      <ol>
        <li>本サービスに関する知的財産権は当社に帰属します。</li>
        <li>ユーザーが本サービスを通じて生成したコンテンツの権利はユーザーに帰属します。</li>
        <li>ただし、AIモデル提供元の利用規約が適用される場合があります。</li>
      </ol>

      <h2>第8条（免責事項）</h2>
      <ol>
        <li>当社は、AIが生成するコンテンツの正確性・完全性を保証しません。</li>
        <li>当社は、サービスの中断・停止による損害について責任を負いません。</li>
        <li>当社は、ユーザー間のトラブルについて責任を負いません。</li>
      </ol>

      <h2>第9条（サービスの変更・終了）</h2>
      <p>
        当社は、事前に通知した上で、本サービスの内容変更または終了を行うことができます。重要な変更については、30日前までに通知します。
      </p>

      <h2>第10条（返金ポリシー）</h2>
      <ul>
        <li>月額サブスクリプションは、次の請求日前にキャンセル可能です。</li>
        <li>日割り計算による返金は行いません。</li>
        <li>技術的な問題によりサービスを利用できなかった場合、クレジットの補填を検討します。</li>
      </ul>

      <h2>第11条（準拠法・管轄裁判所）</h2>
      <p>
        本規約は日本法に準拠し、解釈されるものとします。本サービスに関する紛争は、東京地方裁判所を第一審の専属的合意管轄裁判所とします。
      </p>

      <h2>第12条（規約の変更）</h2>
      <p>
        当社は、必要に応じて本規約を変更できるものとします。変更後の規約は、本サービス上に掲載した時点で効力を生じます。重要な変更については、メールまたはサービス内通知でお知らせします。
      </p>

      <hr />
      <p className="text-sm text-[#717171]">
        ご質問がある場合は、support@nipponclaw.com までお問い合わせください。
      </p>
    </article>
  );
}

function TermsEn() {
  return (
    <article className="prose prose-gray max-w-none">
      <h1>Terms of Service</h1>
      <p className="text-sm text-[#717171]">Last updated: April 9, 2026</p>

      <h2>1. Acceptance of Terms</h2>
      <p>
        By creating an account or using NipponClaw (the &quot;Service&quot;), you agree to be bound by these Terms of Service. If you do not agree, do not use the Service.
      </p>

      <h2>2. Definitions</h2>
      <ul>
        <li>&quot;User&quot; means any individual or entity that creates an account on the Service.</li>
        <li>&quot;AI Agent&quot; means an AI assistant created and operated by a User on the Service.</li>
        <li>&quot;Credits&quot; means the unit of measurement for Service usage.</li>
      </ul>

      <h2>3. Account Registration</h2>
      <ol>
        <li>You must provide accurate information when creating an account.</li>
        <li>You are responsible for maintaining the security of your account.</li>
        <li>Account sharing or transfer is prohibited.</li>
      </ol>

      <h2>4. Service Description</h2>
      <p>NipponClaw provides:</p>
      <ul>
        <li>AI agent creation, management, and operation</li>
        <li>Access to multiple AI models (DeepSeek, Qwen, Claude, GPT-4, etc.)</li>
        <li>Real-time chat with AI agents</li>
        <li>ClawHub skill marketplace</li>
      </ul>

      <h2>5. Pricing &amp; Credits</h2>
      <ol>
        <li>The Service uses a credit-based pay-as-you-go billing model.</li>
        <li>Credit allocations per plan are as described on the pricing page.</li>
        <li>Credit consumption is calculated based on the AI model used and token count.</li>
        <li>Unused credits do not roll over to the next billing period.</li>
        <li>Refund policy is described in Section 10.</li>
      </ol>

      <h2>6. Prohibited Uses</h2>
      <p>You may not:</p>
      <ul>
        <li>Violate any applicable laws or regulations</li>
        <li>Infringe on intellectual property rights</li>
        <li>Place excessive load on Service infrastructure</li>
        <li>Attempt unauthorized access or system attacks</li>
        <li>Generate illegal content using AI</li>
        <li>Reverse-engineer the Service</li>
      </ul>

      <h2>7. Intellectual Property</h2>
      <ol>
        <li>All intellectual property rights in the Service belong to NipponClaw.</li>
        <li>Content generated by Users through the Service belongs to the User.</li>
        <li>Terms of the underlying AI model providers may also apply.</li>
      </ol>

      <h2>8. Disclaimer</h2>
      <ol>
        <li>We do not guarantee the accuracy or completeness of AI-generated content.</li>
        <li>We are not liable for damages caused by service interruptions.</li>
        <li>We are not responsible for disputes between Users.</li>
      </ol>

      <h2>9. Service Changes &amp; Termination</h2>
      <p>
        We may modify or discontinue the Service with prior notice. Significant changes will be communicated at least 30 days in advance.
      </p>

      <h2>10. Refund Policy</h2>
      <ul>
        <li>Monthly subscriptions may be cancelled before the next billing date.</li>
        <li>No prorated refunds are provided.</li>
        <li>Credit compensation may be considered for technical service failures.</li>
      </ul>

      <h2>11. Governing Law</h2>
      <p>
        These Terms are governed by the laws of Japan. Any disputes shall be subject to the exclusive jurisdiction of the Tokyo District Court.
      </p>

      <h2>12. Changes to Terms</h2>
      <p>
        We may update these Terms as needed. Updated Terms take effect upon posting. Significant changes will be communicated via email or in-app notification.
      </p>

      <hr />
      <p className="text-sm text-[#717171]">
        Questions? Contact us at support@nipponclaw.com.
      </p>
    </article>
  );
}
