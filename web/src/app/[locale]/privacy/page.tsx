"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";

export default function PrivacyPage() {
  const t = useTranslations("legal");

  return (
    <div className="min-h-screen bg-background text-foreground">
      <nav className="flex items-center justify-between px-8 py-5 max-w-3xl mx-auto">
        <Link href="/" className="text-base font-semibold tracking-tight">
          Clawzy
        </Link>
      </nav>

      <main className="max-w-3xl mx-auto px-8 py-16">
        <h1 className="text-3xl font-bold tracking-tight mb-8">
          {t("privacyTitle")}
        </h1>
        <p className="text-xs text-muted mb-10">{t("lastUpdated")}: 2025-03-07</p>

        <div className="space-y-8 text-sm text-muted leading-relaxed">
          <section>
            <h2 className="text-lg font-semibold text-foreground mb-3">{t("privacyCollect")}</h2>
            <p>{t("privacyCollectDesc")}</p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-3">{t("privacyUse")}</h2>
            <p>{t("privacyUseDesc")}</p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-3">{t("privacyIsolation")}</h2>
            <p>{t("privacyIsolationDesc")}</p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-3">{t("privacyOpenSource")}</h2>
            <p>{t("privacyOpenSourceDesc")}</p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-3">{t("privacyThirdParty")}</h2>
            <p>{t("privacyThirdPartyDesc")}</p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-3">{t("privacyRights")}</h2>
            <p>{t("privacyRightsDesc")}</p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-3">{t("privacyContact")}</h2>
            <p>{t("privacyContactDesc")}</p>
          </section>
        </div>
      </main>

      <footer className="border-t border-border py-8 text-center text-xs text-muted">
        <Link href="/" className="hover:text-foreground transition-colors">Clawzy.ai</Link>
      </footer>
    </div>
  );
}
