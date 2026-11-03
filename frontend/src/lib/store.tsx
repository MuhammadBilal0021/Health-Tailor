"use client";
import {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { freshState } from "./seed";
import { addItem, checkout, advanceOrder, approveRecharge } from "./domain";
import type { State, Locale, Role, Status, Dish, Restaurant } from "./types";

type Store = {
  state: State;
  locale: Locale;
  ready: boolean;
  live: boolean;
  busy: boolean;
  notice: string;
  t: (en: string, ar: string) => string;
  setLocale: (l: Locale) => void;
  clearNotice: () => void;
  add: (id: string) => Promise<void>;
  quantity: (id: string, n: number) => void;
  reset: () => void;
  role: (role: Role, kitchenId?: string) => void;
  placeOrder: (address: string) => Promise<boolean>;
  status: (id: string, status: Status) => Promise<void>;
  recharge: (amount: number) => Promise<void>;
  decide: (id: string, approve: boolean) => Promise<void>;
  approveKitchen: (id: string, approve: boolean) => Promise<void>;
  profile: (
    name: string,
    preferences: string[],
    considerations: string,
  ) => Promise<void>;
  saveDish: (dish: Dish, creating?: boolean) => Promise<boolean>;
  saveKitchen: (restaurant: Restaurant) => Promise<void>;
  review: (orderId: string, rating: number, comment: string) => Promise<void>;
  login: (
    email: string,
    password: string,
    name?: string,
    role?: Role,
  ) => Promise<boolean>;
  logout: () => Promise<void>;
  analyze: (question: string, image?: string) => Promise<string>;
};
const Context = createContext<Store | null>(null);
const STORAGE = "health-tailor-demo-v2";
function savedValue(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}
function saveValue(key: string, value: string | null): void {
  try {
    if (value === null) localStorage.removeItem(key);
    else localStorage.setItem(key, value);
  } catch {
    /* Storage is optional; the current session still works. */
  }
}
export function Provider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<State>(freshState);
  const ref = useRef(state);
  const [locale, setLocaleState] = useState<Locale>("en");
  const [ready, setReady] = useState(false);
  const [live, setLive] = useState(false);
  const liveRef = useRef(false);
  const csrf = useRef("");
  const pendingCheckout = useRef<{ signature: string; key: string } | null>(
    null,
  );
  const [busy, setBusy] = useState(false);
  const working = useRef(false);
  const [notice, setNotice] = useState("");
  const commit = (next: State) => {
    ref.current = next;
    setState(next);
  };
  async function api<T>(
    path: string,
    method = "GET",
    body?: unknown,
  ): Promise<T> {
    const response = await fetch("/api" + path, {
      method,
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrf.current,
      },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    const data = await response.json().catch(() => ({
      detail: "The API is unavailable. Check your deployment configuration.",
    }));
    if (!response.ok)
      throw new Error(
        typeof data.detail === "string"
          ? data.detail
          : "Please check the form fields and try again.",
      );
    return data as T;
  }
  async function refresh(clearCart = false) {
    const result = await api<{ csrf: string; state: State }>("/bootstrap");
    csrf.current = result.csrf;
    const cart = clearCart
      ? []
      : ref.current.user.id === result.state.user.id
        ? ref.current.cart
        : [];
    commit({ ...result.state, cart });
  }
  useEffect(() => {
    try {
      const saved = savedValue(STORAGE);
      if (saved) {
        const parsed = JSON.parse(saved) as State;
        if (
          parsed.user?.id === "demo-customer" &&
          [
            "dishes",
            "orders",
            "cart",
            "restaurants",
            "ledger",
            "recharges",
            "reviews",
          ].every((key) =>
            Array.isArray((parsed as unknown as Record<string, unknown>)[key]),
          )
        )
          commit(parsed);
      }
      setLocaleState(savedValue("ht-language") === "ar" ? "ar" : "en");
    } catch {
      /* A broken browser save starts a fresh demo. */
    }
    if (
      process.env.NEXT_PUBLIC_API_ENABLED === "true" &&
      savedValue("ht-live") === "true"
    ) {
      api<{ csrf: string; state: State }>("/bootstrap")
        .then((result) => {
          csrf.current = result.csrf;
          liveRef.current = true;
          setLive(true);
          commit(result.state);
        })
        .catch(() => {
          saveValue("ht-live", null);
        })
        .finally(() => setReady(true));
    } else setReady(true);
    // Initial storage hydration runs once; later writes are below.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  useEffect(() => {
    if (ready && !live) {
      try {
        localStorage.setItem(STORAGE, JSON.stringify(state));
      } catch {
        setNotice(
          "Browser storage is full. Changes will last only for this visit.",
        );
      }
    }
  }, [state, ready, live]);
  useEffect(() => {
    document.documentElement.lang = locale;
    document.documentElement.dir = locale === "ar" ? "rtl" : "ltr";
    if (ready) saveValue("ht-language", locale);
  }, [locale, ready]);
  async function run(
    fn: () => Promise<void> | void,
    message?: string,
  ): Promise<boolean> {
    if (working.current) return false;
    working.current = true;
    setBusy(true);
    setNotice("");
    try {
      await fn();
      if (message) setNotice(message);
      return true;
    } catch (error) {
      setNotice(
        error instanceof Error
          ? error.message
          : "Something went wrong. Please try again.",
      );
      return false;
    } finally {
      working.current = false;
      setBusy(false);
    }
  }
  const t = (en: string, ar: string) => (locale === "ar" ? ar : en);
  const store: Store = {
    state,
    locale,
    ready,
    live,
    busy,
    notice,
    t,
    setLocale: setLocaleState,
    clearNotice: () => setNotice(""),
    add: async (id) => {
      await run(
        () => commit(addItem(ref.current, id)),
        t("Added to your bag.", "تمت الإضافة إلى حقيبتك."),
      );
    },
    quantity: (id, n) => {
      if (busy) return;
      commit({
        ...ref.current,
        cart: ref.current.cart
          .map((x) =>
            x.dishId === id
              ? { ...x, quantity: Math.min(20, Math.max(0, n)) }
              : x,
          )
          .filter((x) => x.quantity > 0),
      });
    },
    reset: () => {
      if (liveRef.current) return;
      commit(freshState());
      setNotice(t("Demo reset.", "تمت إعادة ضبط العرض."));
    },
    role: (role, kitchenId) => {
      if (liveRef.current) return;
      commit({
        ...ref.current,
        user: {
          ...ref.current.user,
          role,
          restaurantId:
            role === "restaurant"
              ? kitchenId || ref.current.user.restaurantId || "r1"
              : undefined,
        },
      });
    },
    placeOrder: async (address) =>
      run(
        async () => {
          const s = ref.current;
          if (liveRef.current) {
            const signature = JSON.stringify({
              user: s.user.id,
              items: s.cart,
              address,
            });
            if (pendingCheckout.current?.signature !== signature)
              pendingCheckout.current = { signature, key: crypto.randomUUID() };
            await api("/orders", "POST", {
              items: s.cart,
              address,
              idempotencyKey: pendingCheckout.current.key,
            });
            await refresh(true);
            pendingCheckout.current = null;
          } else
            commit(
              checkout(
                s,
                address,
                crypto.randomUUID(),
                new Date().toISOString(),
              ),
            );
        },
        t(
          "Order placed. Follow its progress in Orders.",
          "تم الطلب. تابع حالته في صفحة الطلبات.",
        ),
      ),
    status: async (id, status) => {
      await run(
        async () => {
          if (liveRef.current) {
            await api("/orders/" + id, "PATCH", { status });
            await refresh();
          } else commit(advanceOrder(ref.current, id, status));
        },
        t("Order updated.", "تم تحديث الطلب."),
      );
    },
    recharge: async (amount) => {
      await run(
        async () => {
          if (!Number.isInteger(amount) || amount < 100 || amount > 100000)
            throw new Error(
              t(
                "Enter an amount from SAR 1 to 1,000.",
                "أدخل مبلغاً من ١ إلى ١٠٠٠ ريال.",
              ),
            );
          if (liveRef.current) {
            await api("/wallet/requests", "POST", { amount });
            await refresh();
          } else {
            const s = ref.current;
            if (s.recharges.some((x) => x.status === "pending"))
              throw new Error(
                t(
                  "You already have a pending request.",
                  "لديك طلب قيد الانتظار.",
                ),
              );
            commit({
              ...s,
              recharges: [
                {
                  id: crypto.randomUUID(),
                  userId: s.user.id,
                  amount,
                  status: "pending",
                },
                ...s.recharges,
              ],
            });
          }
        },
        t(
          "Credit request submitted for admin approval.",
          "تم إرسال طلب الرصيد للموافقة.",
        ),
      );
    },
    decide: async (id, approved) => {
      await run(async () => {
        if (liveRef.current) {
          await api("/admin/requests/" + id, "PATCH", { approved });
          await refresh();
        } else commit(approveRecharge(ref.current, id, approved));
      });
    },
    approveKitchen: async (id, approved) => {
      await run(async () => {
        if (liveRef.current) {
          await api("/admin/restaurants/" + id, "PATCH", { approved });
          await refresh();
        } else
          commit({
            ...ref.current,
            restaurants: ref.current.restaurants.map((r) =>
              r.id === id ? { ...r, approved } : r,
            ),
          });
      });
    },
    profile: async (name, preferences, considerations) => {
      await run(
        async () => {
          if (name.trim().length < 2)
            throw new Error(t("Please enter your name.", "يرجى إدخال اسمك."));
          if (liveRef.current) {
            await api("/profile", "PATCH", {
              name,
              preferences,
              considerations,
            });
            await refresh();
          } else
            commit({
              ...ref.current,
              user: {
                ...ref.current.user,
                name: name.trim(),
                preferences,
                considerations,
              },
            });
        },
        t("Profile saved.", "تم حفظ الملف الشخصي."),
      );
    },
    saveDish: async (dish, creating = false) => {
      return run(
        async () => {
          if (
            !dish.name.trim() ||
            !Number.isInteger(dish.price) ||
            dish.price < 100
          )
            throw new Error(
              t(
                "Enter a dish name and a valid price.",
                "أدخل اسم الطبق وسعراً صحيحاً.",
              ),
            );
          if (liveRef.current) {
            const { id, restaurantId, ...body } = dish;
            void restaurantId;
            await api(
              "/restaurant/dishes" + (creating ? "" : "/" + id),
              creating ? "POST" : "PUT",
              body,
            );
            await refresh();
          } else
            commit({
              ...ref.current,
              dishes: creating
                ? [...ref.current.dishes, dish]
                : ref.current.dishes.map((d) => (d.id === dish.id ? dish : d)),
            });
        },
        t("Menu updated.", "تم تحديث القائمة."),
      );
    },
    saveKitchen: async (restaurant) => {
      await run(
        async () => {
          if (liveRef.current) {
            const { id, approved, ...body } = restaurant;
            void id;
            void approved;
            await api("/restaurant/profile", "PATCH", body);
            await refresh();
          } else
            commit({
              ...ref.current,
              restaurants: ref.current.restaurants.map((r) =>
                r.id === restaurant.id ? restaurant : r,
              ),
            });
        },
        t("Kitchen profile saved.", "تم حفظ ملف المطعم."),
      );
    },
    review: async (orderId, rating, comment) => {
      await run(
        async () => {
          if (comment.trim().length < 3)
            throw new Error(
              t("Please add a short review.", "يرجى إضافة مراجعة قصيرة."),
            );
          if (liveRef.current) {
            await api("/reviews", "POST", { orderId, rating, comment });
            await refresh();
          } else {
            const s = ref.current;
            const order = s.orders.find((o) => o.id === orderId);
            if (
              !order ||
              order.status !== "delivered" ||
              s.reviews.some((r) => r.orderId === orderId)
            )
              throw new Error(
                t(
                  "Only one review per delivered order.",
                  "مراجعة واحدة لكل طلب تم توصيله.",
                ),
              );
            commit({
              ...s,
              reviews: [
                ...s.reviews,
                {
                  id: crypto.randomUUID(),
                  orderId,
                  restaurantId: order.restaurantId,
                  rating,
                  comment,
                  name: s.user.name,
                },
              ],
            });
          }
        },
        t("Thank you for your review.", "شكراً لمراجعتك."),
      );
    },
    login: async (email, password, name, role = "customer") =>
      run(async () => {
        if (process.env.NEXT_PUBLIC_API_ENABLED !== "true")
          throw new Error(
            t(
              "Live accounts are disabled. You can explore the browser demo.",
              "الحسابات الفعلية غير مفعلة. يمكنك تجربة العرض.",
            ),
          );
        const result = await api<{ csrf: string }>(
          "/auth/" + (name ? "signup" : "login"),
          "POST",
          name ? { email, password, name, role } : { email, password },
        );
        csrf.current = result.csrf;
        const account = await api<{ csrf: string; state: State }>("/bootstrap");
        csrf.current = account.csrf;
        liveRef.current = true;
        setLive(true);
        commit(account.state);
        saveValue("ht-live", "true");
      }),
    logout: async () => {
      await run(async () => {
        if (liveRef.current) await api("/auth/logout", "POST");
        liveRef.current = false;
        setLive(false);
        saveValue("ht-live", null);
        commit(freshState());
      });
    },
    analyze: async (question, image) => {
      if (!liveRef.current)
        throw new Error(
          t(
            "AI is off in the demo. No image or profile was sent. Connect the API and sign in to use this feature.",
            "الذكاء الاصطناعي غير مفعل في العرض. لم تُرسل صورتك أو بياناتك.",
          ),
        );
      const result = await api<{ answer: string }>("/insights", "POST", {
        question,
        image,
        consent: true,
      });
      return result.answer;
    },
  };
  return <Context.Provider value={store}>{children}</Context.Provider>;
}
export function useStore() {
  const value = useContext(Context);
  if (!value) throw new Error("Missing Provider");
  return value;
}
