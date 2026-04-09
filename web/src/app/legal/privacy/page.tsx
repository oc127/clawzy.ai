"use client";

import Link from "next/link";
import { useLanguage } from "@/context/language-context";

export default function PrivacyPage() {
  const { locale } = useLanguage();
  const isJa = locale === "ja";

  return (
    <div className="min-h-screen bg-white">
      <header className="border-b border-[#ebebeb]">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-6 py-4">
          <Link href="/" className="flex items-center gap-2">
            <span className="text-xl">🦞</span>
            <span className="text-lg font-extrabold">
              <span className="text-[#ff385c]">Nippon</span>Claw
            </span>
          </Link>
          <div className="flex gap-4 text-sm text-[#717171]">
            <Link href="/legal/terms" className="hover:text-[#222]">
              {isJa ? "利用規約" : "Terms"}
            </Link>
            <Link href="/legal/tokushoho" className="hover:text-[#222]">
              {isJa ? "特商法表示" : "Commercial Disclosure"}
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-6 py-12">
        {isJa ? <PrivacyJa /> : <PrivacyEn />}
      </main>
    </div>
  );
}

function PrivacyJa() {
  return (
    <article className="prose prose-gray max-w-none">
      <h1>プライバシーポリシー</h1>
      <p className="text-sm text-[#717171]">最終更新日：2026年4月9日</p>

      <h2>1. はじめに</h2>
      <p>
        NipponClaw（以下「当社」）は、ユーザーのプライバシーを重視し、個人情報の保護に関する法律（個人情報保護法 / APPI）を遵守します。本プライバシーポリシーは、当社が収集、使用、保護する情報について説明します。
      </p>

      <h2>2. 収集する情報</h2>
      <h3>2.1 アカウント情報</h3>
      <ul>
        <li>氏名</li>
        <li>メールアドレス</li>
        <li>パスワード（ハッシュ化して保存）</li>
      </ul>

      <h3>2.2 利用データ</h3>
      <ul>
        <li>AIエージェントとの会話内容</li>
        <li>クレジット使用履歴</li>
        <li>アクセスログ（IPアドレス、ブラウザ情報）</li>
      </ul>

      <h3>2.3 決済情報</h3>
      <p>
        決済処理はStripe, Inc.が行います。当社はクレジットカード番号を直接保存しません。
      </p>

      <h2>3. 情報の利用目的</h2>
      <ul>
        <li>サービスの提供・改善</li>
        <li>アカウント管理・認証</li>
        <li>クレジット使用量の計算・請求</li>
        <li>カスタマーサポート</li>
        <li>サービスに関する重要な通知</li>
      </ul>

      <h2>4. AIモデル提供元へのデータ送信</h2>
      <p>
        本サービスでは、ユーザーのメッセージを以下のAIモデル提供元に送信して処理します：
      </p>
      <ul>
        <li><strong>DeepSeek</strong>（DeepSeek AI, 中国）</li>
        <li><strong>Qwen / 通義千問</strong>（Alibaba Cloud, 中国）</li>
        <li><strong>Claude</strong>（Anthropic, 米国）</li>
        <li><strong>GPT-4</strong>（OpenAI, 米国）</li>
        <li><strong>Gemini</strong>（Google, 米国）</li>
      </ul>
      <p>
        各提供元のプライバシーポリシーが追加的に適用されます。ユーザーは、モデル選択時にデータの送信先を確認できます。
      </p>

      <h2>5. データの保存場所</h2>
      <p>
        ユーザーデータは当社のサーバーに保存されます。会話データはAIモデル処理後、当社サーバーにのみ保持され、モデル提供元には保存されません（各提供元のAPIポリシーに準拠）。
      </p>

      <h2>6. データの共有</h2>
      <p>当社は、以下の場合を除き、個人情報を第三者に提供しません：</p>
      <ul>
        <li>ユーザーの同意がある場合</li>
        <li>法令に基づく開示要求がある場合</li>
        <li>サービス提供に必要な業務委託先（Stripe等）への提供</li>
      </ul>

      <h2>7. データの保護</h2>
      <ul>
        <li>通信の暗号化（TLS/SSL）</li>
        <li>パスワードのbcryptハッシュ化</li>
        <li>JWTトークンによる認証</li>
        <li>コンテナ化によるエージェント間の分離</li>
      </ul>

      <h2>8. ユーザーの権利</h2>
      <p>ユーザーは以下の権利を有します：</p>
      <ul>
        <li><strong>アクセス権</strong>：保有する個人データの開示を請求する権利</li>
        <li><strong>訂正権</strong>：不正確な個人データの訂正を請求する権利</li>
        <li><strong>削除権</strong>：個人データの削除を請求する権利</li>
        <li><strong>利用停止権</strong>：個人データの利用停止を請求する権利</li>
      </ul>
      <p>
        これらの権利行使については、support@nipponclaw.com までご連絡ください。
      </p>

      <h2>9. Cookie</h2>
      <p>
        当社は、認証トークンの保存およびサービス改善のためにCookieを使用します。ブラウザの設定でCookieを無効化できますが、一部機能が制限される場合があります。
      </p>

      <h2>10. 未成年者</h2>
      <p>
        本サービスは16歳未満のユーザーを対象としていません。16歳未満の方がアカウントを作成したことが判明した場合、当該アカウントを削除します。
      </p>

      <h2>11. ポリシーの変更</h2>
      <p>
        本ポリシーは随時更新される場合があります。重要な変更については、メールまたはサービス内通知でお知らせします。
      </p>

      <h2>12. お問い合わせ</h2>
      <p>
        プライバシーに関するご質問・ご要望は、以下までご連絡ください。
      </p>
      <p>
        NipponClaw プライバシー担当<br />
        メール：support@nipponclaw.com
      </p>
    </article>
  );
}

