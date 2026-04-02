"""Legal pages: Privacy Policy and Terms of Service for NipponClaw."""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["legal"])

# ---------------------------------------------------------------------------
# Shared CSS
# ---------------------------------------------------------------------------
_CSS = """
<style>
  :root {
    --bg: #fafafa;
    --fg: #1a1a1a;
    --muted: #555;
    --accent: #2563eb;
    --border: #e5e7eb;
    --section-bg: #fff;
  }
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  html { scroll-behavior: smooth; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Hiragino Sans",
                 "Noto Sans JP", sans-serif;
    background: var(--bg);
    color: var(--fg);
    line-height: 1.7;
    padding: 0;
    margin: 0;
  }
  .container {
    max-width: 800px;
    margin: 0 auto;
    padding: 40px 24px 80px;
  }
  header {
    text-align: center;
    padding: 48px 24px 24px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 32px;
  }
  header h1 {
    font-size: 2rem;
    font-weight: 700;
    letter-spacing: -0.02em;
  }
  header p {
    color: var(--muted);
    margin-top: 8px;
    font-size: 0.95rem;
  }
  .lang-toggle {
    display: flex;
    justify-content: center;
    gap: 12px;
    margin: 24px 0 32px;
  }
  .lang-toggle a {
    display: inline-block;
    padding: 8px 20px;
    border: 1px solid var(--border);
    border-radius: 6px;
    text-decoration: none;
    color: var(--fg);
    font-size: 0.9rem;
    transition: background 0.15s;
  }
  .lang-toggle a:hover, .lang-toggle a.active {
    background: var(--accent);
    color: #fff;
    border-color: var(--accent);
  }
  section {
    background: var(--section-bg);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 32px;
    margin-bottom: 24px;
  }
  h2 {
    font-size: 1.35rem;
    font-weight: 600;
    margin-bottom: 16px;
    padding-bottom: 8px;
    border-bottom: 2px solid var(--accent);
    display: inline-block;
  }
  h3 {
    font-size: 1.1rem;
    font-weight: 600;
    margin: 20px 0 8px;
  }
  p, li { font-size: 0.95rem; color: var(--fg); }
  p { margin-bottom: 12px; }
  ul { padding-left: 20px; margin-bottom: 12px; }
  li { margin-bottom: 6px; }
  .date { color: var(--muted); font-size: 0.85rem; }
  footer {
    text-align: center;
    padding: 32px 24px;
    color: var(--muted);
    font-size: 0.85rem;
    border-top: 1px solid var(--border);
  }
  footer a { color: var(--accent); text-decoration: none; }
  @media (max-width: 600px) {
    .container { padding: 24px 16px 60px; }
    section { padding: 20px 16px; }
    header h1 { font-size: 1.5rem; }
  }
</style>
"""


# ---------------------------------------------------------------------------
# Privacy Policy
# ---------------------------------------------------------------------------
_PRIVACY_HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Privacy Policy - NipponClaw</title>
  {_CSS}
</head>
<body>

<header>
  <h1>Privacy Policy / プライバシーポリシー</h1>
  <p>NipponClaw (nipponclaw.com)</p>
</header>

<div class="container">

<div class="lang-toggle">
  <a href="#english" class="active">English</a>
  <a href="#japanese">日本語</a>
</div>

<!-- ==================== ENGLISH ==================== -->
<div id="english">

<section>
  <h2>1. Introduction</h2>
  <p>NipponClaw ("we", "us", "our") operates the NipponClaw platform, including the website at nipponclaw.com, the NipponClaw iOS application, and related services (collectively, the "Service"). This Privacy Policy explains how we collect, use, disclose, and protect your personal information in compliance with the Act on the Protection of Personal Information of Japan (APPI) and applicable international privacy regulations.</p>
  <p class="date">Last updated: April 2, 2026</p>
</section>

<section>
  <h2>2. Information We Collect</h2>
  <h3>2.1 Account Information</h3>
  <ul>
    <li>Email address</li>
    <li>Display name</li>
    <li>Password (stored as a salted cryptographic hash; we never store plaintext passwords)</li>
  </ul>
  <h3>2.2 Usage Data</h3>
  <ul>
    <li>Chat messages and conversation history with AI agents</li>
    <li>Agent configurations and custom settings</li>
    <li>Workspace and memory data you create</li>
    <li>Credit purchase and usage history</li>
  </ul>
  <h3>2.3 Technical Data</h3>
  <ul>
    <li>IP address and approximate location</li>
    <li>Device type, operating system, and browser information</li>
    <li>App usage analytics and error logs</li>
  </ul>
  <h3>2.4 Payment Information</h3>
  <p>Payment processing is handled by Stripe and Apple (for in-app purchases). We do not store your credit card numbers or payment method details on our servers. Stripe and Apple process payments in accordance with their own privacy policies.</p>
