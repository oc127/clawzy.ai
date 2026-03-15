import {
  Globe,
  Calculator,
  Code,
  Database,
  Sparkles,
  MessageSquare,
  Monitor,
} from "lucide-react";

export const CATEGORY_ICONS: Record<string, React.ElementType> = {
  search: Globe,
  productivity: Calculator,
  development: Code,
  data: Database,
  ai: Sparkles,
  communication: MessageSquare,
  browser: Monitor,
};
