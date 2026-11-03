import test from "node:test";
import assert from "node:assert/strict";
import { freshState } from "../src/lib/seed";
import {
  addItem,
  checkout,
  advanceOrder,
  approveRecharge,
  totals,
} from "../src/lib/domain";
const ordered = () =>
  checkout(
    addItem(freshState(), "d1"),
    "Riyadh, building 10",
    "order-123",
    "2026-01-01T00:00:00Z",
  );
test("checkout snapshots prices, debits integer credit and clears cart", () => {
  const before = addItem(freshState(), "d1");
  const cost = totals(before);
  const after = checkout(
    before,
    "Riyadh, building 10",
    "order-123",
    "2026-01-01T00:00:00Z",
  );
  assert.equal(after.user.balance, 50000 - cost.total);
  assert.equal(after.orders[0].items[0].price, 4200);
  assert.equal(after.cart.length, 0);
  assert.equal(before.cart.length, 1);
});
test("cannot mix kitchens or add unavailable dishes", () => {
  assert.throws(
    () => addItem(addItem(freshState(), "d1"), "d3"),
    /one kitchen/,
  );
  const s = freshState();
  s.dishes[0].available = false;
  assert.throws(() => addItem(s, "d1"), /unavailable/);
});
test("checkout rechecks availability and funds", () => {
  const s = addItem(freshState(), "d1");
  s.user.balance = 1;
  assert.throws(() => checkout(s, "Riyadh", "key", "now"), /credit/);
  s.dishes[0].available = false;
  assert.throws(() => checkout(s, "Riyadh", "key", "now"), /unavailable/);
});
test("cancellation refunds exactly once and is terminal", () => {
  const s = advanceOrder(ordered(), "order-123", "cancelled");
  assert.equal(s.user.balance, 50000);
  assert.deepEqual(advanceOrder(s, "order-123", "cancelled"), s);
  assert.throws(() => advanceOrder(s, "order-123", "confirmed"));
  assert.equal(s.ledger.filter((x) => x.id.startsWith("refund")).length, 1);
});
test("delivery settles once and cannot skip stages", () => {
  let s = ordered();
  assert.throws(() => advanceOrder(s, "order-123", "delivered"));
  for (const status of [
    "confirmed",
    "preparing",
    "ready",
    "delivered",
  ] as const)
    s = advanceOrder(s, "order-123", status);
  assert.equal(s.restaurantBalance, 4200);
  assert.equal(
    advanceOrder(s, "order-123", "delivered").restaurantBalance,
    4200,
  );
  assert.throws(() => advanceOrder(s, "order-123", "cancelled"));
});
test("credit approval cannot be replayed", () => {
  const s = freshState();
  s.recharges = [
    { id: "r", userId: s.user.id, amount: 1000, status: "pending" },
  ];
  const approved = approveRecharge(s, "r", true);
  assert.equal(approved.user.balance, 51000);
  assert.throws(() => approveRecharge(approved, "r", true));
  assert.equal(approveRecharge(s, "r", false).user.balance, 50000);
});
