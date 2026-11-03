import type { State, Status, CartItem } from "./types";
export function totals(state: State, cart: CartItem[] = state.cart) {
  const subtotal = cart.reduce(
    (sum, item) =>
      sum +
      (state.dishes.find((d) => d.id === item.dishId)?.price ?? 0) *
        item.quantity,
    0,
  );
  const delivery = subtotal ? 500 : 0;
  return { subtotal, delivery, total: subtotal + delivery };
}
export function addItem(state: State, dishId: string): State {
  const dish = state.dishes.find((d) => d.id === dishId);
  if (
    !dish?.available ||
    !state.restaurants.find((r) => r.id === dish.restaurantId)?.approved
  )
    throw new Error("This dish is unavailable.");
  if (
    state.cart.some(
      (i) =>
        state.dishes.find((d) => d.id === i.dishId)?.restaurantId !==
        dish.restaurantId,
    )
  )
    throw new Error("Order from one kitchen at a time. Clear your bag first.");
  const cart = state.cart.map((i) => ({ ...i }));
  const existing = cart.find((i) => i.dishId === dishId);
  if (existing) {
    if (existing.quantity >= 20) throw new Error("Maximum quantity is 20.");
    existing.quantity++;
  } else cart.push({ dishId, quantity: 1 });
  return { ...state, cart };
}
export function checkout(
  state: State,
  address: string,
  id: string,
  timestamp: string,
): State {
  if (!address.trim() || address.length > 300)
    throw new Error("Enter a delivery address (up to 300 characters).");
  if (!state.cart.length) throw new Error("Your bag is empty.");
  const restaurants = new Set<string>();
  for (const item of state.cart) {
    const dish = state.dishes.find((d) => d.id === item.dishId);
    if (
      !dish?.available ||
      !state.restaurants.find((r) => r.id === dish.restaurantId)?.approved ||
      !Number.isInteger(item.quantity) ||
      item.quantity < 1 ||
      item.quantity > 20
    )
      throw new Error("Your bag has an unavailable or invalid item.");
    restaurants.add(dish.restaurantId);
  }
  if (restaurants.size !== 1) throw new Error("Choose one kitchen per order.");
  if (state.orders.some((o) => o.id === id)) return state;
  const cost = totals(state);
  if (state.user.balance < cost.total)
    throw new Error("Not enough test credit. Request a top-up in your wallet.");
  const order = {
    id,
    userId: state.user.id,
    restaurantId: [...restaurants][0],
    items: state.cart.map((i) => {
      const d = state.dishes.find((d) => d.id === i.dishId)!;
      return { name: d.name, price: d.price, quantity: i.quantity };
    }),
    subtotal: cost.subtotal,
    total: cost.total,
    status: "pending" as Status,
    createdAt: timestamp,
    address: address.trim(),
    settled: false,
  };
  return {
    ...state,
    cart: [],
    user: { ...state.user, balance: state.user.balance - cost.total },
    orders: [order, ...state.orders],
    ledger: [
      {
        id: "pay-" + id,
        description: "Order " + id.slice(0, 8),
        amount: -cost.total,
        createdAt: timestamp,
      },
      ...state.ledger,
    ],
  };
}
export const transitions: Record<Status, Status[]> = {
  pending: ["confirmed", "cancelled"],
  confirmed: ["preparing", "cancelled"],
  preparing: ["ready"],
  ready: ["delivered"],
  delivered: [],
  cancelled: [],
};
export function advanceOrder(state: State, id: string, status: Status): State {
  const order = state.orders.find((o) => o.id === id);
  if (!order) throw new Error("Order not found.");
  if (order.status === status) return state;
  if (!transitions[order.status].includes(status))
    throw new Error("This order cannot move to that status.");
  let next = {
    ...state,
    orders: state.orders.map((o) =>
      o.id === id
        ? { ...o, status, settled: o.settled || status === "delivered" }
        : o,
    ),
  };
  if (status === "cancelled")
    next = {
      ...next,
      user: { ...state.user, balance: state.user.balance + order.total },
      ledger: [
        {
          id: "refund-" + id,
          description: "Order refund",
          amount: order.total,
          createdAt: new Date().toISOString(),
        },
        ...state.ledger,
      ],
    };
  if (status === "delivered" && !order.settled)
    next = {
      ...next,
      restaurantBalance: state.restaurantBalance + order.subtotal,
    };
  return next;
}
export function approveRecharge(
  state: State,
  id: string,
  approve: boolean,
): State {
  const r = state.recharges.find((x) => x.id === id);
  if (!r || r.status !== "pending")
    throw new Error("Request already processed or missing.");
  return {
    ...state,
    recharges: state.recharges.map((x) =>
      x.id === id ? { ...x, status: approve ? "approved" : "rejected" } : x,
    ),
    user: {
      ...state.user,
      balance: state.user.balance + (approve ? r.amount : 0),
    },
    ledger: approve
      ? [
          {
            id: "recharge-" + id,
            description: "Approved test credit",
            amount: r.amount,
            createdAt: new Date().toISOString(),
          },
          ...state.ledger,
        ]
      : state.ledger,
  };
}
