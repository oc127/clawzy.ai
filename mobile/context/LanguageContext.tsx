import React, { createContext, useContext, useState, useEffect, type ReactNode } from "react";
import { getLocale, saveLocale } from "@/lib/storage";

// Re-use same translation structure as web
export type Locale = "en" | "zh" | "ja" | "ko";

const LABELS: Record<Locale, string> = { en: "EN", zh: "中文", ja: "日本語", ko: "한국어" };
const FLAGS: Record<Locale, string> = { en: "🇺🇸", zh: "🇨🇳", ja: "🇯🇵", ko: "🇰🇷" };

// Inline translations for mobile (only what's needed)
const translations = {
  en: {
    nav: { login: "Log in", signup: "Sign up", logout: "Log out", settings: "Settings" },
    auth: {
      login: { title: "Welcome back", subtitle: "Sign in to NipponClaw", email: "Email", password: "Password", submit: "Sign in", noAccount: "No account?", signup: "Sign up", emailPlaceholder: "you@example.com", stat1: "Free credits", stat2: "AI models", stat3: "Uptime" },
      register: { title: "Create account", subtitle: "Free to start", name: "Full name", email: "Email", password: "Password", submit: "Create account", haveAccount: "Have account?", login: "Sign in", namePlaceholder: "Your name", passwordHint: "At least 8 characters", perk1: "500 free credits", perk2: "6+ AI models", perk3: "No credit card needed" },
    },
    tabs: { home: "Home", agents: "Agents", discover: "Discover", settings: "Settings" },
    dashboard: { title: "Dashboard", credits: "Credits", agents: "Agents", usage: "Usage Today", newAgent: "New Agent", welcome: "Welcome back", recentActivity: "Recent Activity", noActivity: "No recent activity", seeAll: "See all →" },
    agents: { title: "My Agents", newAgent: "New Agent", noAgents: "No agents yet", createFirst: "Create your first agent", name: "Agent name", description: "Description (optional)", model: "Model", create: "Create Agent", delete: "Delete", running: "Running", stopped: "Stopped", error: "Error", namePlaceholder: "My Coding Assistant", descPlaceholder: "What does this agent do?" },
    discover: { subtitle: "Explore AI models & skills", availableModels: "Available Models", comingSoonTitle: "ClawHub coming soon", comingSoonSubtitle: "Marketplace for AI agent skills" },
    chat: { placeholder: "Message the agent...", send: "Send", typing: "Agent is thinking...", newConv: "New Chat", noMessages: "Start a conversation" },
    settings: { title: "Settings", profile: "Profile", language: "Language", logout: "Log out", plan: "Plan", credits: "Credits", version: "Version" },
    common: { cancel: "Cancel", confirm: "Confirm", delete: "Delete", save: "Save", back: "Back", loading: "Loading...", error: "Something went wrong", retry: "Retry", areYouSure: "Are you sure?" },
  },
  zh: {
    nav: { login: "登录", signup: "注册", logout: "退出", settings: "设置" },
    auth: {
      login: { title: "欢迎回来", subtitle: "登录 NipponClaw", email: "邮箱", password: "密码", submit: "登录", noAccount: "没有账户？", signup: "注册", emailPlaceholder: "you@example.com", stat1: "免费积分", stat2: "AI 模型", stat3: "在线率" },
      register: { title: "创建账户", subtitle: "免费开始", name: "姓名", email: "邮箱", password: "密码", submit: "创建账户", haveAccount: "已有账户？", login: "登录", namePlaceholder: "你的名字", passwordHint: "至少8个字符", perk1: "500 免费积分", perk2: "6+ AI 模型", perk3: "无需信用卡" },
    },
    tabs: { home: "主页", agents: "Agent", discover: "探索", settings: "设置" },
    dashboard: { title: "控制台", credits: "积分", agents: "Agent", usage: "今日用量", newAgent: "创建", welcome: "欢迎回来", recentActivity: "最近活动", noActivity: "暂无活动", seeAll: "查看全部 →" },
    agents: { title: "我的 Agent", newAgent: "创建", noAgents: "还没有 Agent", createFirst: "创建你的第一个 Agent", name: "名称", description: "描述（可选）", model: "模型", create: "创建", delete: "删除", running: "运行中", stopped: "已停止", error: "错误", namePlaceholder: "我的编程助手", descPlaceholder: "这个 Agent 做什么？" },
    discover: { subtitle: "探索 AI 模型和技能", availableModels: "可用模型", comingSoonTitle: "ClawHub 即将上线", comingSoonSubtitle: "AI 技能市场" },
    chat: { placeholder: "发消息...", send: "发送", typing: "Agent 正在思考...", newConv: "新对话", noMessages: "开始对话" },
    settings: { title: "设置", profile: "个人资料", language: "语言", logout: "退出登录", plan: "套餐", credits: "积分", version: "版本" },
    common: { cancel: "取消", confirm: "确认", delete: "删除", save: "保存", back: "返回", loading: "加载中...", error: "出错了", retry: "重试", areYouSure: "确定吗？" },
  },
  ja: {
    nav: { login: "ログイン", signup: "登録", logout: "ログアウト", settings: "設定" },
    auth: {
      login: { title: "おかえりなさい", subtitle: "NipponClaw にログイン", email: "メール", password: "パスワード", submit: "ログイン", noAccount: "アカウントがない？", signup: "登録", emailPlaceholder: "you@example.com", stat1: "無料クレジット", stat2: "AIモデル", stat3: "稼働率" },
      register: { title: "アカウント作成", subtitle: "無料で始める", name: "氏名", email: "メール", password: "パスワード", submit: "アカウント作成", haveAccount: "アカウントをお持ち？", login: "ログイン", namePlaceholder: "お名前", passwordHint: "8文字以上", perk1: "500無料クレジット", perk2: "6以上のAIモデル", perk3: "クレジットカード不要" },
    },
    tabs: { home: "ホーム", agents: "エージェント", discover: "発見", settings: "設定" },
    dashboard: { title: "ダッシュボード", credits: "クレジット", agents: "エージェント", usage: "本日の使用量", newAgent: "新規作成", welcome: "おかえりなさい", recentActivity: "最近のアクティビティ", noActivity: "アクティビティなし", seeAll: "すべて見る →" },
    agents: { title: "マイエージェント", newAgent: "新規作成", noAgents: "エージェントなし", createFirst: "最初のエージェントを作成", name: "エージェント名", description: "説明（任意）", model: "モデル", create: "作成", delete: "削除", running: "稼働中", stopped: "停止中", error: "エラー", namePlaceholder: "コーディングアシスタント", descPlaceholder: "このエージェントの役割は？" },
    discover: { subtitle: "AIモデルとスキルを探索", availableModels: "利用可能なモデル", comingSoonTitle: "ClawHub 近日公開", comingSoonSubtitle: "AIスキルマーケットプレイス" },
    chat: { placeholder: "メッセージを入力...", send: "送信", typing: "考え中...", newConv: "新しい会話", noMessages: "会話を始めましょう" },
    settings: { title: "設定", profile: "プロフィール", language: "言語", logout: "ログアウト", plan: "プラン", credits: "クレジット", version: "バージョン" },
    common: { cancel: "キャンセル", confirm: "確認", delete: "削除", save: "保存", back: "戻る", loading: "読み込み中...", error: "エラーが発生しました", retry: "再試行", areYouSure: "よろしいですか？" },
  },
  ko: {
    nav: { login: "로그인", signup: "회원가입", logout: "로그아웃", settings: "설정" },
    auth: {
      login: { title: "다시 오셨군요", subtitle: "NipponClaw 로그인", email: "이메일", password: "비밀번호", submit: "로그인", noAccount: "계정 없으신가요?", signup: "회원가입", emailPlaceholder: "you@example.com", stat1: "무료 크레딧", stat2: "AI 모델", stat3: "가동 시간" },
      register: { title: "계정 만들기", subtitle: "무료로 시작", name: "이름", email: "이메일", password: "비밀번호", submit: "계정 만들기", haveAccount: "계정 있으신가요?", login: "로그인", namePlaceholder: "이름 입력", passwordHint: "8자 이상", perk1: "500 무료 크레딧", perk2: "6+ AI 모델", perk3: "신용카드 불필요" },
    },
    tabs: { home: "홈", agents: "에이전트", discover: "탐색", settings: "설정" },
    dashboard: { title: "대시보드", credits: "크레딧", agents: "에이전트", usage: "오늘 사용량", newAgent: "새 에이전트", welcome: "다시 오셨군요", recentActivity: "최근 활동", noActivity: "최근 활동 없음", seeAll: "모두 보기 →" },
    agents: { title: "내 에이전트", newAgent: "새로 만들기", noAgents: "에이전트 없음", createFirst: "첫 에이전트 만들기", name: "이름", description: "설명 (선택)", model: "모델", create: "만들기", delete: "삭제", running: "실행 중", stopped: "정지됨", error: "오류", namePlaceholder: "코딩 어시스턴트", descPlaceholder: "이 에이전트의 역할은?" },
    discover: { subtitle: "AI 모델과 스킬 탐색", availableModels: "사용 가능한 모델", comingSoonTitle: "ClawHub 출시 예정", comingSoonSubtitle: "AI 스킬 마켓플레이스" },
    chat: { placeholder: "메시지 입력...", send: "보내기", typing: "생각 중...", newConv: "새 대화", noMessages: "대화를 시작하세요" },
    settings: { title: "설정", profile: "프로필", language: "언어", logout: "로그아웃", plan: "플랜", credits: "크레딧", version: "버전" },
    common: { cancel: "취소", confirm: "확인", delete: "삭제", save: "저장", back: "뒤로", loading: "로딩 중...", error: "오류가 발생했습니다", retry: "다시 시도", areYouSure: "정말 진행하시겠습니까?" },
  },
} as const;

export type T = typeof translations.en;

interface LanguageContextValue {
  locale: Locale;
  setLocale: (l: Locale) => void;
  t: T;
  locales: Locale[];
  labels: typeof LABELS;
  flags: typeof FLAGS;
}

const LanguageContext = createContext<LanguageContextValue | null>(null);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("ja");

  useEffect(() => {
    getLocale().then((saved) => {
      if (saved && saved in translations) setLocaleState(saved as Locale);
    });
  }, []);

  const setLocale = async (l: Locale) => {
    setLocaleState(l);
    await saveLocale(l);
  };

  return (
    <LanguageContext.Provider value={{
      locale, setLocale, t: translations[locale],
      locales: ["en", "zh", "ja", "ko"], labels: LABELS, flags: FLAGS,
    }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error("useLanguage must be used within LanguageProvider");
  return ctx;
}