</section>

<section>
  <h2>3. How We Use Your Information</h2>
  <ul>
    <li>Provide and operate the Service, including AI-powered conversations</li>
    <li>Process your messages through third-party LLM providers to generate responses</li>
    <li>Manage your account, credits, and subscription</li>
    <li>Send service-related notifications</li>
    <li>Improve and develop the Service</li>
    <li>Detect and prevent fraud or abuse</li>
    <li>Comply with legal obligations</li>
  </ul>
</section>

<section>
  <h2>4. Third-Party Services</h2>
  <p>We share data with the following categories of third-party service providers as necessary to operate the Service:</p>
  <h3>4.1 LLM / AI Providers</h3>
  <p>Your chat messages are sent to third-party large language model (LLM) providers (including but not limited to DeepSeek, Qwen / Alibaba Cloud, and other AI model providers) for processing. These providers process message content to generate AI responses. We send only the content necessary to generate responses and do not share your account information with these providers.</p>
  <h3>4.2 Payment Processors</h3>
  <ul>
    <li><strong>Stripe</strong> - processes credit/debit card payments and manages billing</li>
    <li><strong>Apple</strong> - processes in-app purchases through the App Store</li>
  </ul>
  <h3>4.3 Messaging Channel Integrations</h3>
  <p>If you connect your account to Telegram or LINE, messages sent through those channels are processed by the respective platform APIs in addition to our Service.</p>
  <h3>4.4 Infrastructure</h3>
  <p>Our servers and data are hosted on Alibaba Cloud infrastructure located in Japan.</p>
</section>

<section>
  <h2>5. Data Storage and Security</h2>
  <p>Your data is stored on servers located in Japan (Alibaba Cloud Japan region). We implement industry-standard security measures including:</p>
  <ul>
    <li>Encryption in transit (TLS/HTTPS)</li>
    <li>Encryption at rest for sensitive data</li>
    <li>Salted password hashing (bcrypt)</li>
    <li>Rate limiting and access controls</li>
    <li>Regular security reviews</li>
  </ul>
</section>

<section>
  <h2>6. Data Retention</h2>
  <ul>
    <li><strong>Account data</strong> - retained for the duration of your account, deleted within 30 days of account deletion</li>
    <li><strong>Chat history</strong> - retained for the duration of your account unless you delete individual conversations</li>
    <li><strong>Payment records</strong> - retained as required by applicable tax and commercial laws (typically 7 years)</li>
    <li><strong>Server logs</strong> - automatically purged after 90 days</li>
  </ul>
</section>

<section>
  <h2>7. Your Rights</h2>
  <p>Under the APPI and other applicable laws, you have the right to:</p>
  <ul>
    <li><strong>Access</strong> - request a copy of your personal data</li>
    <li><strong>Correction</strong> - request correction of inaccurate data</li>
    <li><strong>Deletion</strong> - request deletion of your personal data</li>
    <li><strong>Export</strong> - request your data in a portable format</li>
    <li><strong>Withdrawal</strong> - withdraw consent for data processing</li>
    <li><strong>Restriction</strong> - request restriction of processing</li>
  </ul>
  <p>To exercise any of these rights, contact us at the address below. We will respond within 30 days.</p>
</section>

<section>
  <h2>8. Children's Privacy</h2>
  <p>The Service is not intended for children under the age of 16. We do not knowingly collect personal information from children. If we learn we have collected data from a child under 16, we will delete it promptly.</p>
</section>

<section>
  <h2>9. Changes to This Policy</h2>
  <p>We may update this Privacy Policy from time to time. We will notify you of significant changes by posting a notice in the app or sending an email to your registered address. Continued use of the Service after changes constitutes acceptance of the updated policy.</p>
</section>

<section>
  <h2>10. Contact Us</h2>
  <p>For privacy-related inquiries, data requests, or complaints:</p>
  <ul>
    <li>Email: <strong>privacy@nipponclaw.com</strong></li>
    <li>Website: <strong>https://nipponclaw.com</strong></li>
  </ul>
