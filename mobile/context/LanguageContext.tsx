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
      login: { title: "Welcome back", subtitle: "Sign in to Lucy", email: "Email", password: "Password", submit: "Sign in", noAccount: "No account?", signup: "Sign up", emailPlaceholder: "you@example.com", stat1: "Free credits", stat2: "AI models", stat3: "Uptime", forgotPassword: "Forgot password?" },
      register: { title: "Create account", subtitle: "Free to start", name: "Full name", email: "Email", password: "Password", submit: "Create account", haveAccount: "Have account?", login: "Sign in", namePlaceholder: "Your name", passwordHint: "At least 8 characters", perk1: "500 free credits", perk2: "6+ AI models", perk3: "No credit card needed" },
      forgotPassword: { title: "Forgot password?", subtitle: "Enter your email to receive a reset link", email: "Email", submit: "Send reset link", backToLogin: "Back to sign in", sent: "If that email is registered, a reset link has been sent." },
      resetPassword: { title: "Reset password", subtitle: "Enter your new password", password: "New password", confirm: "Confirm password", submit: "Reset password", success: "Password reset! You can now sign in.", backToLogin: "Back to sign in", mismatch: "Passwords do not match" },
    },
    tabs: { home: "Chat", status: "Status", memory: "Memory", knowledge: "Knowledge", settings: "Settings" },
    dashboard: { title: "Lucy", credits: "Credits", mood: "Mood", usage: "Usage Today", welcome: "Welcome back", recentActivity: "Recent Activity", noActivity: "No recent activity", seeAll: "See all →" },
    lucy: { title: "Lucy Status", mood: "Mood", affection: "Affection", stage: "Relationship", streak: "Streak", totalInteractions: "Interactions", personality: "Personality", expressions: "Expressions", noExpressions: "No expressions unlocked yet", model: "Preferred Model" },
    memory: { title: "Memory", subtitle: "Lucy's conversation history", noConversations: "No conversations yet", startFirst: "Start chatting with Lucy" },
    knowledge: { title: "Knowledge Base", subtitle: "Manage Lucy's knowledge", empty: "No knowledge bases yet", emptySubtitle: "Create a knowledge base to give Lucy custom knowledge", createNew: "Create New", createTitle: "New Knowledge Base", namePlaceholder: "Knowledge base name", documents: "Documents", chunks: "Chunks", active: "Active", inactive: "Inactive", noDocuments: "No documents yet", deleteKb: "Delete Knowledge Base", deleteDoc: "Delete Document", deleteKbConfirm: "This will permanently delete this knowledge base and all its documents.", deleteDocConfirm: "This will permanently delete this document.", pending: "Pending", processing: "Processing", ready: "Ready", failed: "Failed" },
    chat: { placeholder: "Message Lucy...", send: "Send", typing: "Lucy is thinking...", newConv: "New Chat", noMessages: "Start a conversation with Lucy" },
    settings: { title: "Settings", profile: "Profile", language: "Language", logout: "Log out", plan: "Plan", credits: "Credits", version: "Version", editProfile: "Edit Profile", name: "Name", changePassword: "Change Password", currentPassword: "Current password", newPassword: "New password", confirmPassword: "Confirm password", passwordChanged: "Password changed", passwordMismatch: "Passwords do not match", billing: "Billing", transactions: "Transactions", noTransactions: "No transactions yet" },
    common: { cancel: "Cancel", confirm: "Confirm", delete: "Delete", save: "Save", back: "Back", loading: "Loading...", error: "Something went wrong", retry: "Retry", areYouSure: "Are you sure?" },
  },
  zh: {
    nav: { login: "登录", signup: "注册", logout: "退出", settings: "设置" },
    auth: {
      login: { title: "欢迎回来", subtitle: "登录 Lucy", email: "邮箱", password: "密码", submit: "登录", noAccount: "没有账户？", signup: "注册", emailPlaceholder: "you@example.com", stat1: "免费积分", stat2: "AI 模型", stat3: "在线率", forgotPassword: "忘记密码？" },
      register: { title: "创建账户", subtitle: "免费开始", name: "姓名", email: "邮箱", password: "密码", submit: "创建账户", haveAccount: "已有账户？", login: "登录", namePlaceholder: "你的名字", passwordHint: "至少8个字符", perk1: "500 免费积分", perk2: "6+ AI 模型", perk3: "无需信用卡" },
      forgotPassword: { title: "忘记密码？", subtitle: "输入邮箱，我们将发送重置链接", email: "邮箱", submit: "发送重置链接", backToLogin: "返回登录", sent: "如果该邮箱已注册，重置链接已发送。" },
      resetPassword: { title: "重置密码", subtitle: "输入新密码", password: "新密码", confirm: "确认密码", submit: "重置密码", success: "密码重置成功！请登录。", backToLogin: "返回登录", mismatch: "两次密码输入不一致" },
    },
    tabs: { home: "聊天", status: "状态", memory: "记忆", knowledge: "知识库", settings: "设置" },
    dashboard: { title: "Lucy", credits: "积分", mood: "心情", usage: "今日用量", welcome: "欢迎回来", recentActivity: "最近活动", noActivity: "暂无活动", seeAll: "查看全部 →" },
    lucy: { title: "Lucy 状态", mood: "心情", affection: "好感度", stage: "关系", streak: "连续互动", totalInteractions: "总互动次数", personality: "性格", expressions: "表情", noExpressions: "还没有解锁表情", model: "偏好模型" },
    memory: { title: "记忆", subtitle: "Lucy 的对话历史", noConversations: "还没有对话", startFirst: "和 Lucy 开始聊天吧" },
    knowledge: { title: "知识库", subtitle: "管理 Lucy 的知识", empty: "还没有知识库", emptySubtitle: "创建知识库，赋予 Lucy 自定义知识", createNew: "新建", createTitle: "新建知识库", namePlaceholder: "知识库名称", documents: "文档", chunks: "分块", active: "启用", inactive: "未启用", noDocuments: "暂无文档", deleteKb: "删除知识库", deleteDoc: "删除文档", deleteKbConfirm: "这将永久删除该知识库及其所有文档。", deleteDocConfirm: "这将永久删除该文档。", pending: "等待中", processing: "处理中", ready: "就绪", failed: "失败" },
    chat: { placeholder: "给 Lucy 发消息...", send: "发送", typing: "Lucy 正在思考...", newConv: "新对话", noMessages: "和 Lucy 开始对话" },
    settings: { title: "设置", profile: "个人资料", language: "语言", logout: "退出登录", plan: "套餐", credits: "积分", version: "版本", editProfile: "编辑资料", name: "姓名", changePassword: "修改密码", currentPassword: "当前密码", newPassword: "新密码", confirmPassword: "确认密码", passwordChanged: "密码已修改", passwordMismatch: "两次密码不一致", billing: "账单", transactions: "交易记录", noTransactions: "暂无交易" },
    common: { cancel: "取消", confirm: "确认", delete: "删除", save: "保存", back: "返回", loading: "加载中...", error: "出错了", retry: "重试", areYouSure: "确定吗？" },
  },
  ja: {
    nav: { login: "ログイン", signup: "登録", logout: "ログアウト", settings: "設定" },
    auth: {
      login: { title: "おかえりなさい", subtitle: "Lucy にログイン", email: "メール", password: "パスワード", submit: "ログイン", noAccount: "アカウントがない？", signup: "登録", emailPlaceholder: "you@example.com", stat1: "無料クレジット", stat2: "AIモデル", stat3: "稼働率", forgotPassword: "パスワードをお忘れですか？" },
      register: { title: "アカウント作成", subtitle: "無料で始める", name: "氏名", email: "メール", password: "パスワード", submit: "アカウント作成", haveAccount: "アカウントをお持ち？", login: "ログイン", namePlaceholder: "お名前", passwordHint: "8文字以上", perk1: "500無料クレジット", perk2: "6以上のAIモデル", perk3: "クレジットカード不要" },
      forgotPassword: { title: "パスワードをお忘れですか？", subtitle: "メールアドレスを入力してください", email: "メール", submit: "リセットリンクを送信", backToLogin: "ログインに戻る", sent: "登録済みのメールアドレスであれば、リセットリンクが送信されました。" },
      resetPassword: { title: "パスワードリセット", subtitle: "新しいパスワードを入力してください", password: "新しいパスワード", confirm: "パスワード確認", submit: "パスワードをリセット", success: "パスワードがリセットされました！ログインしてください。", backToLogin: "ログインに戻る", mismatch: "パスワードが一致しません" },
    },
    tabs: { home: "チャット", status: "ステータス", memory: "メモリー", knowledge: "知識", settings: "設定" },
    dashboard: { title: "Lucy", credits: "クレジット", mood: "気分", usage: "本日の使用量", welcome: "おかえりなさい", recentActivity: "最近のアクティビティ", noActivity: "アクティビティなし", seeAll: "すべて見る →" },
    lucy: { title: "Lucy ステータス", mood: "気分", affection: "好感度", stage: "関係", streak: "連続インタラクション", totalInteractions: "総インタラクション数", personality: "性格", expressions: "表情", noExpressions: "まだ表情がアンロックされていません", model: "お気に入りモデル" },
    memory: { title: "メモリー", subtitle: "Lucyの会話履歴", noConversations: "まだ会話がありません", startFirst: "Lucyとチャットを始めましょう" },
    knowledge: { title: "知識ベース", subtitle: "Lucyの知識を管理", empty: "知識ベースがありません", emptySubtitle: "知識ベースを作成して、Lucyにカスタム知識を与えましょう", createNew: "新規作成", createTitle: "新しい知識ベース", namePlaceholder: "知識ベース名", documents: "ドキュメント", chunks: "チャンク", active: "有効", inactive: "無効", noDocuments: "ドキュメントがありません", deleteKb: "知識ベースを削除", deleteDoc: "ドキュメントを削除", deleteKbConfirm: "この知識ベースとすべてのドキュメントが完全に削除されます。", deleteDocConfirm: "このドキュメントが完全に削除されます。", pending: "保留中", processing: "処理中", ready: "準備完了", failed: "失敗" },
    chat: { placeholder: "Lucyにメッセージ...", send: "送信", typing: "Lucy が考え中...", newConv: "新しい会話", noMessages: "Lucyと会話を始めましょう" },
    settings: { title: "設定", profile: "プロフィール", language: "言語", logout: "ログアウト", plan: "プラン", credits: "クレジット", version: "バージョン", editProfile: "プロフィール編集", name: "名前", changePassword: "パスワード変更", currentPassword: "現在のパスワード", newPassword: "新しいパスワード", confirmPassword: "パスワード確認", passwordChanged: "パスワードを変更しました", passwordMismatch: "パスワードが一致しません", billing: "請求", transactions: "取引履歴", noTransactions: "取引履歴はありません" },
    common: { cancel: "キャンセル", confirm: "確認", delete: "削除", save: "保存", back: "戻る", loading: "読み込み中...", error: "エラーが発生しました", retry: "再試行", areYouSure: "よろしいですか？" },
  },
  ko: {
    nav: { login: "로그인", signup: "회원가입", logout: "로그아웃", settings: "설정" },
    auth: {
      login: { title: "다시 오셨군요", subtitle: "Lucy 로그인", email: "이메일", password: "비밀번호", submit: "로그인", noAccount: "계정 없으신가요?", signup: "회원가입", emailPlaceholder: "you@example.com", stat1: "무료 크레딧", stat2: "AI 모델", stat3: "가동 시간", forgotPassword: "비밀번호를 잊으셨나요?" },
      register: { title: "계정 만들기", subtitle: "무료로 시작", name: "이름", email: "이메일", password: "비밀번호", submit: "계정 만들기", haveAccount: "계정 있으신가요?", login: "로그인", namePlaceholder: "이름 입력", passwordHint: "8자 이상", perk1: "500 무료 크레딧", perk2: "6+ AI 모델", perk3: "신용카드 불필요" },
      forgotPassword: { title: "비밀번호를 잊으셨나요?", subtitle: "이메일을 입력하시면 재설정 링크를 보내드립니다", email: "이메일", submit: "재설정 링크 보내기", backToLogin: "로그인으로 돌아가기", sent: "등록된 이메일이라면 재설정 링크가 발송되었습니다." },
      resetPassword: { title: "비밀번호 재설정", subtitle: "새 비밀번호를 입력해주세요", password: "새 비밀번호", confirm: "비밀번호 확인", submit: "비밀번호 재설정", success: "비밀번호가 재설정되었습니다! 로그인해주세요.", backToLogin: "로그인으로 돌아가기", mismatch: "비밀번호가 일치하지 않습니다" },
    },
    tabs: { home: "채팅", status: "상태", memory: "기억", knowledge: "지식", settings: "설정" },
    dashboard: { title: "Lucy", credits: "크레딧", mood: "기분", usage: "오늘 사용량", welcome: "다시 오셨군요", recentActivity: "최근 활동", noActivity: "최근 활동 없음", seeAll: "모두 보기 →" },
    lucy: { title: "Lucy 상태", mood: "기분", affection: "호감도", stage: "관계", streak: "연속 대화", totalInteractions: "총 대화 수", personality: "성격", expressions: "표정", noExpressions: "아직 해금된 표정이 없습니다", model: "선호 모델" },
    memory: { title: "기억", subtitle: "Lucy의 대화 기록", noConversations: "대화가 없습니다", startFirst: "Lucy와 대화를 시작하세요" },
    knowledge: { title: "지식 베이스", subtitle: "Lucy의 지식 관리", empty: "지식 베이스가 없습니다", emptySubtitle: "지식 베이스를 만들어 Lucy에게 맞춤 지식을 제공하세요", createNew: "새로 만들기", createTitle: "새 지식 베이스", namePlaceholder: "지식 베이스 이름", documents: "문서", chunks: "청크", active: "활성", inactive: "비활성", noDocuments: "문서가 없습니다", deleteKb: "지식 베이스 삭제", deleteDoc: "문서 삭제", deleteKbConfirm: "이 지식 베이스와 모든 문서가 영구적으로 삭제됩니다.", deleteDocConfirm: "이 문서가 영구적으로 삭제됩니다.", pending: "대기 중", processing: "처리 중", ready: "준비 완료", failed: "실패" },
    chat: { placeholder: "Lucy에게 메시지...", send: "보내기", typing: "Lucy가 생각 중...", newConv: "새 대화", noMessages: "Lucy와 대화를 시작하세요" },
    settings: { title: "설정", profile: "프로필", language: "언어", logout: "로그아웃", plan: "플랜", credits: "크레딧", version: "버전", editProfile: "프로필 수정", name: "이름", changePassword: "비밀번호 변경", currentPassword: "현재 비밀번호", newPassword: "새 비밀번호", confirmPassword: "비밀번호 확인", passwordChanged: "비밀번호가 변경되었습니다", passwordMismatch: "비밀번호가 일치하지 않습니다", billing: "결제", transactions: "거래 내역", noTransactions: "거래 내역이 없습니다" },
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
