export type Locale = "en" | "ar";
export type Role = "customer" | "restaurant" | "admin";
export type Status =
  "pending" | "confirmed" | "preparing" | "ready" | "delivered" | "cancelled";
export type User = {
  id: string;
  name: string;
  email: string;
  role: Role;
  restaurantId?: string;
  preferences: string[];
  considerations: string;
  balance: number;
};
export type Restaurant = {
  id: string;
  name: string;
  nameAr: string;
  description: string;
  descriptionAr: string;
  city: string;
  approved: boolean;
  cuisine: string;
};
export type Dish = {
  id: string;
  restaurantId: string;
  name: string;
  nameAr: string;
  description: string;
  descriptionAr: string;
  price: number;
  tags: string[];
  ingredients: string[];
  allergens: string[];
  available: boolean;
  art: number;
};
export type CartItem = { dishId: string; quantity: number };
export type Order = {
  id: string;
  userId: string;
  restaurantId: string;
  items: { name: string; quantity: number; price: number }[];
  total: number;
  subtotal: number;
  status: Status;
  createdAt: string;
  address: string;
  settled: boolean;
};
export type Entry = {
  id: string;
  description: string;
  amount: number;
  createdAt: string;
};
export type Recharge = {
  id: string;
  userId: string;
  amount: number;
  status: "pending" | "approved" | "rejected";
};
export type Review = {
  id: string;
  orderId: string;
  restaurantId: string;
  rating: number;
  comment: string;
  name: string;
};
export type State = {
  user: User;
  restaurants: Restaurant[];
  dishes: Dish[];
  cart: CartItem[];
  orders: Order[];
  ledger: Entry[];
  recharges: Recharge[];
  reviews: Review[];
  restaurantBalance: number;
};
export type Page =
  | "home"
  | "explore"
  | "cart"
  | "orders"
  | "profile"
  | "wallet"
  | "insights"
  | "restaurant"
  | "admin"
  | "login";
export const statusSequence: Status[] = [
  "pending",
  "confirmed",
  "preparing",
  "ready",
  "delivered",
];
export const statusAr: Record<Status, string> = {
  pending: "قيد الانتظار",
  confirmed: "مؤكد",
  preparing: "قيد التحضير",
  ready: "جاهز",
  delivered: "تم التوصيل",
  cancelled: "ملغى",
};
export const formatMoney = (cents: number, locale: Locale = "en") =>
  new Intl.NumberFormat(locale === "ar" ? "ar-SA" : "en-SA", {
    style: "currency",
    currency: "SAR",
  }).format(cents / 100);