</section>

</div>

<!-- ==================== JAPANESE ==================== -->
<div id="japanese">

<section>
  <h2>1. はじめに</h2>
  <p>NipponClaw（以下「当社」）は、nipponclaw.com ウェブサイト、NipponClaw iOSアプリケーション、および関連サービス（以下総称して「本サービス」）を運営しています。本プライバシーポリシーは、個人情報の保護に関する法律（個人情報保護法・APPI）および適用される国際的なプライバシー規制に準拠し、お客様の個人情報の収集、利用、開示、保護について説明するものです。</p>
  <p class="date">最終更新日：2026年4月2日</p>
</section>

<section>
  <h2>2. 収集する情報</h2>
  <h3>2.1 アカウント情報</h3>
  <ul>
    <li>メールアドレス</li>
    <li>表示名</li>
    <li>パスワード（ソルト付き暗号化ハッシュとして保存。平文のパスワードは一切保存しません）</li>
  </ul>
  <h3>2.2 利用データ</h3>
  <ul>
    <li>AIエージェントとのチャットメッセージおよび会話履歴</li>
    <li>エージェントの設定およびカスタム設定</li>
    <li>ワークスペースおよびメモリデータ</li>
    <li>クレジット購入・利用履歴</li>
  </ul>
  <h3>2.3 技術データ</h3>
  <ul>
    <li>IPアドレスおよびおおよその位置情報</li>
    <li>デバイスの種類、オペレーティングシステム、ブラウザ情報</li>
    <li>アプリの利用分析およびエラーログ</li>
  </ul>
  <h3>2.4 決済情報</h3>
  <p>決済処理はStripeおよびApple（アプリ内課金）が行います。クレジットカード番号や決済方法の詳細は当社のサーバーに保存されません。StripeおよびAppleはそれぞれのプライバシーポリシーに従って決済を処理します。</p>
</section>

<section>
  <h2>3. 情報の利用目的</h2>
  <ul>
    <li>AI会話機能を含む本サービスの提供および運営</li>
    <li>AI応答を生成するための第三者LLMプロバイダーへのメッセージ処理</li>
    <li>アカウント、クレジット、サブスクリプションの管理</li>
    <li>サービス関連の通知の送信</li>
    <li>本サービスの改善および開発</li>
    <li>不正利用の検出および防止</li>
    <li>法的義務の遵守</li>
  </ul>
</section>

<section>
  <h2>4. 第三者サービス</h2>
  <p>本サービスの運営に必要な範囲で、以下のカテゴリの第三者サービスプロバイダーとデータを共有します。</p>
  <h3>4.1 LLM / AIプロバイダー</h3>
  <p>チャットメッセージは、AI応答を生成するために第三者の大規模言語モデル（LLM）プロバイダー（DeepSeek、Qwen / Alibaba Cloud等を含みますがこれらに限定されません）に送信されます。応答の生成に必要なコンテンツのみを送信し、アカウント情報はこれらのプロバイダーと共有しません。</p>
  <h3>4.2 決済処理業者</h3>
  <ul>
    <li><strong>Stripe</strong> - クレジットカード/デビットカード決済の処理および請求管理</li>
    <li><strong>Apple</strong> - App Store経由のアプリ内課金の処理</li>
  </ul>
  <h3>4.3 メッセージングチャネル連携</h3>
  <p>TelegramまたはLINEとアカウントを連携した場合、それらのチャネルを通じて送信されたメッセージは、当社のサービスに加えて各プラットフォームのAPIによって処理されます。</p>
  <h3>4.4 インフラストラクチャ</h3>
  <p>当社のサーバーおよびデータは、日本国内のAlibaba Cloudインフラストラクチャでホストされています。</p>
</section>

<section>
  <h2>5. データの保存とセキュリティ</h2>
  <p>お客様のデータは日本国内のサーバー（Alibaba Cloud日本リージョン）に保存されます。以下の業界標準のセキュリティ対策を実施しています。</p>
  <ul>
    <li>通信時の暗号化（TLS/HTTPS）</li>
    <li>機密データの保存時暗号化</li>
    <li>ソルト付きパスワードハッシュ（bcrypt）</li>
    <li>レート制限およびアクセス制御</li>
    <li>定期的なセキュリティレビュー</li>
  </ul>
</section>

