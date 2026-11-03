"""Money is stored in integer halalas. Each operation commits once in the route dependency."""

import hashlib
import json
import uuid
from fastapi import HTTPException
from sqlalchemy import select
from models import User, Restaurant, Dish, Order, Ledger, Recharge

TRANSITIONS = {
    "pending": {"confirmed", "cancelled"},
    "confirmed": {"preparing", "cancelled"},
    "preparing": {"ready"},
    "ready": {"delivered"},
    "delivered": set(),
    "cancelled": set(),
}


def reject(message):
    raise HTTPException(409, message)


def checkout(db, user, payload):
    # Lock the payer first so retries and concurrent purchases serialize.
    payer = db.scalar(
        select(User)
        .where(User.id == user.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    fingerprint = hashlib.sha256(
        json.dumps(payload.model_dump(exclude={"idempotencyKey"}), sort_keys=True).encode()
    ).hexdigest()
    existing = db.scalar(
        select(Order).where(
            Order.user_id == user.id, Order.idempotency_key == payload.idempotencyKey
        )
    )
    if existing:
        if existing.fingerprint != fingerprint:
            reject("This checkout key was used for a different order.")
        return existing
    if len({line.dishId for line in payload.items}) != len(payload.items):
        reject("Combine duplicate items in your bag.")
    dishes = list(
        db.scalars(
            select(Dish)
            .where(Dish.id.in_([line.dishId for line in payload.items]))
            .order_by(Dish.id)
            .with_for_update()
        )
    )
    lookup = {dish.id: dish for dish in dishes}
    if len(dishes) != len(payload.items) or any(not d.available for d in dishes):
        reject("A dish is unavailable. Refresh your bag.")
    kitchens = {d.restaurant_id for d in dishes}
    if len(kitchens) != 1:
        reject("Choose one kitchen per order.")
    restaurant = db.scalar(
        select(Restaurant).where(Restaurant.id == next(iter(kitchens))).with_for_update()
    )
    if not restaurant or not restaurant.approved:
        reject("This kitchen is not accepting orders.")
    items = [
        {
            "name": lookup[line.dishId].name,
            "price": lookup[line.dishId].price,
            "quantity": line.quantity,
        }
        for line in payload.items
    ]
    subtotal = sum(item["price"] * item["quantity"] for item in items)
    total = subtotal + 500
    if payer.balance < total:
        reject("Insufficient wallet credit.")
    payer.balance -= total
    order = Order(
        id=uuid.uuid4().hex,
        user_id=user.id,
        restaurant_id=restaurant.id,
        items=items,
        subtotal=subtotal,
        total=total,
        address=payload.address,
        idempotency_key=payload.idempotencyKey,
        fingerprint=fingerprint,
        status="pending",
        settled=False,
    )
    db.add(order)
    db.add(
        Ledger(
            id="pay-" + order.id,
            user_id=user.id,
            amount=-total,
            description="Order " + order.id[:8],
        )
    )
    db.flush()
    return order


def change_status(db, user, order_id, status):
    order = db.scalar(select(Order).where(Order.id == order_id).with_for_update())
    if not order:
        raise HTTPException(404, "Order not found.")
    restaurant = db.get(Restaurant, order.restaurant_id)
    if user.role == "customer":
        if order.user_id != user.id:
            raise HTTPException(404, "Order not found.")
        if status != "cancelled":
            raise HTTPException(403, "Customers can only cancel an order.")
    elif user.role == "restaurant":
        if restaurant.owner_id != user.id:
            raise HTTPException(404, "Order not found.")
    elif user.role != "admin":
        raise HTTPException(403, "Not allowed.")
    if status == order.status:
        return order
    if status not in TRANSITIONS[order.status]:
        reject("This status transition is not allowed.")
    if status == "cancelled":
        payer = db.scalar(
            select(User)
            .where(User.id == order.user_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        payer.balance += order.total
        db.add(
            Ledger(
                id="refund-" + order.id,
                user_id=payer.id,
                amount=order.total,
                description="Refund for " + order.id[:8],
            )
        )
    if status == "delivered" and not order.settled:
        kitchen = db.scalar(
            select(Restaurant)
            .where(Restaurant.id == order.restaurant_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        kitchen.balance += order.subtotal
        order.settled = True
    order.status = status
    db.flush()
    return order


def decide_recharge(db, request_id, approved):
    recharge = db.scalar(select(Recharge).where(Recharge.id == request_id).with_for_update())
    if not recharge:
        raise HTTPException(404, "Request not found.")
    if recharge.status != "pending":
        reject("This request has already been processed.")
    recharge.status = "approved" if approved else "rejected"
    if approved:
        user = db.scalar(select(User).where(User.id == recharge.user_id).with_for_update())
        user.balance += recharge.amount
        db.add(
            Ledger(
                id="recharge-" + recharge.id,
                user_id=user.id,
                amount=recharge.amount,
                description="Administrator-approved credit",
            )
        )
    db.flush()
    return recharge
