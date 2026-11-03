"""Integration tests run against isolated SQLite locally or PostgreSQL in CI."""

import os
from concurrent.futures import ThreadPoolExecutor
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session as DBSession
from sqlalchemy.pool import StaticPool
from database import Base, get_db, engine_for
from models import User, Restaurant, Dish, Order, Ledger
from auth import hash_password
from main import app
from schemas import Checkout, Credentials
import commerce

PASSWORD = "a strong test password"


@pytest.fixture()
def environment(monkeypatch):
    monkeypatch.setenv("COOKIE_SECURE", "false")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    url = os.getenv("TEST_DATABASE_URL")
    engine = (
        engine_for(url)
        if url
        else create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
    )
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with DBSession(engine) as db, db.begin():
        for id, role in [
            ("buyer", "customer"),
            ("other", "customer"),
            ("owner", "restaurant"),
            ("owner2", "restaurant"),
            ("admin", "admin"),
        ]:
            db.add(
                User(
                    id=id,
                    email=id + "@example.test",
                    name=id,
                    password_hash=hash_password(PASSWORD),
                    role=role,
                    balance=50000,
                )
            )
        db.flush()
        db.add_all(
            [
                Restaurant(id="r1", owner_id="owner", name="Kitchen One", approved=True),
                Restaurant(id="r2", owner_id="owner2", name="Kitchen Two", approved=True),
            ]
        )
        db.flush()
        db.add_all(
            [
                Dish(id="d1", restaurant_id="r1", name="Meal", price=4200, available=True),
                Dish(id="d2", restaurant_id="r2", name="Other meal", price=3000, available=True),
            ]
        )

    def sessions():
        with DBSession(engine, expire_on_commit=False) as db:
            try:
                yield db
                db.commit()
            except Exception:
                db.rollback()
                raise

    app.dependency_overrides[get_db] = sessions
    yield engine
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


def client_as(identity):
    client = TestClient(app)
    result = client.post(
        "/api/auth/login", json={"email": identity + "@example.test", "password": PASSWORD}
    )
    assert result.status_code == 200, result.text
    client.headers["X-CSRF-Token"] = result.json()["csrf"]
    return client


def purchase(client, key="checkout-key-001"):
    return client.post(
        "/api/orders",
        json={
            "items": [{"dishId": "d1", "quantity": 1}],
            "address": "Riyadh building 10",
            "idempotencyKey": key,
        },
    )


def balance(engine, id="buyer"):
    with DBSession(engine) as db:
        return db.get(User, id).balance


def test_session_csrf_and_role_checks(environment):
    assert TestClient(app).get("/api/bootstrap").status_code == 401
    buyer = client_as("buyer")
    assert buyer.get("/api/bootstrap").json()["state"]["user"]["role"] == "customer"
    assert buyer.patch("/api/admin/restaurants/r1", json={"approved": False}).status_code == 403
    buyer.headers.pop("X-CSRF-Token")
    assert (
        buyer.patch("/api/profile", json={"name": "Changed", "preferences": []}).status_code == 403
    )
    assert (
        buyer.post("/api/auth/logout", headers={"Origin": "https://evil.example"}).status_code
        == 403
    )


def test_signup_cannot_choose_admin_or_grant_credit(environment):
    c = TestClient(app)
    payload = {
        "email": "new@example.test",
        "password": PASSWORD,
        "name": "New User",
        "role": "admin",
    }
    assert c.post("/api/auth/signup", json=payload).status_code == 422
    payload["role"] = "customer"
    assert c.post("/api/auth/signup", json=payload).status_code == 201
    assert c.get("/api/bootstrap").json()["state"]["user"]["balance"] == 0
    assert c.post("/api/auth/signup", json=payload).status_code == 409


def test_checkout_replay_and_payload_mismatch(environment):
    c = client_as("buyer")
    first = purchase(c)
    assert first.status_code == 201, first.text
    again = purchase(c)
    assert again.json()["id"] == first.json()["id"]
    assert balance(environment) == 45300
    assert (
        c.post(
            "/api/orders",
            json={
                "items": [{"dishId": "d1", "quantity": 2}],
                "address": "Riyadh building 10",
                "idempotencyKey": "checkout-key-001",
            },
        ).status_code
        == 409
    )
    with DBSession(environment) as db:
        assert db.scalar(select(func.count()).select_from(Order)) == 1


def test_server_prices_and_mixed_kitchen_validation(environment):
    c = client_as("buyer")
    payload = {
        "items": [{"dishId": "d1", "quantity": 1}, {"dishId": "d2", "quantity": 1}],
        "address": "Building 10",
        "idempotencyKey": "mixed-key",
    }
    assert c.post("/api/orders", json=payload).status_code == 409
    payload["items"] = [{"dishId": "d1", "quantity": 1, "price": 1}]
    assert c.post("/api/orders", json=payload).status_code == 422
    with DBSession(environment) as db, db.begin():
        db.get(Dish, "d1").price = 5000
    assert purchase(c).json()["total"] == 5500


