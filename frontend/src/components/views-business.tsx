"use client";
import { useState } from "react";
import {
  Store,
  ShieldCheck,
  ClipboardList,
  Wallet,
  Leaf,
  Plus,
  Pencil,
  Check,
} from "lucide-react";
import { useStore } from "@/lib/store";
import { formatMoney, type Dish, type Restaurant } from "@/lib/types";
import { Heading, Empty, Modal, OrderCard, tags, tagAr } from "./view-shared";
import { FoodArt } from "./food-art";
export function Kitchen() {
  const s = useStore();
  const { state, t, locale, busy, live } = s;
  const [tab, setTab] = useState("orders");
  const [editing, setEditing] = useState<Dish | null>(null);
  const [creating, setCreating] = useState(false);
  const kitchen = state.restaurants.find(
    (r) => r.id === (state.user.restaurantId || "r1"),
  );
  if (live && state.user.role !== "restaurant")
    return (
      <Empty
        icon={<Store size={30} />}
        title={t("Restaurant account required", "حساب مطعم مطلوب")}
        text={t(
          "Sign in with a restaurant account to manage your kitchen.",
          "سجل الدخول بحساب مطعم لإدارة مطبخك.",
        )}
      />
    );
  if (!kitchen) return null;
  const orders = state.orders.filter((o) => o.restaurantId === kitchen.id);
  const dishes = state.dishes.filter((d) => d.restaurantId === kitchen.id);
  return (
    <>
      <Heading
        eyebrow={t("BEHIND THE COUNTER", "خلف المنضدة")}
        title={locale === "ar" ? kitchen.nameAr || kitchen.name : kitchen.name}
        description={t(
          "Keep your menu fresh and every order moving.",
          "حدّث قائمتك وتابع كل طلب.",
        )}
        action={
          <span
            className={
              "status " +
              (kitchen.approved ? "status-delivered" : "status-pending")
            }
          >
            {kitchen.approved
              ? t("Approved kitchen", "مطعم معتمد")
              : t("Awaiting approval", "بانتظار الموافقة")}
          </span>
        }
      />
      {!live && (
        <label className="panel">
          {t("Demo kitchen", "المطعم التجريبي")}
          <select
            value={kitchen.id}
            onChange={(e) => {
              s.role("restaurant", e.target.value);
              setTab("orders");
            }}
          >
            {state.restaurants.map((r) => (
              <option key={r.id} value={r.id}>
                {locale === "ar" ? r.nameAr || r.name : r.name}
              </option>
            ))}
          </select>
        </label>
      )}
      <div className="stat-grid">
        <div className="stat">
          <ClipboardList size={21} />
          <span>{t("Active orders", "الطلبات النشطة")}</span>
          <strong>
            {
              orders.filter(
                (o) => !["delivered", "cancelled"].includes(o.status),
              ).length
            }
          </strong>
        </div>
        <div className="stat">
          <Leaf size={21} />
          <span>{t("Menu items", "أطباق القائمة")}</span>
          <strong>{dishes.length}</strong>
        </div>
        <div className="stat">
          <Wallet size={21} />
          <span>{t("Settled revenue", "الإيراد المسوّى")}</span>
          <strong>
            {formatMoney(
              live
                ? state.restaurantBalance
                : orders
                    .filter((o) => o.settled)
                    .reduce((sum, o) => sum + o.subtotal, 0),
              locale,
            )}
          </strong>
        </div>
      </div>
      <div className="tab-row">
        {[
          ["orders", "Orders", "الطلبات"],
          ["menu", "Menu", "القائمة"],
          ["profile", "Kitchen profile", "ملف المطعم"],
          ["reviews", "Reviews", "المراجعات"],
        ].map(([key, en, ar]) => (
          <button
            key={key}
            className={tab === key ? "active" : ""}
            onClick={() => setTab(key)}
          >
            {t(en, ar)}
          </button>
        ))}
      </div>
      {tab === "orders" &&
        (orders.length ? (
          <div className="order-grid">
            {orders.map((o) => (
              <OrderCard key={o.id} order={o} manage />
            ))}
          </div>
        ) : (
          <Empty
            icon={<ClipboardList size={28} />}
            title={t("The kitchen is all caught up", "المطبخ جاهز للطلبات")}
            text={t(
              "New orders will appear here. In demo mode, place an order as a customer first.",
              "ستظهر الطلبات هنا. في العرض، قدّم طلباً كعميل أولاً.",
            )}
          />
        ))}
      {tab === "menu" && (
        <section className="panel">
          <div className="section-heading">
            <h2>{t("Your menu", "قائمتك")}</h2>
            <button
              className="button small-button"
              onClick={() => {
                setCreating(true);
                setEditing({
                  id: crypto.randomUUID(),
                  restaurantId: kitchen.id,
                  name: "",
                  nameAr: "",
                  description: "",
                  descriptionAr: "",
                  price: 3000,
                  tags: [],
                  ingredients: [],
                  allergens: [],
                  available: true,
                  art: 0,
                });
              }}
            >
              <Plus size={16} />
              {t("Add dish", "إضافة طبق")}
            </button>
          </div>
          {dishes.map((d) => (
            <div className="menu-line" key={d.id}>
              <div className="menu-art">
                <FoodArt variant={d.art} />
              </div>
              <div>
                <h3>{locale === "ar" ? d.nameAr || d.name : d.name}</h3>
                <span>{formatMoney(d.price, locale)}</span>
              </div>
              <button
                className={"availability " + (d.available ? "on" : "")}
                disabled={busy}
                onClick={() =>
                  void s.saveDish({ ...d, available: !d.available })
                }
              >
                {d.available ? t("Available", "متاح") : t("Hidden", "مخفي")}
              </button>
              <button
                className="icon-button"
                aria-label={t("Edit dish", "تعديل الطبق")}
                onClick={() => {
                  setCreating(false);
                  setEditing(d);
                }}
              >
                <Pencil size={17} />
              </button>
            </div>
          ))}
        </section>
      )}
      {tab === "profile" && (
        <KitchenProfile key={kitchen.id} kitchen={kitchen} />
      )}{" "}
      {tab === "reviews" && (
        <section className="panel">
          <h2>{t("From your customers", "من عملائك")}</h2>
          {state.reviews.filter((r) => r.restaurantId === kitchen.id).length ? (
            state.reviews
              .filter((r) => r.restaurantId === kitchen.id)
              .map((r) => (
                <article className="review-item" key={r.id}>
                  <strong>{r.name}</strong>
                  <span>{"★".repeat(r.rating)}</span>
                  <p>{r.comment}</p>
                </article>
              ))
          ) : (
            <p className="muted">
              {t(
                "Reviews appear after delivered orders.",
                "تظهر المراجعات بعد توصيل الطلبات.",
              )}
            </p>
          )}
        </section>
      )}
      {editing && (
        <DishEditor
          dish={editing}
          creating={creating}
          close={() => setEditing(null)}
        />
      )}
    </>
  );
}
function KitchenProfile({ kitchen }: { kitchen: Restaurant }) {
  const s = useStore();
  const { t, busy } = s;
  const [form, setForm] = useState(kitchen);
  return (
    <form
      className="panel profile-form"
      onSubmit={(e) => {
        e.preventDefault();
        void s.saveKitchen(form);
      }}
    >
      <h2>{t("Your kitchen’s story", "قصة مطعمك")}</h2>
      {(
        [
          ["name", "Kitchen name", "اسم المطعم"],
          ["nameAr", "Arabic name", "الاسم العربي"],
          ["city", "City", "المدينة"],
          ["cuisine", "Cuisine", "نوع المطبخ"],
          ["description", "Description", "الوصف"],
          ["descriptionAr", "Arabic description", "الوصف العربي"],
        ] as const
      ).map(([key, en, ar]) => (
        <label key={key}>
          {t(en, ar)}
          <input
            required={key === "name" || key === "city" || key === "cuisine"}
            maxLength={key.includes("description") ? 500 : 100}
            value={form[key]}
            onChange={(e) => setForm({ ...form, [key]: e.target.value })}
          />
        </label>
      ))}
      <button className="button" disabled={busy}>
        {t("Save profile", "حفظ الملف")}
        <Check size={16} />
      </button>
    </form>
  );
}
function DishEditor({
  dish,
  creating,
  close,
}: {
  dish: Dish;
  creating: boolean;
  close: () => void;
}) {
  const s = useStore();
  const { t, busy } = s;
  const [form, setForm] = useState(dish);
  const [ingredients, setIngredients] = useState(dish.ingredients.join(", "));
  const [allergens, setAllergens] = useState(dish.allergens.join(", "));
  return (
    <Modal title={t("Edit dish", "تعديل الطبق")} close={close}>
      <form
        className="modal-content dish-editor"
        onSubmit={async (e) => {
          e.preventDefault();
          if (
            await s.saveDish(
              {
                ...form,
                ingredients: ingredients
                  .split(",")
                  .map((x) => x.trim())
                  .filter(Boolean),
                allergens: allergens
                  .split(",")
                  .map((x) => x.trim())
                  .filter(Boolean),
              },
              creating,
            )
          )
            close();
        }}
      >
        <h2>
          {creating
            ? t("Something new on the menu", "طبق جديد في القائمة")
            : t("Refine your dish", "حدّث طبقك")}
        </h2>
        <div className="form-grid">
          {(
            [
              ["name", "Name", "الاسم"],
              ["nameAr", "Arabic name", "الاسم العربي"],
              ["description", "Description", "الوصف"],
              ["descriptionAr", "Arabic description", "الوصف العربي"],
            ] as const
          ).map(([key, en, ar]) => (
            <label key={key}>
              {t(en, ar)}
              <input
                required={key === "name"}
                maxLength={key.includes("description") ? 500 : 100}
                value={form[key]}
                onChange={(e) => setForm({ ...form, [key]: e.target.value })}
              />
            </label>
          ))}
          <label>
            {t("Price (SAR)", "السعر (ريال)")}
            <input
              type="number"
              min="1"
              max="1000"
              step="0.01"
              required
              value={form.price / 100}
              onChange={(e) =>
                setForm({
                  ...form,
                  price: Math.round(Number(e.target.value) * 100),
                })
              }
            />
          </label>
          <label>
            {t("Illustration", "الرسم")}
            <select
              value={form.art}
              onChange={(e) =>
                setForm({ ...form, art: Number(e.target.value) })
              }
            >
              {[0, 1, 2, 3, 4, 5].map((n) => (
                <option key={n} value={n}>
                  {n + 1}
                </option>
              ))}
            </select>
          </label>
        </div>
        <label>
          {t("Ingredients, separated by commas", "المكونات، مفصولة بفواصل")}
          <input
            value={ingredients}
            maxLength={500}
            onChange={(e) => setIngredients(e.target.value)}
          />
        </label>
        <label>
          {t(
            "Allergens, separated by commas",
            "مسببات الحساسية، مفصولة بفواصل",
          )}
          <input
            value={allergens}
            maxLength={500}
            onChange={(e) => setAllergens(e.target.value)}
          />
        </label>
        <fieldset>
          <legend>{t("Menu tags", "تصنيفات الطبق")}</legend>
          <div className="filter-row">
            {tags.map((tag) => (
              <label className="checkbox-tag" key={tag}>
                <input
                  type="checkbox"
                  checked={form.tags.includes(tag)}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      tags: e.target.checked
                        ? [...form.tags, tag]
                        : form.tags.filter((x) => x !== tag),
                    })
                  }
                />
                {t(tag, tagAr[tag])}
              </label>
            ))}
          </div>
        </fieldset>
        <button className="button full-width" disabled={busy}>
          {t("Save dish", "حفظ الطبق")}
          <Check size={16} />
        </button>
      </form>
    </Modal>
  );
}
export function Admin() {
  const s = useStore();
  const { t, state, locale, busy, live } = s;
  if (live && state.user.role !== "admin")
    return (
      <Empty
        icon={<ShieldCheck size={30} />}
        title={t("Administrator account required", "حساب مسؤول مطلوب")}
        text={t(
          "This workspace is restricted to administrators.",
          "هذه المساحة متاحة للمسؤولين فقط.",
        )}
      />
    );
  const pending = state.recharges.filter((r) => r.status === "pending");
  return (
    <>
      <Heading
        eyebrow={t("KEEPING THINGS IN ORDER", "تنظيم العمل")}
        title={t("A thoughtful overview.", "نظرة شاملة بعناية.")}
        description={t(
          "Review kitchens and credit requests with clear, deliberate actions.",
          "راجع المطاعم وطلبات الرصيد بإجراءات واضحة.",
        )}
      />
      <div className="stat-grid">
        <div className="stat">
          <Store size={21} />
          <span>{t("Kitchens", "المطاعم")}</span>
          <strong>{state.restaurants.length}</strong>
        </div>
        <div className="stat">
          <Wallet size={21} />
          <span>{t("Pending requests", "الطلبات المعلقة")}</span>
          <strong>{pending.length}</strong>
        </div>
        <div className="stat">
          <ClipboardList size={21} />
          <span>{t("Orders", "الطلبات")}</span>
          <strong>{state.orders.length}</strong>
        </div>
      </div>
      <div className="info-note">
        <ShieldCheck size={22} />
        <p>
          {t(
            "Prototype ledger: approving credit does not verify a payment or trigger a bank transfer.",
            "سجل تجريبي: الموافقة على الرصيد لا تتحقق من دفع ولا تنفذ تحويلاً بنكياً.",
          )}
        </p>
      </div>
      <section className="panel">
        <h2>{t("Credit requests", "طلبات الرصيد")}</h2>
        {pending.length ? (
          pending.map((r) => (
            <div className="admin-line" key={r.id}>
              <div>
                <strong>{formatMoney(r.amount, locale)}</strong>
                <small>
                  {t("Customer", "العميل")} · {r.userId.slice(0, 12)}
                </small>
              </div>
              <div className="button-group">
                <button
                  className="button small-button"
                  disabled={busy}
                  onClick={() => void s.decide(r.id, true)}
                >
                  <Check size={15} />
                  {t("Approve", "موافقة")}
                </button>
                <button
                  className="button outline small-button"
                  disabled={busy}
                  onClick={() => void s.decide(r.id, false)}
                >
                  {t("Reject", "رفض")}
                </button>
              </div>
            </div>
          ))
        ) : (
          <p className="muted">
            {t(
              "No requests waiting for review.",
              "لا توجد طلبات بانتظار المراجعة.",
            )}
          </p>
        )}
      </section>
      <section className="panel ledger-panel">
        <h2>{t("Kitchen directory", "دليل المطاعم")}</h2>
        {state.restaurants.map((r) => (
          <div className="admin-line" key={r.id}>
            <div>
              <strong>{locale === "ar" ? r.nameAr || r.name : r.name}</strong>
              <small>
                {r.city} · {r.cuisine}
              </small>
            </div>
            <button
              className={"button small-button " + (r.approved ? "outline" : "")}
              disabled={busy}
              onClick={() => void s.approveKitchen(r.id, !r.approved)}
            >
              {r.approved
                ? t("Pause kitchen", "إيقاف المطعم")
                : t("Approve kitchen", "اعتماد المطعم")}
            </button>
          </div>
        ))}
      </section>
    </>
  );
}
