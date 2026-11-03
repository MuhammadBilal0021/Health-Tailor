def restaurant(r):
    return dict(
        id=r.id,
        name=r.name,
        nameAr=r.name_ar,
        description=r.description,
        descriptionAr=r.description_ar,
        city=r.city,
        cuisine=r.cuisine,
        approved=r.approved,
    )


def dish(d):
    return dict(
        id=d.id,
        restaurantId=d.restaurant_id,
        name=d.name,
        nameAr=d.name_ar,
        description=d.description,
        descriptionAr=d.description_ar,
        price=d.price,
        tags=d.tags,
        ingredients=d.ingredients,
        allergens=d.allergens,
        available=d.available,
        art=d.art,
    )


def order(o):
    return dict(
        id=o.id,
        userId=o.user_id,
        restaurantId=o.restaurant_id,
        items=o.items,
        subtotal=o.subtotal,
        total=o.total,
        status=o.status,
        address=o.address,
        settled=o.settled,
        createdAt=o.created_at.isoformat() + "Z"
        if o.created_at.tzinfo is None
        else o.created_at.isoformat(),
    )


def recharge(r):
    return dict(id=r.id, userId=r.user_id, amount=r.amount, status=r.status)


def review(r):
    return dict(
        id=r.id,
        orderId=r.order_id,
        restaurantId=r.restaurant_id,
        rating=r.rating,
        comment=r.comment,
        name=r.name,
    )
