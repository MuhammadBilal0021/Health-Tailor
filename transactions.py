"""Atomic wallet/order operations for the graduation-project data model.

All related records are committed in one root transaction. Suitable for this
small prototype; a production system should partition its ledger to avoid root contention.
Callbacks have no external side effects because Firebase may retry them.
"""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import datetime, timezone
import copy
import uuid


def money(value):
    try:
        result = Decimal(str(value))
        if not result.is_finite() or result < 0:
            raise ValueError('Amount must be a finite non-negative number.')
        return result.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise ValueError('Invalid amount.') from exc


def now():
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')


def ledger(data, collection, user_id, key, amount, kind, description):
    wallet_collection = 'restaurant_wallets' if collection == 'restaurant_wallet_transactions' else 'wallets'
    wallet = data.setdefault(wallet_collection, {}).setdefault(user_id, {'balance': 0})
    previous = money(wallet.get('balance', 0))
    balance = previous + amount if kind == 'credit' else previous - amount
    if balance < 0:
        raise ValueError('Insufficient wallet balance.')
    wallet.update(balance=float(balance), updated_at=now())
    data.setdefault(collection, {}).setdefault(user_id, {})[key] = {
        'type': kind, 'amount': float(amount), 'previous_balance': float(previous),
        'new_balance': float(balance), 'description': description, 'created_at': now(), 'currency': 'PKR'}
    return float(balance)


def approve_recharge(db, request_id):
    def update(data):
        data = data or {}
        req = data.get('wallet_recharge_requests', {}).get(request_id)
        if not req:
            raise ValueError('Recharge request not found.')
        if req.get('status') != 'pending':
            raise ValueError('This request has already been processed.')
        amount = money(req.get('amount', 0))
        if amount <= 0:
            raise ValueError('Amount must be positive.')
        ledger(data, 'wallet_transactions', req['user_id'], 'recharge-' + request_id, amount, 'credit', 'Approved wallet recharge')
        req.update(status='approved', processed_at=now(), processed_by='admin')
        return data
    db.reference('/').transaction(update)


def _settle(data, order_id):
    order = data.get('orders', {}).get(order_id)
    if not order or order.get('status') != 'delivered' or order.get('payout_settled'):
        return
    if order.get('payment_status') != 'paid':
        raise ValueError('Only paid orders can be settled.')
    amount = money(order.get('subtotal', 0))
    ledger(data, 'restaurant_wallet_transactions', order['restaurant_id'], 'order-' + order_id, amount, 'credit', 'Delivered order ' + order_id)
    order.update(payout_settled=True, payout_amount=float(amount), payout_currency='PKR', payout_at=now())


def settle_order(db, order_id):
    def update(data):
        data = data or {}
        _settle(data, order_id)
        return data
    db.reference('/').transaction(update)


def _refund(data, order_id, order):
    if order.get('payment_status') == 'paid':
        ledger(data, 'wallet_transactions', order['user_id'], 'refund-' + order_id,
               money(order['total_amount']), 'credit', 'Order cancellation refund')
        order['payment_status'] = 'refunded'
    order.update(status='cancelled', cancelled_at=now())


def change_order_status(db, order_id, restaurant_id, status):
    transitions = {'pending': {'confirmed', 'cancelled'}, 'confirmed': {'preparing', 'cancelled'},
                   'preparing': {'ready'}, 'ready': {'delivered'}, 'delivered': set(), 'cancelled': set()}
    def update(data):
        data = data or {}
        order = data.get('orders', {}).get(order_id)
        if not order or order.get('restaurant_id') != restaurant_id:
            raise ValueError('Order not found.')
        current = order.get('status', 'pending')
        if status != current and status not in transitions.get(current, set()):
            raise ValueError('This order status transition is not allowed.')
        if status == 'cancelled':
            _refund(data, order_id, order)
        else:
            order.update(status=status, updated_at=now())
            order[status + '_at'] = now()
            _settle(data, order_id)
        return data
    state = db.reference('/').transaction(update)
    return state['orders'][order_id]


def refund_order(db, order_id, user_id):
    def update(data):
        data = data or {}
        order = data.get('orders', {}).get(order_id)
        if not order or order.get('user_id') != user_id:
            raise ValueError('Order not found.')
        if order.get('status') not in ('pending', 'confirmed'):
            raise ValueError('This order can no longer be cancelled.')
        _refund(data, order_id, order)
        return data
    db.reference('/').transaction(update)


def place_order(db, user_id, user_session, details):
    order_id = uuid.uuid4().hex
    if not str(details.get('delivery_address', '')).strip():
        raise ValueError('Please provide a delivery address.')
    def update(data):
        data = data or {}
        cart = data.get('carts', {}).get(user_id, {})
        if not cart:
            raise ValueError('Your cart is empty.')
        items, restaurant_ids, subtotal = [], set(), Decimal('0')
        for item in cart.values():
            rid = item['restaurant_id']
            restaurant_ids.add(rid)
            menu = data.get('menu', {}).get(rid, {}).get(item['menu_item_id'])
            if not menu or not menu.get('is_available', True):
                raise ValueError('A menu item is no longer available. Please update your cart.')
            quantity = item.get('quantity', 1)
            if type(quantity) is not int or not 1 <= quantity <= 100:
                raise ValueError('Quantity must be between 1 and 100.')
            price = money(menu['price'])
            subtotal += price * quantity
            items.append({**item, 'price': float(price), 'name': menu['name']})
        if len(restaurant_ids) != 1:
            raise ValueError('Please order from one restaurant at a time.')
        rid = next(iter(restaurant_ids))
        restaurant = data.get('restaurants', {}).get(rid, {})
        if str(restaurant.get('status')).lower() not in ('approved', 'true'):
            raise ValueError('This restaurant is not currently accepting orders.')
        delivery = Decimal('2.99')
        tax = money(subtotal * Decimal('0.05'))
        total = subtotal + delivery + tax
        ledger(data, 'wallet_transactions', user_id, 'order-' + order_id, total, 'debit', 'Food order ' + order_id)
        data.setdefault('orders', {})[order_id] = {
            'user_id': user_id, 'user_email': user_session.get('user_email', ''), 'user_name': user_session.get('user_name', 'Customer'),
            'restaurant_id': rid, 'restaurant_name': restaurant.get('restaurant_name', ''), 'items': items,
            'subtotal': float(subtotal), 'tax': float(tax), 'delivery_fee': float(delivery), 'total_amount': float(total),
            'delivery_address': str(details['delivery_address']), 'delivery_instructions': str(details.get('delivery_instructions', '')),
            'status': 'pending', 'payment_status': 'paid', 'payment_method': 'wallet', 'created_at': now(), 'order_number': 'HT-' + order_id[:10].upper()}
        data['carts'].pop(user_id, None)
        return data
    state = db.reference('/').transaction(update)
    return order_id, state['orders'][order_id], state['wallets'][user_id]['balance']
