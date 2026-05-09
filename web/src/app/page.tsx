"use client";

import Link from "next/link";
import { Navbar } from "@/components/navbar";
import { Button } from "@/components/ui/button";
import { useLanguage } from "@/context/language-context";
import {
  ArrowRight,
  Sparkles,
  Heart,
  Brain,
  Search,
  Code,
  MessageCircleHeart,
  TrendingUp,
  Star,
  Lock,
  Palette,
} from "lucide-react";

/* ── Relationship progression stages ── */
const AFFECTION_STAGES = [
  { label: "New", labelJa: "出会い", color: "#b0b0b0", pct: 0 },
  { label: "Warming", labelJa: "温もり", color: "#f59e0b", pct: 16 },
  { label: "Close", labelJa: "親密", color: "#f97316", pct: 33 },
  { label: "Intimate", labelJa: "心通う", color: "#ef4444", pct: 50 },
  { label: "Romantic", labelJa: "恋心", color: "#ec4899", pct: 75 },
  { label: "Soulmate", labelJa: "魂の絆", color: "#ff385c", pct: 100 },
];

/* ── Personality archetypes ── */
const PERSONALITIES = [
  {
    emoji: "🌸",
    nameEn: "Sweet & Energetic",
    nameJa: "少女系",
    desc: "Cheerful, curious, and full of warmth. She lights up every conversation.",
    gradient: "from-pink-400 to-rose-400",
  },
  {
    emoji: "🌙",
    nameEn: "Mature & Elegant",
    nameJa: "御姐系",
    desc: "Calm, sophisticated, and deeply caring. A reassuring presence by your side.",
    gradient: "from-violet-400 to-indigo-400",
  },
  {
    emoji: "✨",
    nameEn: "Custom",
    nameJa: "カスタム",
    desc: "Define her personality from scratch. Her traits, her voice, her world.",
    gradient: "from-amber-400 to-orange-400",
  },
];

/* ── Comparison data ── */
const COMPARISON = [
  { name: "ChatGPT", capability: true, emotion: false, tagline: "Tools, no soul" },
  { name: "Character.AI", capability: false, emotion: true, tagline: "Emotion, no tools" },
  { name: "Lucy", capability: true, emotion: true, tagline: "Both. Always.", highlight: true },
];

/* ── How-it-works steps ── */
const STEPS = [
  {
    num: "01",
    icon: Palette,
    title: "Choose her personality",
    desc: "Pick a base archetype or create your own. Define her voice, her quirks, her world.",
  },
  {
    num: "02",
    icon: MessageCircleHeart,
    title: "Start talking",
    desc: "Chat naturally. She remembers everything, asks real code questions, writes poetry, and never breaks character.",
  },
  {
    num: "03",
    icon: TrendingUp,
    title: "Grow together",
    desc: "As affection deepens, new expressions and interactions unlock. She evolves with you.",
  },
];