<section>
  <h2>6. データ保持期間</h2>
  <ul>
    <li><strong>アカウントデータ</strong> - アカウントの有効期間中保持し、アカウント削除後30日以内に削除</li>
    <li><strong>チャット履歴</strong> - 個別の会話を削除しない限り、アカウントの有効期間中保持</li>
    <li><strong>決済記録</strong> - 適用される税法および商法の要件に従い保持（通常7年間）</li>
    <li><strong>サーバーログ</strong> - 90日後に自動削除</li>
  </ul>
</section>

<section>
  <h2>7. お客様の権利</h2>
  <p>個人情報保護法およびその他の適用法に基づき、お客様には以下の権利があります。</p>
  <ul>
    <li><strong>アクセス権</strong> - 個人データのコピーを請求する権利</li>
    <li><strong>訂正権</strong> - 不正確なデータの訂正を請求する権利</li>
    <li><strong>削除権</strong> - 個人データの削除を請求する権利</li>
    <li><strong>エクスポート権</strong> - ポータブルな形式でデータを請求する権利</li>
    <li><strong>同意撤回権</strong> - データ処理に対する同意を撤回する権利</li>
    <li><strong>制限権</strong> - 処理の制限を請求する権利</li>
  </ul>
  <p>これらの権利を行使するには、下記の連絡先までお問い合わせください。30日以内に対応いたします。</p>
</section>

<section>
  <h2>8. 未成年者のプライバシー</h2>
  <p>本サービスは16歳未満の方を対象としていません。16歳未満の方の個人情報を故意に収集することはありません。16歳未満の方のデータを収集したことが判明した場合、速やかに削除します。</p>
</section>

<section>
  <h2>9. ポリシーの変更</h2>
  <p>本プライバシーポリシーは随時更新される場合があります。重要な変更がある場合は、アプリ内の通知または登録されたメールアドレスへの送信によりお知らせします。変更後の本サービスの継続利用は、更新されたポリシーへの同意とみなされます。</p>
</section>

<section>
  <h2>10. お問い合わせ</h2>
  <p>プライバシーに関するお問い合わせ、データ請求、または苦情については下記までご連絡ください。</p>
  <ul>
    <li>メール：<strong>privacy@nipponclaw.com</strong></li>
    <li>ウェブサイト：<strong>https://nipponclaw.com</strong></li>
  </ul>
</section>

</div>

</div>

<footer>
  &copy; 2026 NipponClaw. All rights reserved. |
  <a href="/terms">Terms of Service</a> |
  <a href="/privacy">Privacy Policy</a>
</footer>