function PrivacyEn() {
  return (
    <article className="prose prose-gray max-w-none">
      <h1>Privacy Policy</h1>
      <p className="text-sm text-[#717171]">Last updated: April 9, 2026</p>

      <h2>1. Introduction</h2>
      <p>
        NipponClaw (&quot;we&quot;, &quot;us&quot;) is committed to protecting your privacy and complying with Japan&apos;s Act on the Protection of Personal Information (APPI). This Privacy Policy explains how we collect, use, and protect your information.
      </p>

      <h2>2. Information We Collect</h2>
      <h3>2.1 Account Information</h3>
      <ul>
        <li>Name</li>
        <li>Email address</li>
        <li>Password (stored as a bcrypt hash)</li>
      </ul>

      <h3>2.2 Usage Data</h3>
      <ul>
        <li>Conversations with AI agents</li>
        <li>Credit usage history</li>
        <li>Access logs (IP address, browser information)</li>
      </ul>

      <h3>2.3 Payment Information</h3>
      <p>
        Payment processing is handled by Stripe, Inc. We do not directly store credit card numbers.
      </p>

      <h2>3. How We Use Your Information</h2>
      <ul>
        <li>Providing and improving the Service</li>
        <li>Account management and authentication</li>
        <li>Calculating credit usage and billing</li>
        <li>Customer support</li>
        <li>Important service notifications</li>
      </ul>

      <h2>4. Data Sent to AI Model Providers</h2>
      <p>
        When you chat with an AI agent, your messages are sent to the following AI model providers for processing:
      </p>
      <ul>
        <li><strong>DeepSeek</strong> (DeepSeek AI, China)</li>
        <li><strong>Qwen</strong> (Alibaba Cloud, China)</li>
        <li><strong>Claude</strong> (Anthropic, USA)</li>
        <li><strong>GPT-4</strong> (OpenAI, USA)</li>
        <li><strong>Gemini</strong> (Google, USA)</li>
      </ul>
      <p>
        Each provider&apos;s privacy policy additionally applies. You can see which model processes your data at the time of model selection.
      </p>

      <h2>5. Data Storage</h2>
      <p>
        Your data is stored on our servers. Conversation data is retained only on our servers after AI processing and is not stored by model providers (subject to each provider&apos;s API policies).
      </p>

      <h2>6. Data Sharing</h2>
      <p>We do not share personal information with third parties except:</p>
      <ul>
        <li>With your consent</li>
        <li>When required by law</li>
        <li>With service providers necessary for operation (e.g., Stripe)</li>
      </ul>

      <h2>7. Data Security</h2>
      <ul>
        <li>TLS/SSL encrypted communications</li>
        <li>bcrypt password hashing</li>
        <li>JWT token authentication</li>
        <li>Container isolation between agents</li>
      </ul>

      <h2>8. Your Rights</h2>
      <p>Under APPI, you have the right to:</p>
      <ul>
        <li><strong>Access</strong>: Request disclosure of your personal data</li>
        <li><strong>Correction</strong>: Request correction of inaccurate data</li>
        <li><strong>Deletion</strong>: Request deletion of your data</li>
        <li><strong>Cessation</strong>: Request cessation of data processing</li>
      </ul>
      <p>To exercise these rights, contact support@nipponclaw.com.</p>

      <h2>9. Cookies</h2>
      <p>
        We use cookies for authentication tokens and service improvement. You may disable cookies in your browser settings, but some features may be limited.
      </p>

      <h2>10. Children</h2>
      <p>
        The Service is not intended for users under 16. If we learn that a user under 16 has created an account, we will delete it.
      </p>

      <h2>11. Policy Changes</h2>
      <p>
        This policy may be updated periodically. Significant changes will be communicated via email or in-app notification.
      </p>

      <h2>12. Contact</h2>
      <p>
        For privacy inquiries, contact:<br />
        NipponClaw Privacy Team<br />
        Email: support@nipponclaw.com
      </p>
    </article>
  );
}
