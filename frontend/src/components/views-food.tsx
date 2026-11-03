"use client";
import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Search,
  SlidersHorizontal,
  Plus,
  Minus,
  ArrowUpRight,
  ArrowRight,
  Leaf,
  MapPin,
  ShoppingBag,
  X,
  ShieldCheck,
  Wallet,
  ClipboardList,
} from "lucide-react";
import { useStore } from "@/lib/store";
import { formatMoney, type Dish } from "@/lib/types";
import { totals } from "@/lib/domain";
import { FoodArt } from "./food-art";
import { Heading, Empty, Modal, OrderCard, tags, tagAr } from "./view-shared";
export function Explore() {
  const s = useStore();
  const { state, t, locale, busy } = s;
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("All");
  const [kitchen, setKitchen] = useState("all");
  const [selected, setSelected] = useState<Dish | null>(null);
  const dishes = state.dishes
    .filter(
      (d) =>
        d.available &&
        state.restaurants.find((r) => r.id === d.restaurantId)?.approved,
    )
    .filter((d) =>
      [d.name, d.nameAr, d.description, ...d.ingredients]
        .join(" ")
        .toLowerCase()
        .includes(query.toLowerCase()),
    )
    .filter((d) => filter === "All" || d.tags.includes(filter))
    .filter((d) => kitchen === "all" || d.restaurantId === kitchen);
  const preferred = [...dishes].sort(
    (a, b) =>
      b.tags.filter((x) => state.user.preferences.includes(x)).length -
      a.tags.filter((x) => state.user.preferences.includes(x)).length,
  );
  return (
    <>
      <Heading
        eyebrow={t("YOUR NEXT GOOD MEAL", "وجبتك الجيدة القادمة")}
        title={t("A little more you.", "وجبة أقرب إليك.")}
        description={t(
          "Thoughtful dishes from independent kitchens. Find something that fits your day.",
          "أطباق بعناية من مطاعم مستقلة. اختر ما يناسب يومك.",
        )}
        action={
          <span className="location">
            <MapPin size={15} />
            {t("Riyadh · Sample kitchens", "الرياض · مطاعم تجريبية")}
          </span>
        }
      />
      <section className="discovery-banner">
        <div>
          <span className="eyebrow">
            <Leaf size={13} />
            {t("GOOD FOOD STARTS WITH YOU", "الطعام الجيد يبدأ بك")}
          </span>
          <h2>
            {t("Your preferences.", "تفضيلاتك.")}
            <br />
            <em>{t("A better starting point.", "بداية أفضل.")}</em>
          </h2>
          <p>
            {t(
              "Tell us what you enjoy. We’ll bring matching dishes to the top.",
              "أخبرنا بما تحب لنعرض الأطباق الموافقة أولاً.",
            )}
          </p>
          <Link className="quiet-link" href="/profile">
            {t("Personalise your profile", "خصص ملفك")}
            <ArrowUpRight size={16} />
          </Link>
        </div>
        <FoodArt variant={4} />
        <div className="banner-stamp">
          {t("Made for", "مصمم")}
          <br />
          {t("your everyday.", "ليومك.")}
        </div>
      </section>
      <div className="section-heading">
        <div>
          <h2>{t("Find your flavour", "اكتشف نكهتك")}</h2>
          <p>
            {t(
              "Menu details come from kitchens. Always confirm allergens.",
              "تفاصيل القائمة من المطاعم. تأكد دائماً من مسببات الحساسية.",
            )}
          </p>
        </div>
        <span className="result-count">
          {dishes.length} {t("dishes", "أطباق")}
        </span>
      </div>
      <div className="search-row">
        <label className="search-field">
          <Search size={18} />
          <input
            aria-label={t(
              "Search dishes or ingredients",
              "ابحث عن أطباق أو مكونات",
            )}
            placeholder={t(
              "A dish, an ingredient, a little inspiration…",
              "طبق، مكوّن، قليل من الإلهام…",
            )}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          {query && (
            <button
              className="icon-button"
              onClick={() => setQuery("")}
              aria-label={t("Clear search", "مسح البحث")}
            >
              <X size={15} />
            </button>
          )}
        </label>
        <label className="kitchen-select">
          <SlidersHorizontal size={16} />
          <select
            aria-label={t("Filter by kitchen", "تصفية حسب المطعم")}
            value={kitchen}
            onChange={(e) => setKitchen(e.target.value)}
          >
            <option value="all">{t("All kitchens", "كل المطاعم")}</option>
            {state.restaurants
              .filter((r) => r.approved)
              .map((r) => (
                <option value={r.id} key={r.id}>
                  {locale === "ar" ? r.nameAr || r.name : r.name}
                </option>
              ))}
          </select>
        </label>
      </div>
      <div className="filter-row">
        {["All", ...tags].map((tag) => (
          <button
            className={"filter-chip " + (filter === tag ? "selected" : "")}
            key={tag}
            onClick={() => setFilter(tag)}
          >
            {tag === "All"
              ? t("All dishes", "كل الأطباق")
              : locale === "ar"
                ? tagAr[tag]
                : tag}
          </button>
        ))}
      </div>
      {preferred.length ? (
        <div className="dish-grid">
          {preferred.map((d) => {
            const r = state.restaurants.find((r) => r.id === d.restaurantId);
            return (
              <article className="dish-card" key={d.id}>
                <button
                  className={"dish-art art-" + d.art}
                  onClick={() => setSelected(d)}
                  aria-label={
                    t("View details for ", "عرض تفاصيل ") +
                    (locale === "ar" ? d.nameAr : d.name)
                  }
                >
                  <FoodArt variant={d.art} />
                  {d.tags.some((x) => state.user.preferences.includes(x)) && (
                    <span className="match-badge">
                      <Leaf size={11} />
                      {t("Preference match", "يوافق تفضيلاتك")}
                    </span>
                  )}
                </button>
                <div className="dish-info">
                  <span className="kitchen-name">
                    {locale === "ar" ? r?.nameAr : r?.name}
                  </span>
                  <button className="dish-title" onClick={() => setSelected(d)}>
                    {locale === "ar" ? d.nameAr || d.name : d.name}
                  </button>
                  <p>
                    {locale === "ar"
                      ? d.descriptionAr || d.description
                      : d.description}
                  </p>
                  <div className="dish-tags">
                    {d.tags.slice(0, 2).map((tag) => (
                      <span key={tag}>
                        {locale === "ar" ? tagAr[tag] || tag : tag}
                      </span>
                    ))}
                  </div>
                  <div className="dish-bottom">
                    <strong>{formatMoney(d.price, locale)}</strong>
                    <button
                      className="add-button"
                      disabled={busy}
                      onClick={() => void s.add(d.id)}
                      aria-label={
                        t("Add ", "أضف ") +
                        (locale === "ar" ? d.nameAr : d.name)
                      }
                    >
                      <Plus size={17} />
                      {t("Add", "أضف")}
                    </button>
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      ) : (
        <Empty
          icon={<Search size={28} />}
          title={t("Nothing on the menu yet", "لا توجد نتائج")}
          text={t(
            "Try another ingredient or remove a filter.",
            "جرّب مكوناً آخر أو أزل أحد الفلاتر.",
          )}
        />
      )}
      {selected && (
        <Modal close={() => setSelected(null)} title={selected.name}>
          <div className={"detail-art art-" + selected.art}>
            <FoodArt variant={selected.art} />
          </div>
          <div className="modal-content">
            <p className="eyebrow">{t("A CLOSER LOOK", "نظرة أقرب")}</p>
            <h2>{locale === "ar" ? selected.nameAr : selected.name}</h2>
            <p>
              {locale === "ar" ? selected.descriptionAr : selected.description}
            </p>
            <h3>{t("Listed ingredients", "المكونات المدرجة")}</h3>
            <div className="dish-tags">
              {selected.ingredients.map((i) => (
                <span key={i}>{i}</span>
              ))}
            </div>
            <div className="info-note">
              <ShieldCheck size={20} />
              <p>
                <strong>{t("Allergen information", "معلومات الحساسية")}</strong>
                <br />
                {selected.allergens.length
                  ? selected.allergens.join(", ")
                  : t(
                      "No allergens listed. This does not guarantee allergen-free preparation.",
                      "لا توجد مسببات مدرجة. هذا لا يضمن خلو التحضير منها.",
                    )}
                <br />
                {t(
                  "Ask the kitchen about cross-contact and portions.",
                  "اسأل المطعم عن التلوث المتبادل وحجم الحصة.",
                )}
              </p>
            </div>
            <button
              className="button full-width"
              disabled={busy}
              onClick={() => void s.add(selected.id)}
            >
              {t("Add to bag", "أضف إلى الحقيبة")} ·{" "}
              {formatMoney(selected.price, locale)}
              <Plus size={18} />
            </button>
          </div>
        </Modal>
      )}
    </>
  );
}
export function Cart() {
  const s = useStore();
  const { state, t, locale, busy, live } = s;
  const [address, setAddress] = useState("");
  const router = useRouter();
  const cost = totals(state);
  return (
    <>
      <Heading
        title={t("Something good is in your bag.", "شيء لذيذ في حقيبتك.")}
        description={t(
          "Check your selection, then let the kitchen take it from here.",
          "راجع اختياراتك ودع المطعم يتولى الباقي.",
        )}
      />
      {!state.cart.length ? (
        <Empty
          icon={<ShoppingBag size={30} />}
          title={t("Your next meal starts here", "وجبتك القادمة تبدأ هنا")}
          text={t(
            "Your bag is empty. Find a dish you’d love to try.",
            "حقيبتك فارغة. ابحث عن طبق تحب تجربته.",
          )}
          href="/explore"
        />
      ) : (
        <div className="two-column">
          <div className="panel">
            <h2>{t("Your selection", "اختياراتك")}</h2>
            {state.cart.map((item) => {
              const d = state.dishes.find((d) => d.id === item.dishId);
              if (!d) return null;
              return (
                <div className="cart-line" key={d.id}>
                  <div className="cart-art">
                    <FoodArt variant={d.art} />
                  </div>
                  <div className="cart-description">
                    <h3>{locale === "ar" ? d.nameAr : d.name}</h3>
                    <span>{formatMoney(d.price, locale)}</span>
                    <div className="quantity-control">
                      <button
                        disabled={busy}
                        onClick={() => s.quantity(d.id, item.quantity - 1)}
                        aria-label={t("Decrease quantity", "تقليل الكمية")}
                      >
                        <Minus size={14} />
                      </button>
                      <span>{item.quantity}</span>
                      <button
                        disabled={busy}
                        onClick={() => s.quantity(d.id, item.quantity + 1)}
                        aria-label={t("Increase quantity", "زيادة الكمية")}
                      >
                        <Plus size={14} />
                      </button>
                    </div>
                  </div>
                  <strong>
                    {formatMoney(d.price * item.quantity, locale)}
                  </strong>
                </div>
              );
            })}
            <Link className="quiet-link" href="/explore">
              {t("Add something else", "أضف شيئاً آخر")}
              <Plus size={15} />
            </Link>
          </div>
          <form
            className="panel checkout-panel"
            onSubmit={async (e) => {
              e.preventDefault();
              if (await s.placeOrder(address)) router.push("/orders");
            }}
          >
            <p className="eyebrow">
              {t("THE FINISHING TOUCH", "الخطوة الأخيرة")}
            </p>
            <h2>{t("Order summary", "ملخص الطلب")}</h2>
            <div className="summary-line">
              <span>{t("Dishes", "الأطباق")}</span>
              <span>{formatMoney(cost.subtotal, locale)}</span>
            </div>
            <div className="summary-line">
              <span>{t("Delivery", "التوصيل")}</span>
              <span>{formatMoney(cost.delivery, locale)}</span>
            </div>
            <div className="summary-line total">
              <strong>{t("Total", "الإجمالي")}</strong>
              <strong>{formatMoney(cost.total, locale)}</strong>
            </div>
            <label>
              {t("Delivery address", "عنوان التوصيل")}
              <textarea
                required
                minLength={5}
                maxLength={300}
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                placeholder={
                  live
                    ? t("Street, building, city", "الشارع والمبنى والمدينة")
                    : t(
                        "Use a fictional address for the demo",
                        "استخدم عنواناً خيالياً للعرض",
                      )
                }
              />
            </label>
            <p className="wallet-hint">
              <Wallet size={16} />
              {t("Available credit", "الرصيد المتاح")}:{" "}
              {formatMoney(state.user.balance, locale)}
            </p>
            <button className="button full-width" disabled={busy}>
              {busy
                ? t("Placing order…", "جارٍ الطلب…")
                : t("Place order", "إتمام الطلب")}
              <ArrowRight size={17} />
            </button>
            <p className="fine-print">
              {t(
                "Prototype wallet credit. No bank transaction is made.",
                "رصيد محفظة تجريبي. لا تُنفذ معاملة بنكية.",
              )}
            </p>
          </form>
        </div>
      )}
    </>
  );
}
export function Orders() {
  const { state, t } = useStore();
  return (
    <>
      <Heading
        title={t("From kitchen to doorstep.", "من المطبخ إلى بابك.")}
        description={t(
          "Every order, every update, all in one place.",
          "كل طلب وكل تحديث في مكان واحد.",
        )}
      />
      {state.orders.length ? (
        <div className="order-grid">
          {state.orders.map((o) => (
            <OrderCard order={o} key={o.id} />
          ))}
        </div>
      ) : (
        <Empty
          icon={<ClipboardList size={30} />}
          title={t("Your story is still cooking", "حكايتك لم تبدأ بعد")}
          text={t(
            "Place your first order and follow its journey here.",
            "قدّم طلبك الأول وتابع رحلته هنا.",
          )}
          href="/explore"
        />
      )}
    </>
  );
}