</body>
</html>
"""


# ---------------------------------------------------------------------------
# Terms of Service
# ---------------------------------------------------------------------------
_TERMS_HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Terms of Service - NipponClaw</title>
  {_CSS}
</head>
<body>

<header>
  <h1>Terms of Service / 利用規約</h1>
  <p>NipponClaw (nipponclaw.com)</p>
</header>

<div class="container">

<div class="lang-toggle">
  <a href="#english" class="active">English</a>
  <a href="#japanese">日本語</a>
</div>

<!-- ==================== ENGLISH ==================== -->
<div id="english">

<section>
  <h2>1. Acceptance of Terms</h2>
  <p>By accessing or using the NipponClaw platform (the "Service"), including the website at nipponclaw.com, the NipponClaw iOS application, and any associated APIs, you agree to be bound by these Terms of Service ("Terms"). If you do not agree to these Terms, do not use the Service.</p>
  <p class="date">Last updated: April 2, 2026</p>
</section>

<section>
  <h2>2. Service Description</h2>
  <p>NipponClaw is an AI assistant platform that allows users to:</p>
  <ul>
    <li>Create and configure AI agents powered by large language models</li>
    <li>Engage in conversations with AI agents</li>
    <li>Install plugins and tools from the ClawHub marketplace</li>
    <li>Connect messaging channels (Telegram, LINE) to AI agents</li>
    <li>Schedule automated agent tasks</li>
  </ul>
  <p>The Service uses third-party AI models (including but not limited to DeepSeek, Qwen, and other providers) to generate responses.</p>
</section>

<section>
  <h2>3. Account Registration</h2>
  <ul>
    <li>You must provide accurate and complete registration information</li>
    <li>You are responsible for maintaining the security of your account credentials</li>
    <li>You must be at least 16 years old to create an account</li>
    <li>One person may not maintain multiple accounts</li>
    <li>You are responsible for all activity that occurs under your account</li>
  </ul>
</section>

<section>
  <h2>4. Credits and Billing</h2>
  <h3>4.1 Credit System</h3>
  <p>The Service operates on a credit-based system. Credits are consumed when you use AI features, including sending messages to agents and using tools. Different models and features may consume different amounts of credits.</p>
  <h3>4.2 Purchases</h3>
  <ul>
    <li>Credits can be purchased through the website (via Stripe) or the iOS app (via Apple In-App Purchases)</li>
    <li>All purchases are final and non-refundable, except as required by applicable law or as described in Apple's or Stripe's refund policies</li>
    <li>Prices are displayed in the applicable currency at the time of purchase and include any applicable taxes</li>
  </ul>
  <h3>4.3 Free Credits</h3>
  <p>We may offer free credits for new accounts or promotions. Free credits may expire and cannot be transferred or exchanged for cash.</p>
</section>

<section>
  <h2>5. Acceptable Use</h2>
  <p>You agree not to use the Service to:</p>
  <ul>
    <li>Generate content that is illegal, harmful, threatening, abusive, or harassing</li>
    <li>Violate any applicable laws or regulations</li>
    <li>Impersonate any person or entity</li>
    <li>Attempt to circumvent rate limits, security measures, or access controls</li>
    <li>Reverse engineer, decompile, or disassemble any part of the Service</li>
    <li>Use automated tools to scrape or extract data from the Service</li>
    <li>Resell or redistribute access to the Service without authorization</li>
    <li>Generate spam, phishing content, or malicious code</li>
  </ul>
</section>

<section>
  <h2>6. AI-Generated Content</h2>
  <ul>
    <li>AI responses are generated by third-party language models and may contain errors, inaccuracies, or biases</li>
    <li>NipponClaw does not guarantee the accuracy, completeness, or reliability of AI-generated content</li>
    <li>You are solely responsible for verifying and evaluating AI-generated content before relying on it</li>
    <li>AI-generated content should not be considered professional advice (legal, medical, financial, or otherwise)</li>
    <li>You retain ownership of the input you provide; output generated by the AI may be subject to the terms of the underlying model providers</li>
  </ul>
</section>

<section>
  <h2>7. Intellectual Property</h2>
  <ul>
    <li>The Service, including its design, code, and branding, is owned by NipponClaw and protected by intellectual property laws</li>
    <li>You retain ownership of content you create and upload to the Service</li>
    <li>You grant NipponClaw a limited license to process your content as necessary to provide the Service</li>
    <li>Plugins and tools from ClawHub may be subject to their own license terms</li>
  </ul>
</section>

<section>
  <h2>8. Service Availability</h2>
  <ul>
    <li>We strive to maintain high availability but do not guarantee uninterrupted access</li>
    <li>The Service may be temporarily unavailable for maintenance, updates, or due to factors beyond our control</li>
    <li>We may modify, suspend, or discontinue features or the entire Service with reasonable notice</li>
    <li>Third-party AI model providers may experience outages or changes that affect the Service</li>
  </ul>
</section>

<section>
  <h2>9. Termination</h2>
  <ul>
    <li>You may delete your account at any time through the app settings</li>
    <li>We may suspend or terminate your account for violation of these Terms</li>
    <li>Upon termination, your right to use the Service ceases immediately</li>
    <li>We will delete your data in accordance with our Privacy Policy</li>
    <li>Unused credits are forfeited upon account termination, except where prohibited by law</li>
  </ul>
</section>

<section>
  <h2>10. Limitation of Liability</h2>
  <p>TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW:</p>
  <ul>
    <li>The Service is provided "AS IS" and "AS AVAILABLE" without warranties of any kind, express or implied</li>
    <li>NipponClaw shall not be liable for any indirect, incidental, special, consequential, or punitive damages</li>
    <li>Our total liability for any claim shall not exceed the amount you paid us in the 12 months preceding the claim</li>
    <li>We are not liable for any actions taken based on AI-generated content</li>
    <li>We are not liable for any loss of data, profits, or business opportunities</li>
  </ul>
</section>

<section>
  <h2>11. Governing Law</h2>
  <p>These Terms shall be governed by and construed in accordance with the laws of Japan. Any disputes arising from these Terms or the Service shall be subject to the exclusive jurisdiction of the Tokyo District Court as the court of first instance.</p>
</section>

<section>
  <h2>12. Changes to Terms</h2>
  <p>We reserve the right to update these Terms at any time. We will notify you of material changes through the app or by email. Your continued use of the Service after changes become effective constitutes your acceptance of the revised Terms.</p>
</section>

<section>
  <h2>13. Contact Us</h2>
  <p>For questions about these Terms:</p>
  <ul>
    <li>Email: <strong>support@nipponclaw.com</strong></li>
    <li>Website: <strong>https://nipponclaw.com</strong></li>
  </ul>
</section>

</div>

<!-- ==================== JAPANESE ==================== -->
<div id="japanese">

<section>
  <h2>1. 規約への同意</h2>
  <p>NipponClawプラットフォーム（以下「本サービス」）にアクセスまたは使用することにより、nipponclaw.comウェブサイト、NipponClaw iOSアプリケーション、および関連するAPIを含め、本利用規約（以下「本規約」）に拘束されることに同意したものとみなされます。本規約に同意しない場合は、本サービスをご利用にならないでください。</p>
  <p class="date">最終更新日：2026年4月2日</p>
</section>

<section>
  <h2>2. サービスの説明</h2>
  <p>NipponClawは、ユーザーが以下を行えるAIアシスタントプラットフォームです。</p>
  <ul>
    <li>大規模言語モデルを活用したAIエージェントの作成・設定</li>
    <li>AIエージェントとの会話</li>
    <li>ClawHubマーケットプレイスからのプラグイン・ツールのインストール</li>
    <li>メッセージングチャネル（Telegram、LINE）のAIエージェントへの接続</li>
    <li>自動エージェントタスクのスケジュール設定</li>
  </ul>
  <p>本サービスは、応答を生成するために第三者のAIモデル（DeepSeek、Qwen等を含みますがこれらに限定されません）を使用します。</p>
</section>

<section>
  <h2>3. アカウント登録</h2>
  <ul>
    <li>正確かつ完全な登録情報を提供する必要があります</li>
    <li>アカウント認証情報のセキュリティを維持する責任があります</li>
    <li>アカウントを作成するには16歳以上である必要があります</li>
    <li>一人につき複数のアカウントを保持することはできません</li>
    <li>アカウントで発生するすべてのアクティビティについて責任を負います</li>
  </ul>
</section>

<section>
  <h2>4. クレジットと請求</h2>
  <h3>4.1 クレジットシステム</h3>
  <p>本サービスはクレジットベースのシステムで運営されています。エージェントへのメッセージ送信やツールの使用など、AI機能を使用するとクレジットが消費されます。モデルや機能によって消費されるクレジット数は異なります。</p>
  <h3>4.2 購入</h3>
  <ul>
    <li>クレジットはウェブサイト（Stripe経由）またはiOSアプリ（Appleアプリ内課金経由）で購入できます</li>
    <li>適用法またはApple・Stripeの返金ポリシーに記載されている場合を除き、すべての購入は最終的なものであり、返金不可です</li>
    <li>価格は購入時に該当通貨で表示され、適用される税金を含みます</li>
  </ul>
  <h3>4.3 無料クレジット</h3>
  <p>新規アカウントやプロモーションで無料クレジットを提供する場合があります。無料クレジットには有効期限がある場合があり、譲渡または現金への交換はできません。</p>
</section>

<section>
  <h2>5. 利用上の注意</h2>
  <p>以下の目的で本サービスを使用しないことに同意するものとします。</p>
  <ul>
    <li>違法、有害、脅迫的、虐待的、またはハラスメントに該当するコンテンツの生成</li>
    <li>適用される法律または規制への違反</li>
    <li>他者または団体のなりすまし</li>
    <li>レート制限、セキュリティ対策、またはアクセス制御の回避の試み</li>
    <li>本サービスの一部のリバースエンジニアリング、逆コンパイル、または逆アセンブル</li>
    <li>自動化ツールによる本サービスからのデータスクレイピングまたは抽出</li>
    <li>無許可での本サービスへのアクセスの転売または再配布</li>
    <li>スパム、フィッシングコンテンツ、または悪意のあるコードの生成</li>
  </ul>
</section>

<section>
  <h2>6. AI生成コンテンツ</h2>
  <ul>
    <li>AI応答は第三者の言語モデルによって生成され、エラー、不正確さ、またはバイアスを含む可能性があります</li>
    <li>NipponClawは、AI生成コンテンツの正確性、完全性、または信頼性を保証しません</li>
    <li>AI生成コンテンツに依存する前に、その内容を確認・評価する責任はお客様にあります</li>
    <li>AI生成コンテンツは、専門的なアドバイス（法律、医療、金融等）とみなすべきではありません</li>
    <li>お客様が提供した入力の所有権はお客様に帰属します。AIによって生成された出力は、基盤となるモデルプロバイダーの規約に従う場合があります</li>
  </ul>
</section>

<section>
  <h2>7. 知的財産権</h2>
  <ul>
    <li>デザイン、コード、ブランディングを含む本サービスはNipponClawが所有し、知的財産法によって保護されています</li>
    <li>本サービスに作成・アップロードしたコンテンツの所有権はお客様に帰属します</li>
    <li>本サービスの提供に必要な範囲で、お客様のコンテンツを処理するための限定的なライセンスをNipponClawに付与するものとします</li>
    <li>ClawHubのプラグインおよびツールは、それぞれ独自のライセンス条件に従う場合があります</li>
  </ul>
</section>

<section>
  <h2>8. サービスの可用性</h2>
  <ul>
    <li>高い可用性の維持に努めますが、中断のないアクセスを保証するものではありません</li>
    <li>メンテナンス、アップデート、または当社の管理外の要因により、本サービスが一時的に利用できなくなる場合があります</li>
    <li>合理的な通知をもって、機能または本サービス全体を変更、一時停止、または中止する場合があります</li>
    <li>第三者のAIモデルプロバイダーの障害や変更が本サービスに影響を与える場合があります</li>
  </ul>
</section>

<section>
  <h2>9. 契約の終了</h2>
  <ul>
    <li>アプリの設定からいつでもアカウントを削除できます</li>
    <li>本規約に違反した場合、アカウントを停止または終了する場合があります</li>
    <li>契約終了時、本サービスを使用する権利は直ちに消滅します</li>
    <li>プライバシーポリシーに従ってデータを削除します</li>
    <li>法律で禁止されている場合を除き、アカウント終了時の未使用クレジットは無効となります</li>
  </ul>
</section>

<section>
  <h2>10. 責任の制限</h2>
  <p>適用法が許容する最大限の範囲において：</p>
  <ul>
    <li>本サービスは、明示または黙示を問わず、いかなる種類の保証もなく「現状のまま」かつ「利用可能な状態で」提供されます</li>
    <li>NipponClawは、間接的、偶発的、特別、結果的、または懲罰的損害について責任を負いません</li>
    <li>いかなる請求に対する当社の総責任額は、請求に先立つ12か月間にお客様が当社に支払った金額を超えないものとします</li>
    <li>AI生成コンテンツに基づいて行われたいかなる行為についても責任を負いません</li>
    <li>データ、利益、またはビジネス機会の損失について責任を負いません</li>
  </ul>
</section>

<section>
  <h2>11. 準拠法</h2>
  <p>本規約は日本法に準拠し、同法に従って解釈されるものとします。本規約または本サービスから生じる紛争については、東京地方裁判所を第一審の専属管轄裁判所とします。</p>
</section>

<section>
  <h2>12. 規約の変更</h2>
  <p>当社はいつでも本規約を更新する権利を留保します。重要な変更については、アプリ内またはメールでお知らせします。変更の効力発生後に本サービスの使用を継続した場合、改訂された規約に同意したものとみなされます。</p>
</section>

<section>
  <h2>13. お問い合わせ</h2>
  <p>本規約に関するご質問は下記までお問い合わせください。</p>
  <ul>
    <li>メール：<strong>support@nipponclaw.com</strong></li>
    <li>ウェブサイト：<strong>https://nipponclaw.com</strong></li>
  </ul>
</section>

</div>

</div>

<footer>
  &copy; 2026 NipponClaw. All rights reserved. |
  <a href="/terms">Terms of Service</a> |
  <a href="/privacy">Privacy Policy</a>
</footer>

</body>
</html>
"""


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/privacy", response_class=HTMLResponse)
async def privacy_policy():
    """Return the Privacy Policy page (HTML)."""
    return _PRIVACY_HTML


@router.get("/terms", response_class=HTMLResponse)
async def terms_of_service():
    """Return the Terms of Service page (HTML)."""
    return _TERMS_HTML
