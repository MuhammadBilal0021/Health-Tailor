"use client";
import Link from "next/link";
import {
  ArrowUpRight,
  ArrowRight,
  Leaf,
  Globe2,
  MoveDown,
  Sparkles,
} from "lucide-react";
import { useStore } from "@/lib/store";
import { FoodArt } from "./food-art";
export function Landing() {
  const { t, locale, setLocale } = useStore();
  return (
    <div className="landing">
      <a href="#main" className="skip-link">
        {t("Skip to content", "انتقل إلى المحتوى")}
      </a>
      <header className="landing-header">
        <Link href="/" className="brand">
          <span className="brand-icon">
            <Leaf size={22} />
          </span>
          <span>
            Health Tailor
            <small>{t("FOOD, WITH THOUGHT.", "طعام بعناية.")}</small>
          </span>
        </Link>
        <nav>
          <a href="#how">{t("How it works", "كيف يعمل")}</a>
          <Link href="/restaurant">{t("For kitchens", "للمطاعم")}</Link>
          <button
            className="language"
            onClick={() => setLocale(locale === "en" ? "ar" : "en")}
          >
            <Globe2 size={16} />
            {locale === "en" ? "العربية" : "English"}
          </button>
          <Link className="button outline small-button" href="/login">
            {t("Sign in", "تسجيل الدخول")}
            <ArrowUpRight size={15} />
          </Link>
        </nav>
      </header>
      <main id="main">
        <section className="landing-hero">
          <div className="hero-copy">
            <div className="eyebrow">
              <span className="tiny-dot" />
              {t(
                "A LITTLE MORE MINDFUL. A LOT MORE YOU.",
                "اختيارات واعية تناسبك.",
              )}
            </div>
            <h1>
              {t("Good food.", "طعام جيد.")}
              <br />
              {t("A better fit", "اختيار أفضل")}
              <br />
              <em>{t("for you.", "لك.")}</em>
            </h1>
            <p className="lead">
              {t(
                "Your preferences deserve a place at the table. Discover thoughtful meals, explore what’s in them, and make your next order a little more personal.",
                "تفضيلاتك تستحق مكاناً على المائدة. اكتشف وجبات تناسبك وتعرّف على مكوناتها واجعل طلبك القادم أكثر ملاءمة لك.",
              )}
            </p>
            <div className="hero-actions">
              <Link className="button" href="/explore">
                {t("Find your next meal", "اكتشف وجبتك القادمة")}
                <ArrowUpRight size={19} />
              </Link>
              <a href="#how" className="quiet-link">
                {t("Take a closer look", "تعرّف على المزيد")}
                <MoveDown size={15} />
              </a>
            </div>
            <div className="hero-footnote">
              <span className="mini-leaf">
                <Leaf size={14} />
              </span>
              {t(
                "Explore freely. No account needed for the demo.",
                "جرّب بحرية. العرض لا يحتاج إلى حساب.",
              )}
            </div>
          </div>
          <div className="hero-art">
            <div className="art-caption">
              {t(
                "ON THE MENU / A LITTLE INSPIRATION",
                "من القائمة / قليل من الإلهام",
              )}
            </div>
            <FoodArt className="hero-bowl" />
            <div className="round-note">
              {t("A more", "وجبة")}
              <br />
              {t("thoughtful", "بعناية")}
              <br />
              {t("plate.", "أكبر.")}
              <Leaf size={15} />
            </div>
            <div className="art-bottom">
              <div>
                <p className="eyebrow">
                  01 / {t("THE EVERYDAY BOWL", "وعاء كل يوم")}
                </p>
                <h2>
                  {t("Simple ingredients.", "مكونات بسيطة.")}
                  <br />
                  {t("Something good.", "طعم رائع.")}
                </h2>
              </div>
              <span className="art-arrow">
                <ArrowUpRight size={24} />
              </span>
            </div>
            <p className="art-disclaimer">
              {t(
                "Illustrated sample dish · Explore ingredients before ordering",
                "طبق تجريبي مرسوم · تحقق من المكونات قبل الطلب",
              )}
            </p>
          </div>
        </section>
        <div className="promise-strip">
          {[
            [Leaf, "Built around your preferences", "مبني على تفضيلاتك"],
            [
              Sparkles,
              "AI-assisted exploration",
              "استكشاف بمساعدة الذكاء الاصطناعي",
            ],
            [
              ArrowRight,
              "From discovery to delivery",
              "من الاكتشاف إلى التوصيل",
            ],
          ].map(([Icon, en, ar], i) => {
            const C = Icon as typeof Leaf;
            return (
              <div key={i}>
                <C size={16} />
                <span>{t(en as string, ar as string)}</span>
              </div>
            );
          })}
        </div>
        <section className="how-section" id="how">
          <div>
            <p className="eyebrow">
              {t("A LITTLE CONTEXT GOES A LONG WAY", "تفاصيل صغيرة تصنع الفرق")}
            </p>
            <h2>
              {t("Your next meal,", "وجبتك القادمة،")}
              <br />
              <em>{t("with more clarity.", "بوضوح أكبر.")}</em>
            </h2>
            <p>
              {t(
                "One place to connect what matters to you with what’s actually on the menu.",
                "مكان واحد يجمع ما يهمك مع ما تقدمه المطاعم فعلاً.",
              )}
            </p>
            <Link className="quiet-link" href="/profile">
              {t("Make it personal", "اجعلها شخصية")}
              <ArrowUpRight size={16} />
            </Link>
          </div>
          <div className="steps">
            {[
              [
                "01",
                "Tell us what matters",
                "أخبرنا بما يهمك",
                "Set your tastes, preferences and optional health considerations. You stay in control of what you share.",
                "حدد ذوقك وتفضيلاتك واعتباراتك الصحية الاختيارية. أنت تتحكم فيما تشاركه.",
              ],
              [
                "02",
                "Explore with context",
                "اكتشف بوعي",
                "Browse ingredient lists and kitchen menus. Optional AI can help you ask better questions about a meal.",
                "تصفح المكونات وقوائم المطاعم. يمكن للذكاء الاصطناعي مساعدتك في استكشاف وجبتك.",
              ],
              [
                "03",
                "Make it a meal",
                "حوّل اختيارك إلى وجبة",
                "Add a dish, check out, and follow its journey from the kitchen to your door.",
                "أضف طبقاً وأكمل طلبك وتابع رحلته من المطبخ إلى بابك.",
              ],
            ].map(([n, en, ar, desc, descAr]) => (
              <article key={n}>
                <span>{n}</span>
                <div>
                  <h3>{t(en, ar)}</h3>
                  <p>{t(desc, descAr)}</p>
                </div>
              </article>
            ))}
          </div>
        </section>
        <section className="project-note">
          <div>
            <p className="eyebrow">{t("BUILT WITH PURPOSE", "بُني لهدف")}</p>
            <h2>
              {t("A graduation project.", "مشروع تخرج.")}
              <br />
              {t("A practical question.", "سؤال عملي.")}
            </h2>
          </div>
          <div>
            <p>
              {t(
                "How can we make everyday food choices more informed? Health Tailor explores that question through a full-stack application with a transparent, hands-on demo.",
                "كيف نجعل اختيارات الطعام اليومية أكثر وعياً؟ يستكشف هيلث تيلور هذا السؤال من خلال تطبيق متكامل وعرض تجريبي تفاعلي.",
              )}
            </p>
            <a
              className="quiet-link"
              href="https://github.com/MuhammadBilal0021/Health-Tailor"
            >
              {t("Explore the engineering", "استكشف الجانب التقني")}
              <ArrowUpRight size={16} />
            </a>
          </div>
        </section>
      </main>
      <footer className="landing-footer">
        <Link className="brand" href="/">
          <Leaf size={20} />
          Health Tailor
        </Link>
        <span>
          {t(
            "Thoughtful food discovery. Built by Muhammad Bilal.",
            "اكتشاف واعٍ للطعام. تطوير محمد بلال.",
          )}
        </span>
        <span>Next.js · TypeScript · FastAPI</span>
      </footer>
    </div>
  );
}
