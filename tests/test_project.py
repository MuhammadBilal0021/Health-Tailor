import os
os.environ['APP_MODE'] = 'demo'
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import unittest
import io
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
from werkzeug.security import generate_password_hash
import app as project
from runtime import MemoryDB, demo_data, verify_password
from transactions import approve_recharge, change_order_status, place_order, refund_order

class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.db = MemoryDB()
        self.db.data = demo_data()
        project.db.data = demo_data()
        project.app.config['TESTING'] = True
        self.client = project.app.test_client()

    def login(self, role='user'):
        with self.client.session_transaction() as s:
            s['_csrf'] = 'test-csrf'
            if role == 'user':
                s.update(user_id='demo-user', user_email='demo@example.invalid')
            elif role == 'restaurant':
                s.update(restaurant_id='demo-kitchen', restaurant_email='kitchen@example.invalid')
            else:
                s['admin'] = True

    def test_public_pages_and_all_template_syntax(self):
        for path in ['/', '/demo', '/user_login', '/restaurant_login', '/admin_login', '/signup', '/restaurant_signup', '/missing']:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 404 if path == '/missing' else 200, path)
        for template in Path(project.app.template_folder if Path(project.app.template_folder).is_absolute() else Path(project.app.root_path)/project.app.template_folder).glob('*.html'):
            project.app.jinja_env.parse(template.read_text(encoding='utf-8-sig'))

    def test_customer_pages(self):
        self.login()
        for path in ['/user_dashboard', '/user/restaurants', '/user/restaurant/demo-kitchen', '/user/cart', '/user/wallet', '/user/orders', '/health_analysis', '/edit_profile']:
            self.assertEqual(self.client.get(path).status_code, 200, path)

    def test_restaurant_pages(self):
        self.login('restaurant')
        for path in ['/restaurant_dashboard', '/restaurant/menu', '/restaurant/my_orders', '/restaurant/wallet', '/restaurant/profile', '/restaurant/settings', '/restaurant/gallery', '/restaurant/help']:
            self.assertEqual(self.client.get(path).status_code, 200, path)

    def test_admin_pages(self):
        self.login('admin')
        for path in ['/admin_dashboard', '/admin/restaurants', '/admin/wallet_requests']:
            self.assertEqual(self.client.get(path).status_code, 200, path)

    def test_csrf_rejects_missing_token(self):
        self.assertEqual(self.client.post('/demo').status_code, 400)

    def test_passwords_require_hashes(self):
        self.assertTrue(verify_password(generate_password_hash('a-test-password'), 'a-test-password'))
        self.assertFalse(verify_password('legacy-plaintext', 'legacy-plaintext'))
        self.assertFalse(verify_password(generate_password_hash('correct'), 'wrong'))

    def test_recharge_cannot_be_replayed_concurrently(self):
        self.db.data['wallet_recharge_requests'] = {'r1': {'user_id': 'demo-user', 'amount': 100, 'status': 'pending'}}
        def approve(_):
            try:
                approve_recharge(self.db, 'r1')
                return True
            except ValueError:
                return False
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(approve, range(8)))
        self.assertEqual(sum(results), 1)
        self.assertEqual(self.db.data['wallets']['demo-user']['balance'], 5100)

    def create_order(self):
        self.db.data['carts'] = {'demo-user': {'i1': {'restaurant_id': 'demo-kitchen', 'menu_item_id': 'bowl', 'quantity': 1, 'price': 1}}}
        return place_order(self.db, 'demo-user', {'user_email': 'demo@example.invalid'}, {'delivery_address': 'Demo address'})

    def test_checkout_reprices_and_refund_is_once(self):
        order_id, order, balance = self.create_order()
        self.assertEqual(order['subtotal'], 650)
        self.assertEqual(balance, 4314.51)
        refund_order(self.db, order_id, 'demo-user')
        with self.assertRaises(ValueError):
            refund_order(self.db, order_id, 'demo-user')
        self.assertEqual(self.db.data['wallets']['demo-user']['balance'], 5000)

    def test_status_transition_and_settlement_idempotency(self):
        oid, _, _ = self.create_order()
        with self.assertRaises(ValueError):
            change_order_status(self.db, oid, 'other-restaurant', 'confirmed')
        with self.assertRaises(ValueError):
            change_order_status(self.db, oid, 'demo-kitchen', 'delivered')
        for status in ['confirmed', 'preparing', 'ready', 'delivered', 'delivered']:
            change_order_status(self.db, oid, 'demo-kitchen', status)
        self.assertEqual(self.db.data['restaurant_wallets']['demo-kitchen']['balance'], 650)
        with self.assertRaises(ValueError):
            change_order_status(self.db, oid, 'demo-kitchen', 'pending')

    def test_ai_failure_returns_no_fabricated_result(self):
        buf = io.BytesIO(); Image.new('RGB', (2,2)).save(buf, format='PNG')
        self.assertIsNone(project.analyze_dish_with_gemini(buf.getvalue(), {}))
        self.assertIsNone(project.get_fallback_recommendations({}))
        self.assertIsNone(project.prepare_comprehensive_chart_data({}, True, {}))

    def test_customer_checkout_route(self):
        self.login()
        headers={'X-CSRF-Token': 'test-csrf'}
        self.assertTrue(self.client.post('/user/cart/add/demo-kitchen/bowl', headers=headers).json['success'])
        response = self.client.post('/user/checkout', json={'delivery_address':'Sample address'}, headers=headers)
        self.assertTrue(response.json['success'], response.json)
        self.assertEqual(self.client.get('/user/order/' + response.json['order_id']).status_code, 200)

    def test_delivery_still_settles_when_email_fails(self):
        from unittest.mock import patch
        self.login('restaurant')
        project.db.data['orders'] = {'test-order': {'restaurant_id': 'demo-kitchen', 'user_id': 'demo-user',
            'status': 'ready', 'payment_status': 'paid', 'subtotal': 650, 'total_amount': 685.49}}
        with patch.object(project, 'send_order_status_email_v2', side_effect=RuntimeError('mail unavailable')):
            response = self.client.post('/restaurant/order/update_status/test-order',
                json={'status': 'delivered'}, headers={'X-CSRF-Token': 'test-csrf'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['success'])
        self.assertEqual(project.db.data['restaurant_wallets']['demo-kitchen']['balance'], 650)

    def test_invalid_ai_text_does_not_become_assessment(self):
        self.assertIsNone(project.parse_analysis_response('unstructured error', {}))

if __name__ == '__main__':
    unittest.main()