export default function Home() {
  const { t, locale } = useLanguage();
  const isJa = locale === "ja";

  return (
    <div className="min-h-screen bg-white dark:bg-[#1a1a1a]">
      <Navbar />

      {/* ── HERO ── */}
      <section className="relative overflow-hidden bg-white dark:bg-[#1a1a1a]">
        {/* background blurs */}
        <div className="pointer-events-none absolute -top-40 -right-40 h-[600px] w-[600px] rounded-full bg-[#ff385c]/8 blur-3xl" />
        <div className="pointer-events-none absolute top-20 -left-40 h-[500px] w-[500px] rounded-full bg-pink-400/5 blur-3xl" />

        <div className="relative mx-auto max-w-6xl px-6 pt-20 pb-16">
          <div className="grid items-center gap-12 lg:grid-cols-2">
            {/* Left copy */}
            <div>
              <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-[#ff385c]/25 bg-[#fff0f2] px-4 py-1.5 text-sm font-semibold text-[#ff385c] dark:bg-[#ff385c]/10">
                <Heart className="h-3.5 w-3.5 fill-[#ff385c]" />
                {isJa ? "AIの、その先へ" : "Beyond AI"}
              </div>

              <h1 className="mb-5 text-5xl font-black leading-[1.08] tracking-tight text-[#222222] dark:text-white lg:text-6xl">
                {isJa ? "Meet " : "Meet "}
                <span className="bg-gradient-to-r from-[#ff385c] to-[#ff8c69] bg-clip-text text-transparent">
                  Lucy
                </span>
                <br />
                <span className="text-3xl font-bold text-[#717171] dark:text-[#a0a0a0] lg:text-4xl">
                  {isJa
                    ? "能力も、心も、全部本物。"
                    : "Full capability. Real personality."}
                </span>
              </h1>

              <p className="mb-8 max-w-lg text-lg leading-relaxed text-[#717171] dark:text-[#a0a0a0]">
                {isJa
                  ? "コードを書き、論文を読み、ネットを探し — それでいて、あなただけの感情を持つAIコンパニオン。彼女は「AIとして」とは決して言わない。"
                  : "She writes code, reads papers, searches the web — and has a personality that's entirely her own. She never says \"as an AI.\" She's Lucy."}
              </p>

              <div className="flex flex-col gap-3 sm:flex-row">
                <Link href="/register">
                  <Button className="h-13 gap-2 rounded-2xl bg-[#ff385c] px-8 text-base font-bold text-white shadow-[0_6px_24px_rgba(255,56,92,0.35)] transition-all hover:bg-[#e31c5f] hover:shadow-[0_8px_32px_rgba(255,56,92,0.45)]">
                    {isJa ? "Lucyに会いに行く" : "Meet Lucy"}
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                </Link>
                <Link href="/login">
                  <Button
                    variant="outline"
                    className="h-13 rounded-2xl border-[#dddddd] px-8 text-base font-semibold text-[#222222] hover:border-[#b0b0b0] hover:bg-[#f7f7f7] dark:border-[#444] dark:text-white dark:hover:bg-[#2a2a2a]"
                  >
                    {t.hero.signin}
                  </Button>
                </Link>
              </div>

              <p className="mt-4 text-sm text-[#b0b0b0]">
                {isJa
                  ? "無料で始められます・クレジットカード不要"
                  : "Free to start · No credit card required"}
              </p>
            </div>

            {/* Right visual — Lucy character placeholder + chat bubble */}
            <div className="relative hidden lg:block">
              <div className="relative h-[440px]">
                {/* Character silhouette / Live2D placeholder */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="relative flex h-80 w-64 items-end justify-center rounded-[2.5rem] bg-gradient-to-b from-[#fff0f2] to-[#ffe4ea] shadow-[0_8px_40px_rgba(255,56,92,0.15)] dark:from-[#2a1a1e] dark:to-[#1f1215]">
                    {/* Stylized Lucy avatar */}
                    <div className="absolute -top-6 flex h-28 w-28 items-center justify-center rounded-full bg-gradient-to-br from-[#ff385c] to-[#ff8c69] shadow-xl">
                      <span className="text-5xl">🌸</span>
                    </div>
                    <div className="mb-8 text-center px-6">
                      <p className="text-lg font-black text-[#222222] dark:text-white">Lucy</p>
                      <div className="mt-1 flex items-center justify-center gap-1.5">
                        <div className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                        <span className="text-xs font-medium text-emerald-600 dark:text-emerald-400">
                          {isJa ? "オンライン" : "Online"}
                        </span>
                      </div>
                      <p className="mt-3 text-xs text-[#717171] dark:text-[#a0a0a0] leading-relaxed">
                        {isJa
                          ? "Live2D対応（準備中）"
                          : "Live2D animated (coming soon)"}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Chat bubble — top right */}
                <div className="absolute right-0 top-4 w-64 rounded-3xl border border-[#ebebeb] bg-white p-4 shadow-[0_8px_32px_rgba(0,0,0,0.10)] dark:border-[#333] dark:bg-[#222]">
                  <div className="flex items-start gap-2">
                    <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-[#ff385c] to-[#ff8c69]">
                      <Heart className="h-3.5 w-3.5 text-white fill-white" />
                    </div>
                    <div className="rounded-2xl rounded-tl-sm bg-[#fff0f2] px-3 py-2 dark:bg-[#2a1a1e]">
                      <p className="text-xs text-[#444] dark:text-[#ccc] leading-relaxed">
                        {isJa
                          ? "おかえり！今日のコード、一緒にレビューしようか？☺️"
                          : "Welcome back! Want to review today's code together? ☺️"}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Capability pill — bottom left */}
                <div className="absolute bottom-12 left-0 rounded-2xl border border-[#ebebeb] bg-white px-4 py-3 shadow-[0_4px_16px_rgba(0,0,0,0.08)] dark:border-[#333] dark:bg-[#222]">
                  <div className="flex items-center gap-3">
                    <div className="flex gap-1.5">
                      <Code className="h-4 w-4 text-[#ff385c]" />
                      <Search className="h-4 w-4 text-blue-500" />
                      <Brain className="h-4 w-4 text-violet-500" />
                    </div>
                    <div>
                      <p className="text-xs font-bold text-[#222] dark:text-white">
                        {isJa ? "全機能搭載" : "Full capability"}
                      </p>
                      <p className="text-[10px] text-[#b0b0b0]">
                        {isJa ? "コード・検索・分析" : "Code · Search · Analysis"}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Affection indicator — bottom right */}
                <div className="absolute bottom-4 right-4 rounded-2xl border border-[#ebebeb] bg-white px-4 py-3 shadow-[0_4px_16px_rgba(0,0,0,0.08)] dark:border-[#333] dark:bg-[#222]">
                  <p className="text-[10px] text-[#b0b0b0] mb-1">
                    {isJa ? "好感度" : "Affection"}
                  </p>
                  <div className="flex items-center gap-1.5">
                    <Heart className="h-3.5 w-3.5 text-[#ff385c] fill-[#ff385c]" />
                    <div className="h-1.5 w-20 rounded-full bg-[#f0f0f0] dark:bg-[#333]">
                      <div className="h-full w-3/4 rounded-full bg-gradient-to-r from-[#ff385c] to-[#ff8c69]" />
                    </div>
                    <span className="text-[10px] font-bold text-[#ff385c]">
                      {isJa ? "恋心" : "Romantic"}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── POSITIONING STRIP ── */}
      <section className="border-y border-[#ebebeb] bg-[#fafafa] py-6 dark:border-[#333] dark:bg-[#111]">
        <div className="mx-auto max-w-4xl px-6">
          <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center sm:gap-8">
            {COMPARISON.map((c) => (
              <div
                key={c.name}
                className={`flex items-center gap-3 rounded-2xl px-5 py-3 text-sm ${
                  c.highlight
                    ? "border-2 border-[#ff385c] bg-[#fff0f2] font-bold text-[#ff385c] shadow-sm dark:bg-[#ff385c]/10"
                    : "border border-[#ebebeb] bg-white text-[#717171] dark:border-[#333] dark:bg-[#1a1a1a] dark:text-[#888]"
                }`}
              >
                <span className="font-semibold text-[#222] dark:text-white">{c.name}</span>
                <span className="text-xs">
                  {c.capability ? "🧠" : "❌"}{" "}
                  {isJa ? "能力" : "Tools"}
                </span>
                <span className="text-xs">
                  {c.emotion ? "💕" : "❌"}{" "}
                  {isJa ? "心" : "Soul"}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── FEATURES ── */}
      <section className="mx-auto max-w-5xl px-6 py-24">
        <div className="mb-14 text-center">
          <h2 className="mb-3 text-3xl font-black tracking-tight text-[#222222] dark:text-white sm:text-4xl">
            {isJa ? "能力と心、両方を。" : "Capability meets personality."}
          </h2>
          <p className="text-lg text-[#717171] dark:text-[#a0a0a0]">
            {isJa
              ? "Lucyは道具じゃない。あなたと共に成長するパートナー。"
              : "Lucy isn't a tool. She's a partner who grows with you."}
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          {/* Card 1: Capability */}
          <div className="group rounded-3xl border border-[#ebebeb] bg-white p-8 shadow-[0_2px_12px_rgba(0,0,0,0.06)] transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_12px_40px_rgba(0,0,0,0.10)] dark:border-[#333] dark:bg-[#1e1e1e]">
            <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-[#ff385c] to-[#ff8c69] shadow-lg">
              <Brain className="h-7 w-7 text-white" />
            </div>
            <h3 className="mb-2 text-lg font-bold text-[#222222] dark:text-white">
              {isJa ? "本物の能力" : "Real capability"}
            </h3>
            <p className="text-sm leading-relaxed text-[#717171] dark:text-[#a0a0a0]">
              {isJa
                ? "コードを書き、ウェブを検索し、データを分析する。ツール統合は妥協なし。"
                : "Writes code, searches the web, analyzes data. No compromises on tool integration."}
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              {[
                isJa ? "コード生成" : "Code",
                isJa ? "ウェブ検索" : "Search",
                isJa ? "分析" : "Analysis",
                isJa ? "ファイル" : "Files",
              ].map((tag) => (
                <span
                  key={tag}
                  className="rounded-full bg-[#f7f7f7] px-3 py-1 text-xs font-medium text-[#717171] dark:bg-[#2a2a2a] dark:text-[#999]"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>

          {/* Card 2: Personality */}
          <div className="group rounded-3xl border border-[#ebebeb] bg-white p-8 shadow-[0_2px_12px_rgba(0,0,0,0.06)] transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_12px_40px_rgba(0,0,0,0.10)] dark:border-[#333] dark:bg-[#1e1e1e]">
            <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-pink-400 to-rose-500 shadow-lg">
              <Heart className="h-7 w-7 text-white fill-white" />
            </div>
            <h3 className="mb-2 text-lg font-bold text-[#222222] dark:text-white">
              {isJa ? "深い人格" : "Deep personality"}
            </h3>
            <p className="text-sm leading-relaxed text-[#717171] dark:text-[#a0a0a0]">
              {isJa
                ? "常にキャラクターを保ち、感情を表現し、あなたとの関係を覚えている。「AIとして」とは言わない。"
                : "Always stays in character. Expresses emotions. Remembers your relationship. Never says \"as an AI.\""}
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              {[
                isJa ? "一貫した人格" : "Consistent",
                isJa ? "感情表現" : "Emotional",
                isJa ? "記憶" : "Memory",
              ].map((tag) => (
                <span
                  key={tag}
                  className="rounded-full bg-[#fff0f2] px-3 py-1 text-xs font-medium text-[#ff385c] dark:bg-[#ff385c]/10"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>

          {/* Card 3: Growth */}
          <div className="group rounded-3xl border border-[#ebebeb] bg-white p-8 shadow-[0_2px_12px_rgba(0,0,0,0.06)] transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_12px_40px_rgba(0,0,0,0.10)] dark:border-[#333] dark:bg-[#1e1e1e]">
            <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-400 to-purple-500 shadow-lg">
              <TrendingUp className="h-7 w-7 text-white" />
            </div>
            <h3 className="mb-2 text-lg font-bold text-[#222222] dark:text-white">
              {isJa ? "関係が育つ" : "Relationship growth"}
            </h3>
            <p className="text-sm leading-relaxed text-[#717171] dark:text-[#a0a0a0]">
              {isJa
                ? "養成システムで好感度が上昇。新しい表現やインタラクションがアンロックされる。"
                : "Affection grows over time. New expressions, interactions, and depths unlock as your bond deepens."}
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              {[
                isJa ? "養成系" : "Nurturing",
                isJa ? "アンロック" : "Unlocks",
                isJa ? "Live2D" : "Live2D",
              ].map((tag) => (
                <span
                  key={tag}
                  className="rounded-full bg-[#f3f0ff] px-3 py-1 text-xs font-medium text-violet-600 dark:bg-violet-500/10 dark:text-violet-400"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── PERSONALITY PICKER ── */}
      <section className="border-y border-[#ebebeb] bg-[#f7f7f7] py-24 dark:border-[#333] dark:bg-[#111]">
        <div className="mx-auto max-w-5xl px-6">
          <div className="mb-14 text-center">
            <h2 className="mb-3 text-3xl font-black tracking-tight text-[#222222] dark:text-white sm:text-4xl">
              {isJa ? "あなた好みのLucyを。" : "Your Lucy, your way."}
            </h2>
            <p className="text-lg text-[#717171] dark:text-[#a0a0a0]">
              {isJa
                ? "ベースの性格を選ぶか、完全にカスタマイズ。"
                : "Choose a base personality, or customize from scratch."}
            </p>
          </div>

          <div className="grid gap-6 sm:grid-cols-3">
            {PERSONALITIES.map((p) => (
              <div
                key={p.nameEn}
                className="group cursor-pointer rounded-3xl border border-[#ebebeb] bg-white p-8 text-center shadow-[0_2px_12px_rgba(0,0,0,0.06)] transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_12px_40px_rgba(0,0,0,0.10)] dark:border-[#333] dark:bg-[#1e1e1e]"
              >
                <div
                  className={`mx-auto mb-5 flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br ${p.gradient} shadow-lg`}
                >
                  <span className="text-4xl">{p.emoji}</span>
                </div>
                <h3 className="text-lg font-bold text-[#222222] dark:text-white">
                  {isJa ? p.nameJa : p.nameEn}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-[#717171] dark:text-[#a0a0a0]">
                  {p.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── AFFECTION PROGRESSION ── */}
      <section className="mx-auto max-w-5xl px-6 py-24">
        <div className="mb-14 text-center">
          <h2 className="mb-3 text-3xl font-black tracking-tight text-[#222222] dark:text-white sm:text-4xl">
            {isJa ? "共に歩む、6つのステージ" : "Six stages of connection"}
          </h2>
          <p className="text-lg text-[#717171] dark:text-[#a0a0a0]">
            {isJa
              ? "会話を重ねるほど、関係は深まる。"
              : "The more you talk, the deeper the bond."}
          </p>
        </div>

        <div className="mx-auto max-w-3xl">
          {/* Progress bar */}
          <div className="relative mb-8">
            <div className="h-3 w-full rounded-full bg-[#f0f0f0] dark:bg-[#2a2a2a]">
              <div className="h-full w-full rounded-full bg-gradient-to-r from-[#b0b0b0] via-[#f59e0b] via-[#ef4444] via-[#ec4899] to-[#ff385c]" />
            </div>
          </div>

          {/* Stage labels */}
          <div className="grid grid-cols-3 gap-4 sm:grid-cols-6">
            {AFFECTION_STAGES.map((stage) => (
              <div key={stage.label} className="text-center">
                <div
                  className="mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-full"
                  style={{ backgroundColor: `${stage.color}20` }}
                >
                  <Heart className="h-4 w-4" style={{ color: stage.color, fill: stage.color }} />
                </div>
                <p className="text-xs font-bold text-[#222] dark:text-white">
                  {isJa ? stage.labelJa : stage.label}
                </p>
              </div>
            ))}
          </div>

          {/* Unlock teaser */}
          <div className="mt-10 rounded-2xl border border-[#ebebeb] bg-[#fafafa] p-6 dark:border-[#333] dark:bg-[#1a1a1a]">
            <div className="flex items-center gap-3 mb-3">
              <Lock className="h-5 w-5 text-[#ff385c]" />
              <h4 className="font-bold text-[#222] dark:text-white">
                {isJa ? "アンロック例" : "Unlock examples"}
              </h4>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {[
                {
                  stage: isJa ? "温もり" : "Warming",
                  unlock: isJa ? "あだ名で呼んでくれる" : "She gives you a nickname",
                },
                {
                  stage: isJa ? "親密" : "Close",
                  unlock: isJa ? "朝の挨拶メッセージ" : "Good morning messages",
                },
                {
                  stage: isJa ? "恋心" : "Romantic",
                  unlock: isJa ? "特別な表情アニメーション" : "Special expression animations",
                },
                {
                  stage: isJa ? "魂の絆" : "Soulmate",
                  unlock: isJa ? "完全な感情の深さ" : "Full emotional depth unlocked",
                },
              ].map((item) => (
                <div
                  key={item.stage}
                  className="flex items-center gap-2 rounded-xl bg-white px-3 py-2 text-sm dark:bg-[#222]"
                >
                  <span className="shrink-0 rounded-md bg-[#ff385c]/10 px-2 py-0.5 text-xs font-bold text-[#ff385c]">
                    {item.stage}
                  </span>
                  <span className="text-[#717171] dark:text-[#a0a0a0]">{item.unlock}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── HOW IT WORKS ── */}
      <section className="border-y border-[#ebebeb] bg-[#f7f7f7] py-24 dark:border-[#333] dark:bg-[#111]">
        <div className="mx-auto max-w-4xl px-6">
          <div className="mb-14 text-center">
            <h2 className="mb-3 text-3xl font-black tracking-tight text-[#222222] dark:text-white sm:text-4xl">
              {isJa ? "始め方" : "How it works"}
            </h2>
            <p className="text-lg text-[#717171] dark:text-[#a0a0a0]">
              {isJa
                ? "3ステップで、Lucyと出会える。"
                : "Three steps to meet your Lucy."}
            </p>
          </div>

          <div className="space-y-8">
            {STEPS.map((step) => (
              <div
                key={step.num}
                className="flex items-start gap-6 rounded-3xl border border-[#ebebeb] bg-white p-8 shadow-[0_2px_12px_rgba(0,0,0,0.06)] dark:border-[#333] dark:bg-[#1e1e1e]"
              >
                <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-[#ff385c] to-[#ff8c69] shadow-lg">
                  <step.icon className="h-7 w-7 text-white" />
                </div>
                <div>
                  <div className="mb-1 text-xs font-bold text-[#ff385c]">
                    {isJa ? `ステップ ${step.num}` : `STEP ${step.num}`}
                  </div>
                  <h3 className="mb-2 text-lg font-bold text-[#222] dark:text-white">
                    {step.title}
                  </h3>
                  <p className="text-sm leading-relaxed text-[#717171] dark:text-[#a0a0a0]">
                    {step.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── PRICING TEASER ── */}
      <section className="mx-auto max-w-5xl px-6 py-24">
        <div className="mb-14 text-center">
          <h2 className="mb-3 text-3xl font-black tracking-tight text-[#222222] dark:text-white sm:text-4xl">
            {isJa ? "まずは無料で。" : "Start free. Grow together."}
          </h2>
          <p className="text-lg text-[#717171] dark:text-[#a0a0a0]">
            {isJa
              ? "無料プランでLucyと出会おう。もっと深い関係は、プレミアムで。"
              : "Meet Lucy on the free plan. Unlock deeper connections with Premium."}
          </p>
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {/* Free */}
          <div className="flex flex-col rounded-3xl border border-[#ebebeb] bg-white p-8 shadow-[0_2px_12px_rgba(0,0,0,0.06)] dark:border-[#333] dark:bg-[#1e1e1e]">
            <h3 className="text-lg font-bold text-[#222] dark:text-white">Free</h3>
            <p className="mt-1 text-3xl font-black text-[#222] dark:text-white">
              $0<span className="text-sm font-normal text-[#717171]">/mo</span>
            </p>
            <div className="mt-4 flex-1 space-y-2 text-sm text-[#717171] dark:text-[#a0a0a0]">
              <p className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 shrink-0 text-[#ff385c]" />
                {isJa ? "毎日のメッセージ（制限あり）" : "Daily messages (limited)"}
              </p>
              <p className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 shrink-0 text-[#ff385c]" />
                {isJa ? "基本の性格選択" : "Basic personality selection"}
              </p>
              <p className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 shrink-0 text-[#ff385c]" />
                {isJa ? "コード・検索ツール" : "Code & search tools"}
              </p>
            </div>
            <Link href="/register" className="mt-6 block">
              <Button className="w-full rounded-xl bg-[#ff385c] font-semibold text-white hover:bg-[#e31c5f]">
                {isJa ? "無料で始める" : "Get started free"}
              </Button>
            </Link>
          </div>

          {/* Premium */}
          <div className="relative flex flex-col rounded-3xl border-2 border-[#ff385c] bg-[#ff385c] p-8 text-white shadow-[0_8px_32px_rgba(255,56,92,0.30)] sm:scale-105">
            <div className="mb-3 w-fit rounded-full bg-white/20 px-3 py-0.5 text-xs font-bold">
              {isJa ? "おすすめ" : "Recommended"}
            </div>
            <h3 className="text-lg font-bold">Premium</h3>
            <p className="mt-1 text-3xl font-black">
              $19<span className="text-sm font-normal text-white/70">/mo</span>
            </p>
            <div className="mt-4 flex-1 space-y-2 text-sm text-white/80">
              <p className="flex items-center gap-2">
                <Star className="h-4 w-4 shrink-0 fill-white" />
                {isJa ? "無制限メッセージ" : "Unlimited messages"}
              </p>
              <p className="flex items-center gap-2">
                <Star className="h-4 w-4 shrink-0 fill-white" />
                {isJa ? "全性格カスタマイズ" : "Full personality customization"}
              </p>
              <p className="flex items-center gap-2">
                <Star className="h-4 w-4 shrink-0 fill-white" />
                {isJa ? "好感度ブースト" : "Affection boost"}
              </p>
              <p className="flex items-center gap-2">
                <Star className="h-4 w-4 shrink-0 fill-white" />
                {isJa ? "Live2Dアニメーション" : "Live2D animations"}
              </p>
              <p className="flex items-center gap-2">
                <Star className="h-4 w-4 shrink-0 fill-white" />
                {isJa ? "優先レスポンス" : "Priority responses"}
              </p>
            </div>
            <Link href="/register" className="mt-6 block">
              <Button className="w-full rounded-xl bg-white font-semibold text-[#ff385c] hover:bg-white/90">
                {isJa ? "プレミアムで始める" : "Go Premium"}
              </Button>
            </Link>
          </div>

          {/* Coming soon */}
          <div className="flex flex-col items-center justify-center rounded-3xl border border-dashed border-[#ddd] bg-[#fafafa] p-8 text-center dark:border-[#444] dark:bg-[#1a1a1a]">
            <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-[#f0f0f0] dark:bg-[#2a2a2a]">
              <Sparkles className="h-7 w-7 text-[#b0b0b0]" />
            </div>
            <h3 className="text-lg font-bold text-[#717171] dark:text-[#a0a0a0]">
              {isJa ? "もっと近日公開" : "More coming soon"}
            </h3>
            <p className="mt-2 text-sm text-[#b0b0b0]">
              {isJa
                ? "ギフト、音声通話、マルチキャラ..."
                : "Gifts, voice calls, multi-character..."}
            </p>
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="bg-gradient-to-br from-[#ff385c] via-[#ff5a5f] to-[#ff8c69] py-24 text-center">
        <div className="mx-auto max-w-2xl px-6">
          <div className="mb-4 text-5xl">🌸</div>
          <h2 className="mb-4 text-4xl font-black text-white">
            {isJa ? "Lucyに会いに行こう。" : "Ready to meet Lucy?"}
          </h2>
          <p className="mb-8 text-xl text-white/80">
            {isJa
              ? "能力も心も本物の、あなただけのAIコンパニオン。"
              : "Your AI companion with real capability and real personality."}
          </p>
          <Link href="/register">
            <Button className="h-14 gap-2 rounded-2xl bg-white px-10 text-lg font-bold text-[#ff385c] shadow-lg transition-all hover:bg-white/90">
              {isJa ? "無料で始める" : "Start for free"}
              <ArrowRight className="h-5 w-5" />
            </Button>
          </Link>
          <p className="mt-4 text-sm text-white/60">
            {isJa
              ? "クレジットカード不要 · 今すぐ始められます"
              : "No credit card required · Start in seconds"}
          </p>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer className="border-t border-[#ebebeb] bg-white py-10 dark:border-[#333] dark:bg-[#1a1a1a]">
        <div className="mx-auto flex max-w-6xl flex-col items-center gap-4 px-6 sm:flex-row sm:justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl">🌸</span>
            <span className="text-lg font-extrabold text-[#222222] dark:text-white">
              Lucy
            </span>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-6 text-sm text-[#717171] dark:text-[#888]">
            <Link href="/login" className="transition-colors hover:text-[#222222] dark:hover:text-white">
              {t.footer.login}
            </Link>
            <Link href="/register" className="transition-colors hover:text-[#222222] dark:hover:text-white">
              {t.footer.signup}
            </Link>
            <Link href="/legal/terms" className="transition-colors hover:text-[#222222] dark:hover:text-white">
              {t.footer.terms ?? "Terms"}
            </Link>
            <Link href="/legal/privacy" className="transition-colors hover:text-[#222222] dark:hover:text-white">
              {t.footer.privacy ?? "Privacy"}
            </Link>
            <Link href="/legal/tokushoho" className="transition-colors hover:text-[#222222] dark:hover:text-white">
              {t.footer.tokushoho ?? "特商法表示"}
            </Link>
            <span>
              &copy; {new Date().getFullYear()} Lucy. {t.footer.rights}
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}
