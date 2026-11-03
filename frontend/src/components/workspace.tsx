"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Leaf,
  Search,
  ShoppingBag,
  Utensils,
  ClipboardList,
  Wallet,
  UserRound,
  Sparkles,
  Store,
  ShieldCheck,
  Globe2,
  ArrowUpRight,
  X,
  Menu,
  LogOut,
  RotateCcw,
} from "lucide-react";
import { useStore } from "@/lib/store";
import type { Page, Role } from "@/lib/types";
import {
  Explore,
  Cart,
  Orders,
  Profile,
  WalletPanel,
  Insights,
  Login,
  Kitchen,
  Admin,
} from "./views";
const navigation = [
  ["explore", Utensils, "Discover meals", "اكتشف الوجبات"],
  ["cart", ShoppingBag, "Your bag", "حقيبتك"],
  ["orders", ClipboardList, "Your orders", "طلباتك"],
  ["insights", Sparkles, "Meal explorer", "مستكشف الوجبات"],
  ["wallet", Wallet, "Wallet", "المحفظة"],
  ["profile", UserRound, "Your profile", "ملفك الشخصي"],
] as const;
const titles: Record<string, [string, string]> = {
  explore: ["Discover meals", "اكتشف الوجبات"],
  cart: ["Your bag", "حقيبتك"],
  orders: ["Your orders", "طلباتك"],
  insights: ["Meal explorer", "مستكشف الوجبات"],
  wallet: ["Your wallet", "محفظتك"],
  profile: ["Your profile", "ملفك الشخصي"],
  restaurant: ["Kitchen workspace", "مساحة المطعم"],
  admin: ["Administration", "الإدارة"],
  login: ["Welcome back", "مرحباً بعودتك"],
};
export function Workspace({ page }: { page: Page }) {
  const s = useStore();
  const { t, state, locale, setLocale, live, ready, notice, busy } = s;
  const router = useRouter();
  const [menu, setMenu] = useState(false);
  useEffect(() => {
    if (ready && !live && (page === "restaurant" || page === "admin"))
      s.role(page === "restaurant" ? "restaurant" : "admin");
  }, [page, ready, live]);
  const count = state.cart.reduce((n, i) => n + i.quantity, 0);
  const components = {
    explore: <Explore />,
    cart: <Cart />,
    orders: <Orders />,
    profile: <Profile />,
    wallet: <WalletPanel />,
    insights: <Insights />,
    login: <Login />,
    restaurant: <Kitchen />,
    admin: <Admin />,
    home: null,
  };
  function changeRole(role: Role) {
    s.role(role);
    router.push(
      role === "customer"
        ? "/explore"
        : role === "restaurant"
          ? "/restaurant"
          : "/admin",
    );
  }
  return (
    <div className="workspace">
      <a href="#workspace-main" className="skip-link">
        {t("Skip to content", "انتقل إلى المحتوى")}
      </a>
      {menu && (
        <button
          className="sidebar-backdrop"
          aria-label={t("Close navigation", "إغلاق القائمة")}
          onClick={() => setMenu(false)}
        />
      )}
      <aside className={"sidebar " + (menu ? "open" : "")}>
        <Link href="/" className="brand">
          <span className="brand-icon">
            <Leaf size={21} />
          </span>
          <span>
            Health Tailor
            <small>{t("FOOD, WITH THOUGHT.", "طعام بعناية.")}</small>
          </span>
        </Link>
        <p className="nav-label">{t("YOUR EVERYDAY", "يومك بشكل أفضل")}</p>
        <nav aria-label={t("Application navigation", "قائمة التطبيق")}>
          {navigation.map(([key, Icon, en, ar]) => (
            <Link
              key={key}
              onClick={() => setMenu(false)}
              className={"nav-item " + (page === key ? "active" : "")}
              href={"/" + key}
            >
              <Icon size={18} />
              <span>{t(en, ar)}</span>
              {key === "cart" && count > 0 && <b>{count}</b>}
            </Link>
          ))}
          {(!live || state.user.role === "restaurant") && (
            <Link
              className={"nav-item " + (page === "restaurant" ? "active" : "")}
              href="/restaurant"
            >
              <Store size={18} />
              <span>{t("Kitchen workspace", "مساحة المطعم")}</span>
            </Link>
          )}
          {(!live || state.user.role === "admin") && (
            <Link
              className={"nav-item " + (page === "admin" ? "active" : "")}
              href="/admin"
            >
              <ShieldCheck size={18} />
              <span>{t("Administration", "الإدارة")}</span>
            </Link>
          )}
        </nav>
        <div className="sidebar-bottom">
          {!live ? (
            <div className="demo-role">
              <span>{t("TRY A PERSPECTIVE", "جرّب دوراً")}</span>
              <select
                aria-label={t("Demo role", "الدور التجريبي")}
                value={state.user.role}
                onChange={(e) => changeRole(e.target.value as Role)}
              >
                <option value="customer">{t("Customer", "عميل")}</option>
                <option value="restaurant">{t("Restaurant", "مطعم")}</option>
                <option value="admin">{t("Administrator", "مسؤول")}</option>
              </select>
              <button
                className="text-button"
                onClick={() => {
                  s.reset();
                  router.push("/explore");
                }}
              >
                <RotateCcw size={13} />
                {t("Reset demo", "إعادة ضبط العرض")}
              </button>
            </div>
          ) : (
            <button
              className="text-button"
              disabled={busy}
              onClick={() => void s.logout()}
            >
              <LogOut size={15} />
              {t("Sign out", "تسجيل الخروج")}
            </button>
          )}
          <div className="sidebar-person">
            <span className="avatar">{state.user.name.slice(0, 1)}</span>
            <div>
              <strong>{state.user.name}</strong>
              <small>
                {live
                  ? state.user.email
                  : t("Your personal food space", "مساحتك الشخصية للطعام")}
              </small>
            </div>
          </div>
        </div>
      </aside>
      <div className="workspace-body">
        <header className="workspace-header">
          <div className="header-title">
            <button
              className="icon-button mobile-menu"
              aria-label={t("Open navigation", "فتح القائمة")}
              onClick={() => setMenu(true)}
            >
              <Menu size={21} />
            </button>
            <span>{t(...(titles[page] ?? titles.explore))}</span>
          </div>
          <div className="header-actions">
            <span className={"mode-pill " + (live ? "connected" : "")}>
              {live
                ? t("Connected account", "حساب متصل")
                : t("Interactive demo", "عرض تفاعلي")}
            </span>
            <button
              className="language"
              onClick={() => setLocale(locale === "en" ? "ar" : "en")}
            >
              <Globe2 size={16} />
              {locale === "en" ? "العربية" : "English"}
            </button>
            <Link
              className="header-bag"
              href="/cart"
              aria-label={t("Shopping bag", "حقيبة التسوق")}
            >
              <ShoppingBag size={19} />
              {count > 0 && <b>{count}</b>}
            </Link>
          </div>
        </header>
        {!live && (
          <div className="demo-banner">
            <span>
              {t(
                "A space to explore. Fictional kitchens, browser-only data, and test credit.",
                "مساحة للتجربة. مطاعم خيالية وبيانات في متصفحك ورصيد تجريبي.",
              )}
            </span>
            <Link href="/login">
              {t("Use a real account", "استخدم حساباً فعلياً")}
              <ArrowUpRight size={13} />
            </Link>
          </div>
        )}
        <main id="workspace-main" className="workspace-main">
          {!ready ? (
            <div className="loading" role="status">
              {t("Preparing your table…", "نجهز مائدتك…")}
            </div>
          ) : (
            components[page]
          )}
        </main>
        <footer className="workspace-footer">
          <span>© Health Tailor</span>
          <span>
            {t(
              "AI suggestions are estimates. Confirm ingredients with the kitchen.",
              "اقتراحات الذكاء الاصطناعي تقديرية. تأكد من المكونات مع المطعم.",
            )}
          </span>
        </footer>
      </div>
      {notice && (
        <div className="toast" role="status">
          <span>{notice}</span>
          <button
            className="icon-button"
            onClick={s.clearNotice}
            aria-label={t("Dismiss notification", "إغلاق الإشعار")}
          >
            <X size={16} />
          </button>
        </div>
      )}
    </div>
  );
}
