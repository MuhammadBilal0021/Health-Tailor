from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Literal, Annotated
from pydantic import StringConstraints


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Credentials(Input):
    email: str = Field(min_length=3, max_length=254, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    password: Annotated[
        str, StringConstraints(strip_whitespace=False, min_length=10, max_length=128)
    ]

    @field_validator("email")
    @classmethod
    def normalize(cls, value):
        return value.lower()


class Signup(Credentials):
    name: str = Field(min_length=2, max_length=100)
    role: Literal["customer", "restaurant"] = "customer"


class Profile(Input):
    name: str = Field(min_length=2, max_length=100)
    preferences: list[str] = Field(max_length=8)
    considerations: str = Field(max_length=500, default="")

    @field_validator("preferences")
    @classmethod
    def valid_tags(cls, value):
        if any(
            x not in ["Plant-based", "Protein-focused", "Mild", "Gluten-free ingredients", "Spicy"]
            for x in value
        ):
            raise ValueError("Unknown preference")
        return list(dict.fromkeys(value))


class Line(Input):
    dishId: str = Field(min_length=1, max_length=64)
    quantity: int = Field(strict=True, ge=1, le=20)


class Checkout(Input):
    items: list[Line] = Field(min_length=1, max_length=30)
    address: str = Field(min_length=5, max_length=300)
    idempotencyKey: str = Field(min_length=8, max_length=64)


class StatusUpdate(Input):
    status: Literal["pending", "confirmed", "preparing", "ready", "delivered", "cancelled"]


class RechargeInput(Input):
    amount: int = Field(strict=True, ge=100, le=100000)


class Decision(Input):
    approved: bool


class DishInput(Input):
    name: str = Field(min_length=2, max_length=100)
    nameAr: str = Field(default="", max_length=100)
    description: str = Field(max_length=500)
    descriptionAr: str = Field(default="", max_length=500)
    price: int = Field(strict=True, ge=100, le=100000)
    tags: list[str] = Field(default_factory=list, max_length=8)
    ingredients: list[str] = Field(default_factory=list, max_length=30)
    allergens: list[str] = Field(default_factory=list, max_length=20)
    available: bool = True
    art: int = Field(ge=0, le=5, default=0)

    @field_validator("tags", "ingredients", "allergens")
    @classmethod
    def bounded_list(cls, value):
        if any(len(x) > 80 for x in value):
            raise ValueError("Each entry must be at most 80 characters")
        return value


class RestaurantInput(Input):
    name: str = Field(min_length=2, max_length=100)
    nameAr: str = Field(default="", max_length=100)
    description: str = Field(max_length=500)
    descriptionAr: str = Field(default="", max_length=500)
    city: str = Field(min_length=2, max_length=80)
    cuisine: str = Field(min_length=2, max_length=80)


class ReviewInput(Input):
    orderId: str = Field(max_length=64)
    rating: int = Field(strict=True, ge=1, le=5)
    comment: str = Field(min_length=3, max_length=500)


class AnalysisInput(Input):
    consent: Literal[True]
    question: str = Field(min_length=3, max_length=1000)
    image: str | None = Field(default=None, max_length=4000000)
