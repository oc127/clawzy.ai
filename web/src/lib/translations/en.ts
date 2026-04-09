const en = {
  // Navbar
  nav: {
    login: "Log in",
    signup: "Sign up",
    dashboard: "Dashboard",
    logout: "Log out",
  },
  // Landing hero
  hero: {
    badge: "Now available in Japan 🇯🇵",
    title1: "Your AI Agent,",
    title2: "Any Brain.",
    desc: "Create custom AI agents powered by the world's best models. DeepSeek, Qwen, Claude, GPT-4 — all in one place. Pay only for what you use.",
    cta: "Start for free",
    signin: "Sign in",
    subtext: "500 free credits · No credit card required",
    agentCard1: {
      name: "Code Assistant",
      running: "Running",
      lastMsg: "Sure! Here's the optimized React hook with TypeScript types...",
      model: "DeepSeek Chat",
      credits: "12 cr used today",
    },
    agentCard2: {
      name: "Research Hub",
      running: "Running",
      skill1: "Summarize paper",
      skill2: "Find insights",
      skill3: "Compare models",
    },
    creditBalance: "Credit Balance",
    creditBonus: "+500 bonus",
  },
  // Model strip
  poweredBy: "Powered by",
  // Features
  features: {
    title: "Everything you need",
    subtitle: "A complete platform for building and running AI agents.",
    items: [
      {
        title: "Custom AI Agents",
        desc: "Create personal agents that run 24/7. Each agent gets its own isolated environment with persistent memory and skills.",
      },
      {
        title: "Multiple AI Models",
        desc: "Switch between DeepSeek, Qwen, Claude, GPT-4 and more. Find the perfect model for every task.",
      },
      {
        title: "Pay-as-you-go",
        desc: "Start with 500 free credits. No monthly commitment — top up when you need, or subscribe for better rates.",
      },
    ],
  },
  // Trust
  trust: [
    { title: "Lightning Fast", desc: "Sub-second streaming" },
    { title: "Secure & Isolated", desc: "Containerized agents" },
    { title: "Always Improving", desc: "New models weekly" },
  ],
  // Pricing
  pricing: {
    title: "Simple pricing",
    subtitle: "Start free. Scale as you grow.",
    mostPopular: "Most Popular",
    perMonth: "/mo",
    creditsPerMonth: "credits/mo",
    getStarted: "Get started",
    agent: "agent",
    agents: "agents",
  },
  // Reviews
  reviews: {
    title: "Loved by creators",
    subtitle: "Join thousands of users building with NipponClaw.",
    items: [
      { name: "Yuki T.", role: "Software Engineer, Tokyo", text: "I run 3 agents 24/7 for coding, research, and writing. Best AI platform I've tried." },
      { name: "Haruto M.", role: "Product Manager", text: "The pay-as-you-go model is perfect. Switching between DeepSeek and Qwen is seamless." },
      { name: "Aoi S.", role: "Freelancer", text: "Finally one platform for all the cutting-edge models. The Japanese support is excellent!" },
    ],
  },
  // CTA
  cta: {
    title: "Start building today",
    subtitle: "Create your first AI agent in under a minute. Free to start.",
    button: "Create Free Account",
    subtext: "No credit card required · 500 free credits",
  },
  // Footer
  footer: {
    login: "Log in",
    signup: "Sign up",
    terms: "Terms",
    privacy: "Privacy",
    tokushoho: "Commercial Disclosure",
    rights: "All rights reserved.",
  },
  // Auth
  auth: {
    login: {
      title: "Welcome back",
      subtitle: "Sign in to your NipponClaw account",
      email: "Email address",
      password: "Password",
      submit: "Sign in",
      noAccount: "Don't have an account?",
      signup: "Sign up",
      leftTitle: "Your AI agents are waiting",
      leftStat1: "Active Agents",
      leftStat2: "Models Available",
      leftStat3: "Uptime",
    },
    register: {
      title: "Create your account",
      subtitle: "Start building AI agents for free",
      name: "Full name",
      email: "Email address",
      password: "Password",
      submit: "Create account",
      haveAccount: "Already have an account?",
      login: "Sign in",
      perk1: "500 free credits to start",
      perk2: "Access to 6+ AI models",
      perk3: "No credit card required",
      leftTitle: "Join NipponClaw",
      agreePrefix: "By signing up, you agree to our",
      termsLink: "Terms of Service",
      agreeAnd: "and",
      privacyLink: "Privacy Policy",
    },
  },
  // Dashboard
  dashboard: {
    title: "Dashboard",
    welcome: "Welcome back",
    agents: "Agents",
    models: "Models",
    billing: "Billing",
    settings: "Settings",
    clawhub: "ClawHub",
    credits: "Credits",
    usage: "Usage",
    recentActivity: "Recent Activity",
    quickActions: "Quick Actions",
    newAgent: "New Agent",
    topUp: "Top Up Credits",
    viewModels: "View Models",
    noActivity: "No recent activity",
  },
  chat: {
    reconnecting: "Reconnecting...",
    connectionLost: "Connection lost. Waiting for network...",
    connectionRestored: "Connected",
  },
};

export default en;
export type Translations = typeof en;
