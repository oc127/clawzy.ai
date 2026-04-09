"use client";

import Link from "next/link";
import { useLanguage } from "@/context/language-context";

export default function TokushohoPage() {
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
            <Link href="/legal/privacy" className="hover:text-[#222]">
              {isJa ? "プライバシーポリシー" : "Privacy"}
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-6 py-12">
        {isJa ? <TokushohoJa /> : <TokushohoEn />}
      </main>
    </div>
  );
}

function TokushohoJa() {
  return (
    <article className="prose prose-gray max-w-none">
      <h1>特定商取引法に基づく表示</h1>
      <p className="text-sm text-[#717171]">最終更新日：2026年4月9日</p>

      <table className="w-full">
        <tbody>
          <tr>
            <td className="font-semibold w-48">販売事業者</td>
            <td>NipponClaw</td>
          </tr>
          <tr>
            <td className="font-semibold">運営責任者</td>
            <td>（※ 公開前に記入してください）</td>
          </tr>
          <tr>
            <td className="font-semibold">所在地</td>
            <td>（※ 公開前に記入してください）</td>
          </tr>
          <tr>
            <td className="font-semibold">電話番号</td>
            <td>（※ 請求があった場合に遅滞なく開示します）</td>
          </tr>
          <tr>
            <td className="font-semibold">メールアドレス</td>
            <td>support@nipponclaw.com</td>
          </tr>
          <tr>
            <td className="font-semibold">URL</td>
            <td>https://www.nipponclaw.com</td>
          </tr>
          <tr>
            <td className="font-semibold">サービス名称</td>
            <td>NipponClaw AIエージェントプラットフォーム</td>
          </tr>
          <tr>
            <td className="font-semibold">販売価格</td>
            <td>
              <ul className="list-none pl-0 space-y-1">
                <li>Free プラン：0円/月（500クレジット付）</li>
                <li>Starter プラン：$9 USD/月（3,000クレジット付）</li>
                <li>Pro プラン：$19 USD/月（8,000クレジット付）</li>
                <li>Business プラン：$39 USD/月（20,000クレジット付）</li>
              </ul>
              <p className="text-sm text-[#717171]">※ 為替レートにより日本円での請求額が変動する場合があります。</p>
            </td>
          </tr>
          <tr>
            <td className="font-semibold">販売価格以外の必要料金</td>
            <td>インターネット接続料金、通信料金等はお客様のご負担となります。</td>
          </tr>
          <tr>
            <td className="font-semibold">支払方法</td>
            <td>クレジットカード（Visa, Mastercard, JCB, American Express）※ Stripe経由</td>
          </tr>
          <tr>
            <td className="font-semibold">支払時期</td>
            <td>月額プラン：毎月の契約更新日に自動課金</td>
          </tr>
          <tr>
            <td className="font-semibold">サービス提供時期</td>
            <td>お申込み完了後、直ちにご利用いただけます。</td>
          </tr>
          <tr>
            <td className="font-semibold">返品・キャンセル</td>
            <td>
              <ul className="list-none pl-0 space-y-1">
                <li>月額サブスクリプションは次回請求日前にキャンセル可能です。</li>
                <li>日割り計算による返金は行いません。</li>
                <li>無料プランへのダウングレードはいつでも可能です。</li>
              </ul>
            </td>
          </tr>
          <tr>
            <td className="font-semibold">動作環境</td>
            <td>
              <ul className="list-none pl-0 space-y-1">
                <li>ウェブブラウザ：Chrome, Safari, Firefox, Edge（最新版推奨）</li>
                <li>モバイル：iOS 15以上, Android 10以上</li>
              </ul>
            </td>
          </tr>
        </tbody>
      </table>
    </article>
  );
}

function TokushohoEn() {
  return (
    <article className="prose prose-gray max-w-none">
      <h1>Specified Commercial Transaction Act Disclosure</h1>
      <p className="text-sm text-[#717171]">Last updated: April 9, 2026</p>
      <p className="text-sm text-[#717171]">
        Required under the Act on Specified Commercial Transactions (特定商取引法) of Japan.
      </p>

      <table className="w-full">
        <tbody>
          <tr>
            <td className="font-semibold w-48">Seller</td>
            <td>NipponClaw</td>
          </tr>
          <tr>
            <td className="font-semibold">Responsible Person</td>
            <td>(To be filled before launch)</td>
          </tr>
          <tr>
            <td className="font-semibold">Address</td>
            <td>(To be filled before launch)</td>
          </tr>
          <tr>
            <td className="font-semibold">Phone</td>
            <td>(Disclosed upon request without delay)</td>
          </tr>
          <tr>
            <td className="font-semibold">Email</td>
            <td>support@nipponclaw.com</td>
          </tr>
          <tr>
            <td className="font-semibold">URL</td>
            <td>https://www.nipponclaw.com</td>
          </tr>
          <tr>
            <td className="font-semibold">Service Name</td>
            <td>NipponClaw AI Agent Platform</td>
          </tr>
          <tr>
            <td className="font-semibold">Pricing</td>
            <td>
              <ul className="list-none pl-0 space-y-1">
                <li>Free: $0/month (500 credits included)</li>
                <li>Starter: $9 USD/month (3,000 credits included)</li>
                <li>Pro: $19 USD/month (8,000 credits included)</li>
                <li>Business: $39 USD/month (20,000 credits included)</li>
              </ul>
            </td>
          </tr>
          <tr>
            <td className="font-semibold">Additional Costs</td>
            <td>Internet connection fees are borne by the customer.</td>
          </tr>
          <tr>
            <td className="font-semibold">Payment Methods</td>
            <td>Credit card (Visa, Mastercard, JCB, Amex) via Stripe</td>
          </tr>
          <tr>
            <td className="font-semibold">Payment Timing</td>
            <td>Monthly plans: Automatically charged on each renewal date</td>
          </tr>
          <tr>
            <td className="font-semibold">Service Delivery</td>
            <td>Available immediately upon registration.</td>
          </tr>
          <tr>
            <td className="font-semibold">Cancellation &amp; Refund</td>
            <td>
              <ul className="list-none pl-0 space-y-1">
                <li>Subscriptions may be cancelled before the next billing date.</li>
                <li>No prorated refunds.</li>
                <li>Downgrade to Free plan available at any time.</li>
              </ul>
            </td>
          </tr>
          <tr>
            <td className="font-semibold">System Requirements</td>
            <td>
              <ul className="list-none pl-0 space-y-1">
                <li>Web: Chrome, Safari, Firefox, Edge (latest recommended)</li>
                <li>Mobile: iOS 15+, Android 10+</li>
              </ul>
            </td>
          </tr>
        </tbody>
      </table>
    </article>
  );
}
