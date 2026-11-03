"use client";
import Link from "next/link";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { X, Star, Check } from "lucide-react";
import { useStore } from "@/lib/store";
import { formatMoney, statusAr, statusSequence, type Order } from "@/lib/types";
import { transitions } from "@/lib/domain";
export const tags = [
  "Plant-based",
  "Protein-focused",
  "Mild",
  "Gluten-free ingredients",
  "Spicy",
];
export const tagAr: Record<string, string> = {
  "Plant-based": "نباتي",
  "Protein-focused": "غني بالبروتين",
  Mild: "قليل التوابل",
  "Gluten-free ingredients": "مكونات دون غلوتين",
  Spicy: "حار",
};
export function Heading({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow?: string;
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="page-heading">
      <div>
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {action}
    </div>
  );
}
export function Empty({
  icon,
  title,
  text,
  href,
}: {
  icon: ReactNode;
  title: string;
  text: string;
  href?: string;
}) {
  const { t } = useStore();
  return (
    <div className="empty-state">
      <span className="empty-icon">{icon}</span>
      <h2>{title}</h2>
      <p>{text}</p>
      {href && (
        <Link className="button" href={href}>
          {t("Explore the menu", "استكشف القائمة")} →
        </Link>
      )}
    </div>
  );
}
export function Modal({
  children,
  close,
  title,
}: {
  children: ReactNode;
  close: () => void;
  title: string;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const { t } = useStore();
  useEffect(() => {
    ref.current?.showModal();
    return () => ref.current?.close();
  }, []);
  return (
    <dialog
      className="modal"
      ref={ref}
      onCancel={close}
      onClick={(e) => {
        if (e.target === e.currentTarget) close();
      }}
      aria-label={title}
    >
      <button
        className="modal-close icon-button"
        onClick={close}
        aria-label={t("Close", "إغلاق")}
      >
        <X size={20} />
      </button>
      {children}
    </dialog>
  );
}
export function OrderCard({
  order,
  manage = false,
}: {
  order: Order;
  manage?: boolean;
}) {
  const s = useStore();
  const { t, locale, busy, state } = s;
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");
  const [reviewing, setReviewing] = useState(false);
  const r = state.restaurants.find((r) => r.id === order.restaurantId);
  return (
    <article className="panel order-card">
      <div className="order-heading">
        <div>
          <span className="eyebrow">
            HT-{order.id.slice(0, 8).toUpperCase()}
          </span>
          <h3>{locale === "ar" ? r?.nameAr : r?.name}</h3>
          <small>
            {new Date(order.createdAt).toLocaleDateString(
              locale === "ar" ? "ar-SA" : "en-GB",
            )}
          </small>
        </div>
        <span className={"status status-" + order.status}>
          {locale === "ar" ? statusAr[order.status] : order.status}
        </span>
      </div>
      <div className="order-items">
        {order.items.map((item, i) => (
          <p key={i}>
            <span>
              {item.quantity} × {item.name}
            </span>
            <strong>{formatMoney(item.price * item.quantity, locale)}</strong>
          </p>
        ))}
      </div>
      {order.status !== "cancelled" && (
        <div
          className="order-progress"
          aria-label={t("Order progress", "تقدم الطلب")}
        >
          {statusSequence.map((status, i) => (
            <div
              key={status}
              className={
                statusSequence.indexOf(order.status) >= i ? "done" : ""
              }
            >
              <span>
                {statusSequence.indexOf(order.status) > i ? (
                  <Check size={12} />
                ) : (
                  i + 1
                )}
              </span>
              <small>{locale === "ar" ? statusAr[status] : status}</small>
            </div>
          ))}
        </div>
      )}
      <div className="order-actions">
        <strong>{formatMoney(order.total, locale)}</strong>
        {manage ? (
          transitions[order.status].map((status) => (
            <button
              key={status}
              disabled={busy}
              className={
                status === "cancelled"
                  ? "text-button danger"
                  : "button small-button"
              }
              onClick={() => void s.status(order.id, status)}
            >
              {t(
                {
                  confirmed: "Confirm order",
                  preparing: "Start preparing",
                  ready: "Mark ready",
                  delivered: "Mark delivered",
                  cancelled: "Cancel & refund",
                  pending: "Pending",
                }[status],
                {
                  confirmed: "تأكيد الطلب",
                  preparing: "بدء التحضير",
                  ready: "جاهز للتوصيل",
                  delivered: "تم التوصيل",
                  cancelled: "إلغاء واسترداد",
                  pending: "قيد الانتظار",
                }[status],
              )}
            </button>
          ))
        ) : ["pending", "confirmed"].includes(order.status) ? (
          <button
            className="text-button danger"
            disabled={busy}
            onClick={() => void s.status(order.id, "cancelled")}
          >
            {t("Cancel & refund", "إلغاء واسترداد")}
          </button>
        ) : (
          order.status === "delivered" &&
          !state.reviews.some((r) => r.orderId === order.id) && (
            <button
              className="text-button"
              onClick={() => setReviewing(!reviewing)}
            >
              <Star size={15} />
              {t("Leave a review", "أضف مراجعة")}
            </button>
          )
        )}
      </div>
      {reviewing && !state.reviews.some((r) => r.orderId === order.id) && (
        <form
          className="review-form"
          onSubmit={(e) => {
            e.preventDefault();
            void s.review(order.id, rating, comment);
          }}
        >
          <label>
            {t("Rating", "التقييم")}
            <select
              value={rating}
              onChange={(e) => setRating(Number(e.target.value))}
            >
              {[5, 4, 3, 2, 1].map((n) => (
                <option key={n} value={n}>
                  {n} / 5
                </option>
              ))}
            </select>
          </label>
          <label>
            {t("Your review", "مراجعتك")}
            <textarea
              value={comment}
              maxLength={500}
              minLength={3}
              required
              onChange={(e) => setComment(e.target.value)}
            />
          </label>
          <button className="button small-button" disabled={busy}>
            {t("Submit review", "إرسال المراجعة")}
          </button>
        </form>
      )}
    </article>
  );
}
