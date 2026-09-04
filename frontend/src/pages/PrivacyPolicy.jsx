import { Link } from "react-router-dom";

import Logo from "../components/Logo.jsx";

function Section({ title, children }) {
  return (
    <section className="mt-8 first:mt-0">
      <h2 className="text-lg font-bold text-slate-900 dark:text-white">{title}</h2>
      <div className="mt-2 space-y-3 text-sm leading-relaxed text-slate-600 dark:text-slate-400">
        {children}
      </div>
    </section>
  );
}

// Plain-language POPIA notice covering what this app actually collects and
// does, per the real data model (apps/accounts, apps/budgets, apps/catalog)
// — not a template. Update this alongside those models, and bump
// POPIA_CONSENT_GIVEN's "policy_version" metadata (see accounts/views.py)
// whenever a change here would need existing users to re-consent.
export default function PrivacyPolicy() {
  return (
    <div className="min-h-screen bg-white dark:bg-navy-900">
      <div className="mx-auto max-w-2xl px-6 py-10 sm:px-10">
        <Logo size={30} />
        <h1 className="mt-8 text-2xl font-bold text-slate-900 dark:text-white">
          Privacy Policy &amp; POPIA notice
        </h1>
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
          Last updated 4 September 2026. This explains what SmartSpend collects, why, and the rights
          you have over it under the Protection of Personal Information Act (POPIA).
        </p>

        <Section title="What we collect">
          <p>When you register, we collect your DUT email address, password (stored as a salted hash,
          never in plain text), campus, residence (optional), and NSFAS disbursement day.</p>
          <p>When you use the app, we also store the budgets and categories you set up, the expenses
          you log, and any product searches you run. If you enable two-factor authentication (required
          at first login), we store the authenticator secret needed to verify your codes.</p>
          <p>We keep an append-only security log of authentication and account events (registration,
          logins, MFA changes, password changes) together with the IP address they came from, for
          fraud prevention and to investigate account issues if you report one.</p>
        </Section>

        <Section title="Why we collect it">
          <p>To create and secure your account, calculate and track your budget against your fixed
          NSFAS allowance, show you nearby prices, and notify you when a category is close to its
          limit. We don&apos;t collect anything beyond what each of those features needs.</p>
        </Section>

        <Section title="Who else sees it">
          <p>Product searches are sent to Google Shopping via SerpApi to fetch live prices — only the
          search terms you enter, not your identity or budget data. We don&apos;t sell personal
          information or share it with advertisers.</p>
          <p>DUT Student Services can access aggregate spending reports for planning purposes. These
          reports only ever show a category or campus total once at least a minimum number of students
          contribute to it, so no individual student&apos;s spending is identifiable in them.</p>
        </Section>

        <Section title="How long we keep it">
          <p>For as long as your account is active. If you leave DUT or want your account closed,
          contact Student Services (details below) — your profile information (campus, residence,
          budgets) can be deleted on request, while a minimal authentication record may be retained
          where we&apos;re required to for security auditing.</p>
        </Section>

        <Section title="Your rights">
          <p>Under POPIA you can ask us to confirm what personal information we hold about you, correct
          it if it&apos;s wrong, or delete it, and you can object to how it&apos;s processed. To
          exercise any of these, contact DUT Student Services quoting the email address on your
          account.</p>
        </Section>

        <Section title="Security">
          <p>Passwords are hashed with bcrypt; sessions use short-lived tokens; two-factor
          authentication is required on every account. Access to student data is restricted by role,
          and every administrative action is logged.</p>
        </Section>

        <Section title="Questions">
          <p>For anything not covered here, contact DUT Student Services or your institution&apos;s
          Information Officer.</p>
        </Section>

        <Link
          to="/register"
          className="mt-10 inline-block font-semibold text-brand-600 hover:underline dark:text-brand-400"
        >
          ← Back to registration
        </Link>
      </div>
    </div>
  );
}