def test_unavailable_and_insufficient_credit(environment):
    c = client_as("buyer")
    with DBSession(environment) as db, db.begin():
        db.get(Dish, "d1").available = False
    assert purchase(c).status_code == 409
    assert balance(environment) == 50000
    with DBSession(environment) as db, db.begin():
        db.get(Dish, "d1").available = True
        db.get(User, "buyer").balance = 1
    assert purchase(c).status_code == 409
    assert balance(environment) == 1


def test_ownership_and_refund_once(environment):
    buyer = client_as("buyer")
    order = purchase(buyer).json()
    path = "/api/orders/" + order["id"]
    other = client_as("other")
    assert other.patch(path, json={"status": "cancelled"}).status_code == 404
    assert other.get("/api/bootstrap").json()["state"]["orders"] == []
    assert client_as("owner2").patch(path, json={"status": "confirmed"}).status_code == 404
    assert buyer.patch(path, json={"status": "delivered"}).status_code == 403
    assert buyer.patch(path, json={"status": "cancelled"}).status_code == 200
    assert buyer.patch(path, json={"status": "cancelled"}).status_code == 200
    assert balance(environment) == 50000
    with DBSession(environment) as db:
        assert (
            db.scalar(select(func.count()).select_from(Ledger).where(Ledger.id.like("refund-%")))
            == 1
        )


def test_delivery_settles_once_and_review_requires_delivery(environment):
    buyer = client_as("buyer")
    order = purchase(buyer).json()
    path = "/api/orders/" + order["id"]
    owner = client_as("owner")
    review = {"orderId": order["id"], "rating": 5, "comment": "Good meal"}
    assert buyer.post("/api/reviews", json=review).status_code == 409
    assert owner.patch(path, json={"status": "delivered"}).status_code == 409
    for status in ["confirmed", "preparing", "ready", "delivered", "delivered"]:
        response = owner.patch(path, json={"status": status})
        assert response.status_code == 200, response.text
    assert buyer.patch(path, json={"status": "cancelled"}).status_code == 409
    with DBSession(environment) as db:
        assert db.get(Restaurant, "r1").balance == 4200
    assert buyer.post("/api/reviews", json=review).status_code == 201
    assert buyer.post("/api/reviews", json=review).status_code == 409


def test_credit_approval_once(environment):
    buyer = client_as("buyer")
    request = buyer.post("/api/wallet/requests", json={"amount": 1000})
    assert request.status_code == 201
    assert buyer.post("/api/wallet/requests", json={"amount": 1000}).status_code == 409
    path = "/api/admin/requests/" + request.json()["id"]
    admin = client_as("admin")
    assert buyer.patch(path, json={"approved": True}).status_code == 403
    assert admin.patch(path, json={"approved": True}).status_code == 200
    assert admin.patch(path, json={"approved": True}).status_code == 409
    assert balance(environment) == 51000


def test_menu_ownership_and_ai_has_no_fabricated_fallback(environment):
    owner = client_as("owner2")
    payload = {"name": "Changed meal", "description": "Sample", "price": 2000}
    assert owner.put("/api/restaurant/dishes/d1", json=payload).status_code == 404
    buyer = client_as("buyer")
    assert (
        buyer.post(
            "/api/insights", json={"question": "What ingredients?", "consent": False}
        ).status_code
        == 422
    )
    result = buyer.post("/api/insights", json={"question": "What ingredients?", "consent": True})
    assert result.status_code == 503
    assert "No assessment" in result.json()["detail"]


def test_login_rate_limit_and_password_whitespace(environment):
    c = TestClient(app)
    for _ in range(10):
        assert (
            c.post(
                "/api/auth/login", json={"email": "bad@example.test", "password": PASSWORD}
            ).status_code
            == 401
        )
    assert (
        c.post(
            "/api/auth/login", json={"email": "bad@example.test", "password": PASSWORD}
        ).status_code
        == 429
    )
    assert (
        Credentials(email="a@b.test", password="  ten characters  ").password
        == "  ten characters  "
    )


def test_allowed_proxy_origin(environment, monkeypatch):
    monkeypatch.setenv("FRONTEND_ORIGINS", "http://localhost:3000")
    c = client_as("buyer")
    assert (
        c.post(
            "/api/wallet/requests",
            json={"amount": 100},
            headers={"Origin": "http://localhost:3000"},
        ).status_code
        == 201
    )
    assert (
        c.post(
            "/api/wallet/requests",
            json={"amount": 100},
            headers={"Origin": "http://localhost:3000.evil.test"},
        ).status_code
        == 403
    )


def test_postgres_concurrent_checkouts_serialize(environment):
    if environment.dialect.name != "postgresql":
        pytest.skip("Row locking requires PostgreSQL; exercised in CI")
    with DBSession(environment) as db, db.begin():
        db.get(User, "buyer").balance = 4700

    def buy(key):
        from fastapi import HTTPException

        with DBSession(environment) as db:
            try:
                user = db.get(User, "buyer")
                order = commerce.checkout(
                    db,
                    user,
                    Checkout(
                        items=[{"dishId": "d1", "quantity": 1}],
                        address="Building 10",
                        idempotencyKey=key,
                    ),
                )
                db.commit()
                return order.id
            except HTTPException:
                db.rollback()
                return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        result = list(pool.map(buy, ["concurrent-1", "concurrent-2"]))
    assert sum(x is not None for x in result) == 1
    assert balance(environment) == 0
