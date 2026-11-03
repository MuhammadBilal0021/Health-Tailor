"use client";
import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Leaf,
  Check,
  ShieldCheck,
  Wallet,
  Sparkles,
  Upload,
  ArrowUpRight,
  ArrowRight,
} from "lucide-react";
import { useStore } from "@/lib/store";
import { formatMoney, type Role } from "@/lib/types";
import { Heading, tags, tagAr } from "./view-shared";
import { FoodArt } from "./food-art";
export function Profile() {
  const s = useStore();
  const { t, state, busy } = s;
  const [name, setName] = useState(state.user.name);
  const [preferences, setPreferences] = useState(state.user.preferences);
  const [notes, setNotes] = useState(state.user.considerations);
  return (
    <>
      <Heading
        title={t("A place for your preferences.", "مكان لتفضيلاتك.")}
        description={t(
          "A little about you helps make discovery more relevant.",
          "قليل من المعلومات يجعل الاكتشاف أقرب إليك.",
        )}
      />
      <form
        className="panel profile-form"
        onSubmit={(e) => {
          e.preventDefault();
          void s.profile(name, preferences, notes);
        }}
      >
        <label>
          {t("Your name", "اسمك")}
          <input
            required
            minLength={2}
            maxLength={100}
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </label>
        <fieldset>
          <legend>{t("What sounds good?", "ما الذي تفضله؟")}</legend>
          <p className="muted">
            {t(
              "Preference filters, not medical recommendations.",
              "فلاتر تفضيلات وليست توصيات طبية.",
            )}
          </p>
          <div className="preference-grid">
            {tags.map((tag) => (
              <label
                className={
                  "preference " + (preferences.includes(tag) ? "checked" : "")
                }
                key={tag}
              >
                <input
                  type="checkbox"
                  checked={preferences.includes(tag)}
                  onChange={(e) =>
                    setPreferences(
                      e.target.checked
                        ? [...preferences, tag]
                        : preferences.filter((x) => x !== tag),
                    )
                  }
                />
                <Leaf size={18} />
                <span>{t(tag, tagAr[tag])}</span>
              </label>
            ))}
          </div>
        </fieldset>
        <label>
          {t("Optional dietary considerations", "اعتبارات غذائية اختيارية")}
          <textarea
            maxLength={500}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder={t(
              "Use fictional information in the demo.",
              "استخدم معلومات خيالية في العرض.",
            )}
          />
        </label>
        <div className="info-note">
          <ShieldCheck size={22} />
          <p>
            {t(
              "Your profile is sent to the AI provider only when you consent to a request in Meal explorer.",
              "تُرسل بيانات ملفك إلى مزود الذكاء الاصطناعي فقط عند الموافقة على الطلب.",
            )}
          </p>
        </div>
        <button className="button" disabled={busy}>
          {t("Save preferences", "حفظ التفضيلات")}
          <Check size={17} />
        </button>
      </form>
    </>
  );
}
export function WalletPanel() {
  const s = useStore();
  const { state, t, locale, busy, live } = s;
  const [amount, setAmount] = useState("100");
  return (
    <>
      <Heading
        title={t("A little credit. A good meal.", "قليل من الرصيد. وجبة جيدة.")}
        description={t(
          "Track orders, refunds and approved credit.",
          "تابع الطلبات والمبالغ المستردة والرصيد المعتمد.",
        )}
      />
      <div className="two-column">
        <div>
          <section className="balance-card">
            <Wallet size={28} />
            <p>{t("Available balance", "الرصيد المتاح")}</p>
            <h2>{formatMoney(state.user.balance, locale)}</h2>
            <span>
              {t(
                "Prototype ledger · No real payments",
                "سجل تجريبي · لا مدفوعات فعلية",
              )}
            </span>
          </section>
          <section className="panel ledger-panel">
            <h2>{t("Recent activity", "النشاط الأخير")}</h2>
            {state.ledger.length ? (
              state.ledger.map((entry) => (
                <div className="ledger-line" key={entry.id}>
                  <span>
                    {entry.description}
                    <small>
                      {new Date(entry.createdAt).toLocaleDateString()}
                    </small>
                  </span>
                  <strong className={entry.amount > 0 ? "positive" : ""}>
                    {entry.amount > 0 ? "+" : ""}
                    {formatMoney(entry.amount, locale)}
                  </strong>
                </div>
              ))
            ) : (
              <p className="muted">
                {t(
                  "Your first order will appear here.",
                  "سيظهر طلبك الأول هنا.",
                )}
              </p>
            )}
          </section>
        </div>
        <div>
          <form
            className="panel"
            onSubmit={(e) => {
              e.preventDefault();
              void s.recharge(Math.round(Number(amount) * 100));
            }}
          >
            <h2>{t("Request credit", "طلب رصيد")}</h2>
            <p className="muted">
              {live
                ? t(
                    "Administrator approval is required. This is not proof of payment.",
                    "موافقة المسؤول مطلوبة. هذا ليس إثبات دفع.",
                  )
                : t(
                    "Submit a request, then switch to Administrator to approve it.",
                    "أرسل طلباً ثم انتقل إلى المسؤول للموافقة.",
                  )}
            </p>
            <label>
              {t("Amount in SAR", "المبلغ بالريال")}
              <input
                type="number"
                min="1"
                max="1000"
                step="0.01"
                required
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
              />
            </label>
            <button className="button full-width" disabled={busy}>
              {t("Submit request", "إرسال الطلب")}
              <ArrowUpRight size={17} />
            </button>
          </form>
          <section className="panel ledger-panel">
            <h2>{t("Your requests", "طلبات الرصيد")}</h2>
            {state.recharges.length ? (
              state.recharges.map((r) => (
                <div className="ledger-line" key={r.id}>
                  <strong>{formatMoney(r.amount, locale)}</strong>
                  <span className={"status status-" + r.status}>
                    {t(
                      r.status,
                      r.status === "pending"
                        ? "قيد الانتظار"
                        : r.status === "approved"
                          ? "موافق عليه"
                          : "مرفوض",
                    )}
                  </span>
                </div>
              ))
            ) : (
              <p className="muted">{t("No requests yet.", "لا توجد طلبات.")}</p>
            )}
          </section>
        </div>
      </div>
    </>
  );
}
export function Insights() {
  const { t, analyze, live } = useStore();
  const [question, setQuestion] = useState("");
  const [consent, setConsent] = useState(false);
  const [image, setImage] = useState<string>();
  const [fileName, setFileName] = useState("");
  const [busy, setBusy] = useState(false);
  const [answer, setAnswer] = useState("");
  const [error, setError] = useState("");
  return (
    <>
      <Heading
        eyebrow={t("CURIOSITY, WITH CONTEXT", "فضول بوعي")}
        title={t("A closer look at your plate.", "نظرة أقرب إلى طبقك.")}
        description={t(
          "Explore food ideas. AI cannot verify allergens or diagnose dietary needs.",
          "استكشف أفكار الطعام. لا يؤكد الذكاء الاصطناعي مسببات الحساسية ولا يشخّص احتياجاتك.",
        )}
      />
      <div className="two-column">
        <form
          className="panel"
          onSubmit={async (e) => {
            e.preventDefault();
            if (!consent) return;
            setBusy(true);
            setError("");
            setAnswer("");
            try {
              setAnswer(await analyze(question, image));
            } catch (err) {
              setError(err instanceof Error ? err.message : "Unavailable");
            } finally {
              setBusy(false);
            }
          }}
        >
          <div className="panel-icon">
            <Sparkles size={22} />
          </div>
          <h2>{t("What’s on your mind?", "ما الذي تود معرفته؟")}</h2>
          <label>
            {t("Your food question", "سؤالك عن الطعام")}
            <textarea
              required
              minLength={3}
              maxLength={1000}
              rows={4}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder={t(
                "What should I ask the kitchen about this dish?",
                "ماذا أسأل المطعم عن هذا الطبق؟",
              )}
            />
          </label>
          <label className="upload-box">
            <Upload size={23} />
            <strong>
              {fileName ||
                t("Add a food photo (optional)", "أضف صورة طعام (اختياري)")}
            </strong>
            <span>PNG, JPEG, WebP · 3 MB</span>
            <input
              aria-label={t("Food image", "صورة الطعام")}
              type="file"
              accept="image/png,image/jpeg,image/webp"
              onChange={(e) => {
                const file = e.target.files?.[0];
                setError("");
                setImage(undefined);
                setFileName("");
                if (!file) return;
                if (
                  file.size > 3_000_000 ||
                  !["image/png", "image/jpeg", "image/webp"].includes(file.type)
                ) {
                  setError(
                    t(
                      "Choose a PNG, JPEG or WebP under 3 MB.",
                      "اختر صورة أصغر من ٣ ميغابايت.",
                    ),
                  );
                  return;
                }
                const reader = new FileReader();
                reader.onload = () => {
                  setImage(String(reader.result).split(",")[1]);
                  setFileName(file.name);
                };
                reader.readAsDataURL(file);
              }}
            />
          </label>
          <label className="consent">
            <input
              type="checkbox"
              required
              checked={consent}
              onChange={(e) => setConsent(e.target.checked)}
            />
            <span>
              {t(
                "I consent to send this request, optional image, and my dietary profile to the AI provider.",
                "أوافق على إرسال الطلب والصورة الاختيارية وملفي الغذائي إلى مزود الذكاء الاصطناعي.",
              )}
            </span>
          </label>
          <button className="button full-width" disabled={busy || !consent}>
            {busy
              ? t("Exploring…", "جارٍ الاستكشاف…")
              : t("Explore this question", "استكشف هذا السؤال")}
            <Sparkles size={17} />
          </button>
          {!live && (
            <p className="fine-print">
              {t(
                "AI is disabled in the browser demo. No data will be sent.",
                "الذكاء الاصطناعي معطل في العرض. لن تُرسل بيانات.",
              )}
            </p>
          )}
        </form>
        <div className="insights-results panel">
          <p className="eyebrow">
            {t("AN INFORMED STARTING POINT", "نقطة بداية واعية")}
          </p>
          {error ? (
            <div className="inline-error" role="alert">
              {error}
            </div>
          ) : answer ? (
            <div className="ai-answer">
              <span className="status">
                {t(
                  "AI estimate · verify details",
                  "تقدير آلي · تحقق من التفاصيل",
                )}
              </span>
              <p>{answer}</p>
            </div>
          ) : (
            <div className="insights-empty">
              <Leaf size={40} />
              <h2>
                {t("Clarity starts with a question.", "الوضوح يبدأ بسؤال.")}
              </h2>
              <p>
                {t(
                  "Ask about possible ingredients, preparation, or questions to discuss with your kitchen or clinician.",
                  "اسأل عن المكونات المحتملة أو التحضير أو ما يمكنك مناقشته مع المطعم أو المختص.",
                )}
              </p>
            </div>
          )}
          <div className="info-note">
            <ShieldCheck size={21} />
            <p>
              {t(
                "No invented nutrition scores or safety guarantees. If AI is unavailable, we’ll tell you.",
                "لا نسب غذائية مختلقة ولا ضمانات سلامة. سنخبرك إن كانت الخدمة غير متاحة.",
              )}
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
export function Login() {
  const s = useStore();
  const { t, busy } = s;
  const [signup, setSignup] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<Role>("customer");
  const router = useRouter();
  return (
    <div className="login-layout">
      <div>
        <p className="eyebrow">
          {t("YOUR PLACE AT THE TABLE", "مكانك على المائدة")}
        </p>
        <h1>
          {t("Good to", "سعداء")}
          <br />
          <em>{t("have you here.", "بوجودك هنا.")}</em>
        </h1>
        <p>
          {t(
            "Save your preferences. Or explore the demo, no sign-up required.",
            "احفظ تفضيلاتك. أو جرّب العرض دون تسجيل.",
          )}
        </p>
        <Link className="quiet-link" href="/explore">
          {t("Continue with the demo", "تابع العرض التجريبي")}
          <ArrowRight size={16} />
        </Link>
        <FoodArt variant={1} />
      </div>
      <form
        className="panel login-form"
        onSubmit={async (e) => {
          e.preventDefault();
          if (await s.login(email, password, signup ? name : undefined, role))
            router.push("/explore");
        }}
      >
        <h2>
          {signup
            ? t("Create your account", "إنشاء حساب")
            : t("Welcome back", "مرحباً بعودتك")}
        </h2>
        <p className="muted">
          {t(
            "Live accounts require the configured backend.",
            "الحسابات الفعلية تحتاج إلى تهيئة الخادم.",
          )}
        </p>
        {signup && (
          <>
            <label>
              {t("Name", "الاسم")}
              <input
                value={name}
                required
                minLength={2}
                maxLength={100}
                onChange={(e) => setName(e.target.value)}
                autoComplete="name"
              />
            </label>
            <label>
              {t("Account type", "نوع الحساب")}
              <select
                value={role}
                onChange={(e) => setRole(e.target.value as Role)}
              >
                <option value="customer">{t("Customer", "عميل")}</option>
                <option value="restaurant">
                  {t("Restaurant owner", "صاحب مطعم")}
                </option>
              </select>
            </label>
          </>
        )}
        <label>
          {t("Email", "البريد الإلكتروني")}
          <input
            type="email"
            autoComplete="email"
            maxLength={254}
            value={email}
            required
            onChange={(e) => setEmail(e.target.value)}
          />
        </label>
        <label>
          {t(
            "Password (at least 10 characters)",
            "كلمة المرور (١٠ أحرف على الأقل)",
          )}
          <input
            type="password"
            minLength={10}
            maxLength={128}
            autoComplete={signup ? "new-password" : "current-password"}
            value={password}
            required
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        <button className="button full-width" disabled={busy}>
          {busy
            ? t("Please wait…", "يرجى الانتظار…")
            : signup
              ? t("Create account", "إنشاء حساب")
              : t("Sign in", "تسجيل الدخول")}
          <ArrowUpRight size={17} />
        </button>
        <button
          type="button"
          className="text-button centered"
          onClick={() => setSignup(!signup)}
        >
          {signup
            ? t("Already have an account? Sign in", "لديك حساب؟ سجل الدخول")
            : t("New here? Create an account", "جديد هنا؟ أنشئ حساباً")}
        </button>
      </form>
    </div>
  );
}
