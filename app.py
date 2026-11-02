from flask import Flask, request,jsonify, render_template, redirect, url_for, flash, session
import os
from werkzeug.utils import secure_filename
import re
from datetime import datetime, timedelta

import math

import base64
from PIL import Image
import io
# Add this import at the top
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from runtime import configure, verify_password, get_model, mail_client
from transactions import approve_recharge, settle_order, change_order_status, place_order, refund_order
app = Flask(__name__)
db = configure(app)

@app.route('/')
def home():
    return render_template('index.html')


# Configure upload folder and allowed extensions
UPLOAD_FOLDER = str(__import__('pathlib').Path(app.root_path) / 'static' / 'images')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Step 1: Collect form data
        name = request.form.get('name')
        father_name = request.form.get('father_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        age = request.form.get('age')
        sex = request.form.get('sex')
        city = request.form.get('city')
        phone = request.form.get('phone')
        address = request.form.get('address')
        diabetes = request.form.get('diabetes')
        bp = request.form.get('bp')
        dishes = request.form.getlist('dishes')
        spice = request.form.get('spice')
        profile_image = request.files.get('profile_image')

        errors = []

        # Step 2: Field validation
        if not all([name, father_name, email, password, confirm_password, age, sex, city, phone, address]):
            errors.append("Please fill all required fields.")

        # Step 3: Email format validation
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            errors.append("Invalid email format.")

        # Step 4: Password match and strength
        if password != confirm_password:
            errors.append("Passwords do not match.")

        if len(password) < 8 or not re.search(r"[A-Z]", password) or \
                not re.search(r"[0-9]", password) or not re.search(r"[^A-Za-z0-9]", password):
            errors.append(
                "Password must be at least 8 characters and include an uppercase letter, number, and special character.")

        # Step 5: Duplicate email check in Firebase
        ref = db.reference('users')
        users = ref.get() or {}
        if users:
            for user_id, user_info in users.items():
                if user_info.get('email') == email:
                    errors.append("This email is already registered.")
                    break

        # Step 6: Image upload
        image_url = ""
        if profile_image and allowed_file(profile_image.filename):
            filename = secure_filename(profile_image.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            profile_image.save(filepath)
            image_url = url_for('static', filename=f'images/{filename}')
        else:
            if profile_image:
                errors.append("Invalid image file type.")

        # Step 7: Final check
        if errors:
            for error in errors:
                flash(error, 'danger')
            return redirect(url_for('signup'))

        # Step 8: Prepare user data
        user_data = {
            'name': name,
            'father_name': father_name,
            'email': email,
            'password': generate_password_hash(password),
            'age': age,
            'sex': sex,
            'city': city,
            'phone': phone,
            'address': address,
            'diabetes': diabetes,
            'bp': bp,
            'dishes': dishes,
            'spice': spice,
            'status': False,
            'profile_image': image_url
        }

        # Step 9: Push to Firebase
        ref.push(user_data)
        flash("Registration successful!", 'success')
        return redirect(url_for('success'))

    return render_template('signup.html')


@app.route('/success')
def success():
    return render_template('success.html')


@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            flash("Please enter both email and password.", "warning")
            return redirect(url_for('user_login'))

        ref = db.reference('users')
        users = ref.get() or {}

        if users:
            for user_id, user_info in users.items():
                if (
                    isinstance(user_info, dict) and
                    user_info.get('email') == email and
                    verify_password(user_info.get('password'), password)
                ):
                    # Check if approved by admin
                    if str(user_info.get('status')).lower() == 'true':
                        session['user_email'] = email
                        session['user_id'] = user_id
                        flash("Login successful! Welcome!", "success")
                        return redirect(url_for('user_dashboard'))
                    else:
                        flash("Your account is pending admin approval.", "warning")
                        return redirect(url_for('user_login'))

        flash("Invalid email or password.", "danger")
        return redirect(url_for('user_login'))

    return render_template('user_login.html')


@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    # Check if user is logged in
    if 'user_email' not in session:
        flash("Please log in to continue.", "warning")
        return redirect(url_for('user_login'))

    # Get current user data
    ref = db.reference('users')
    users = ref.get() or {}
    current_user = None
    user_id = session.get('user_id')

    # Find current user
    for uid, user in users.items():
        if uid == user_id:
            current_user = user
            break

    if not current_user:
        flash("User not found.", "danger")
        return redirect(url_for('user_dashboard'))

    if request.method == 'POST':
        try:
            # Collect form data
            name = request.form.get('name', '').strip()
            father_name = request.form.get('father_name', '').strip()
            email = request.form.get('email', '').strip()
            age = request.form.get('age', '').strip()
            sex = request.form.get('sex', '').strip()
            city = request.form.get('city', '').strip()
            phone = request.form.get('phone', '').strip()
            address = request.form.get('address', '').strip()
            diabetes = request.form.get('diabetes', 'No')
            bp = request.form.get('bp', 'No')
            dishes = request.form.getlist('dishes')
            spice = request.form.get('spice', 'Medium')
            profile_image = request.files.get('profile_image')

            # Validation
            errors = []

            # Required fields validation
            if not all([name, father_name, email, age, sex, city, phone, address]):
                errors.append("Please fill all required fields.")

            # Email format validation
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                errors.append("Invalid email format.")

            # Email uniqueness check (only if email changed)
            if email != current_user.get('email'):
                for uid, user_info in users.items():
                    if uid != user_id and user_info.get('email') == email:
                        errors.append("This email is already registered.")
                        break

            # Phone validation
            if not re.match(r'^\+?1?\d{9,15}$', phone):
                errors.append("Invalid phone number format.")

            # Age validation
            if not age.isdigit() or not (1 <= int(age) <= 120):
                errors.append("Please enter a valid age (1-120).")

            # Handle image upload
            image_url = current_user.get('profile_image', '')
            if profile_image and allowed_file(profile_image.filename):
                filename = secure_filename(profile_image.filename)
                # Add timestamp to make filename unique
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                profile_image.save(filepath)
                image_url = url_for('static', filename=f'images/{filename}')
            elif profile_image and profile_image.filename != '':
                errors.append("Invalid image file type. Allowed: png, jpg, jpeg, gif")

            # If there are errors, show them and return
            if errors:
                for error in errors:
                    flash(error, 'danger')
                return render_template('edit_profile.html', user=current_user)

            # Prepare updated user data
            updated_data = {
                'name': name,
                'father_name': father_name,
                'email': email,
                'age': age,
                'sex': sex,
                'city': city,
                'phone': phone,
                'address': address,
                'diabetes': diabetes,
                'bp': bp,
                'dishes': dishes if dishes else ['None'],
                'spice': spice,
                'profile_image': image_url,
                'status': current_user.get('status', False),  # Keep existing status
                'password': current_user.get('password', '')  # Keep existing password
            }

            # Update user in Firebase
            user_ref = db.reference(f'users/{user_id}')
            user_ref.update(updated_data)

            # Update session email if changed
            if email != session['user_email']:
                session['user_email'] = email

            flash("Profile updated successfully!", "success")
            return redirect(url_for('user_dashboard'))

        except Exception as e:
            flash(f"Error updating profile: {str(e)}", "danger")
            return render_template('edit_profile.html', user=current_user)

    # GET request - show edit form
    return render_template('edit_profile.html', user=current_user)


@app.route('/user_dashboard')
def user_dashboard():
    if 'user_email' not in session:
        flash("Please log in to continue.", "warning")
        return redirect(url_for('user_login'))

    ref = db.reference('users')
    users = ref.get() or {}

    for uid, user in users.items():
        if user.get('email') == session['user_email']:
            return render_template('user_dashboard.html', user=user)

    flash("User not found.", "danger")
    return redirect(url_for('user_login'))


@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if email == os.getenv('ADMIN_EMAIL') and verify_password(os.getenv('ADMIN_PASSWORD_HASH'), password):
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid credentials", "danger")
            return redirect(url_for('admin_login'))

    return render_template('admin_login.html')


@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('admin'):
        flash("Please login as admin first.", "warning")
        return redirect(url_for('admin_login'))

    users_ref = db.reference('users')
    raw_users = users_ref.get() or {}

    user_list = []
    pending_users_dict = {}  # Create a dictionary for pending users

    for key, val in raw_users.items():
        if isinstance(val, dict):
            val['id'] = key
            user_list.append(val)
            # Add to pending_users_dict if status is false
            if str(val.get('status')).lower() != 'true':
                pending_users_dict[key] = val

    total_users = len(user_list)
    active_users = sum(1 for user in user_list if str(user.get('status')).lower() == 'true')
    pending_users_count = total_users - active_users

    return render_template(
        'admin_dashboard.html',
        users=user_list,
        total_users=total_users,
        active_users=active_users,
        pending_users=pending_users_count,
        pending_users_dict=pending_users_dict  # Pass the dictionary
    )

@app.route('/user_profile/<user_id>')
def user_profile(user_id):
    # Ensure admin is logged in
    if not session.get('admin'):
        flash("Admin login required.", "warning")
        return redirect(url_for('admin_login'))

    # Fetch user data from Firebase
    user_ref = db.reference(f'users/{user_id}')
    user_data = user_ref.get()

    # Handle invalid or missing user data
    if not isinstance(user_data, dict):
        flash("User data not found or corrupted.", "danger")
        return redirect(url_for('admin_dashboard'))

    # Add user ID for actions like update
    user_data['id'] = user_id

    return render_template('user_profile.html', user=user_data)


# Update Status Route
@app.route('/update_status/<user_id>', methods=['POST'])
def update_status(user_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    user_ref = db.reference(f'users/{user_id}')
    user_ref.update({'status': True})

    flash("Status updated successfully.", "success")
    return redirect(url_for('admin_dashboard'))


@app.route('/delete_user/<user_id>', methods=['POST'])
def delete_user(user_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    user_ref = db.reference(f'users/{user_id}')
    user_ref.delete()

    flash("User deleted successfully.", "success")
    return redirect(url_for('admin_dashboard'))


# Restaurant Registration Route
@app.route('/restaurant_signup', methods=['GET', 'POST'])
def restaurant_signup():
    if request.method == 'POST':
        try:
            # Step 1: Collect form data
            restaurant_name = request.form.get('restaurant_name', '').strip()
            owner_name = request.form.get('owner_name', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '').strip()
            phone = request.form.get('phone', '').strip()
            address = request.form.get('address', '').strip()
            city = request.form.get('city', '').strip()
            specialty = request.form.getlist('specialty')
            description = request.form.get('description', '').strip()
            opening_time = request.form.get('opening_time', '')
            closing_time = request.form.get('closing_time', '')

            # Handle multiple image uploads
            image_files = request.files.getlist('restaurant_images')

            errors = []

            # Step 2: Field validation
            required_fields = {
                'restaurant_name': 'Restaurant Name',
                'owner_name': 'Owner Name',
                'email': 'Email Address',
                'password': 'Password',
                'confirm_password': 'Confirm Password',
                'phone': 'Phone Number',
                'address': 'Address',
                'city': 'City'
            }

            for field, field_name in required_fields.items():
                if not locals().get(field):
                    errors.append(f"{field_name} is required.")

            # Step 3: Email format validation
            if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                errors.append("Invalid email format.")

            # Step 4: Password validation
            if password != confirm_password:
                errors.append("Passwords do not match.")

            if len(password) < 8:
                errors.append("Password must be at least 8 characters long.")
            elif not re.search(r"[A-Z]", password):
                errors.append("Password must contain at least one uppercase letter.")
            elif not re.search(r"[0-9]", password):
                errors.append("Password must contain at least one number.")
            elif not re.search(r"[^A-Za-z0-9]", password):
                errors.append("Password must contain at least one special character.")

            # Step 5: Phone validation
            if phone and not re.match(r'^\+?1?\d{9,15}$', phone):
                errors.append("Invalid phone number format.")

            # Step 6: Check for duplicate email
            ref = db.reference('restaurants')
            restaurants = ref.get()
            if restaurants:
                for rest_id, rest_info in restaurants.items():
                    if rest_info.get('email') == email:
                        errors.append("This email is already registered.")
                        break

            # Step 7: Image validation and upload
            image_urls = []
            if not image_files or all(file.filename == '' for file in image_files):
                errors.append("At least one restaurant image is required.")
            else:
                for i, image_file in enumerate(image_files):
                    if image_file and image_file.filename != '':
                        if allowed_file(image_file.filename):
                            filename = secure_filename(image_file.filename)
                            # Add timestamp and index to make filename unique
                            from datetime import datetime
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"restaurant_{timestamp}_{i + 1}_{filename}"
                            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                            image_file.save(filepath)
                            image_urls.append(url_for('static', filename=f'images/{filename}'))
                        else:
                            errors.append(f"Invalid image file type for image {i + 1}. Allowed: png, jpg, jpeg, gif")

            # Require minimum 3 images
            if len(image_urls) < 3:
                errors.append("Minimum 3 restaurant images are required.")

            # Step 8: Time validation
            if opening_time and closing_time:
                if opening_time >= closing_time:
                    errors.append("Opening time must be before closing time.")

            # Step 9: Final validation
            if errors:
                for error in errors:
                    flash(error, 'danger')
                return render_template('restaurant_signup.html',
                                       form_data=request.form,
                                       specialties=specialty)

            # Step 10: Prepare restaurant data
            restaurant_data = {
                'restaurant_name': restaurant_name,
                'owner_name': owner_name,
                'email': email,
                'password': generate_password_hash(password),
                'phone': phone,
                'address': address,
                'city': city,
                'specialty': specialty,
                'description': description,
                'opening_time': opening_time,
                'closing_time': closing_time,
                'images': image_urls,
                'status': False,  # Pending admin approval
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'rating': 0,
                'reviews': 0
            }

            # Step 11: Save to Firebase
            ref.push(restaurant_data)

            # Step 12: Success message
            flash(
                "Restaurant registration submitted successfully! Please wait for admin approval. You will be notified once your account is activated.",
                "success")
            return redirect(url_for('restaurant_success'))

        except Exception as e:
            flash(f"Error during registration: {str(e)}", "danger")
            return render_template('restaurant_signup.html', form_data=request.form)

    # GET request - show empty form
    return render_template('restaurant_signup.html')


@app.route('/restaurant_success')
def restaurant_success():
    return render_template('restaurant_success.html')


# Restaurant Login Route
@app.route('/restaurant_login', methods=['GET', 'POST'])
def restaurant_login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            flash("Please enter both email and password.", "warning")
            return redirect(url_for('restaurant_login'))

        ref = db.reference('restaurants')
        restaurants = ref.get()

        if restaurants:
            for rest_id, rest_info in restaurants.items():
                if (
                        isinstance(rest_info, dict) and
                        rest_info.get('email') == email and
                        verify_password(rest_info.get('password'), password)
                ):
                    # Check if approved by admin
                    if str(rest_info.get('status')).lower() == 'true':
                        session['restaurant_email'] = email
                        session['restaurant_id'] = rest_id
                        session['restaurant_name'] = rest_info.get('restaurant_name', '')
                        flash(f"Login successful! Welcome, {rest_info.get('restaurant_name', '')}!", "success")
                        return redirect(url_for('restaurant_dashboard'))
                    else:
                        flash("Your restaurant account is pending admin approval. Please wait for activation.",
                              "warning")
                        return redirect(url_for('restaurant_login'))

        flash("Invalid email or password.", "danger")
        return redirect(url_for('restaurant_login'))

    return render_template('restaurant_login.html')


# Updated Restaurant Dashboard Route - Add to app.py

@app.route('/restaurant_dashboard')
def restaurant_dashboard():
    """Restaurant dashboard with complete stats and analytics"""
    if 'restaurant_email' not in session:
        flash("Please log in to continue.", "warning")
        return redirect(url_for('restaurant_login'))

    try:
        restaurant_id = session.get('restaurant_id')
        if not restaurant_id:
            flash("Restaurant session missing. Please login again.", "danger")
            return redirect(url_for('restaurant_login'))

        # Get restaurant data
        rest_ref = db.reference(f'restaurants/{restaurant_id}')
        restaurant = rest_ref.get() or {}
        restaurant['id'] = restaurant_id

        # Get all orders for this restaurant
        orders_ref = db.reference('orders')
        all_orders = orders_ref.get() or {}

        # Filter orders for this restaurant
        restaurant_orders = []
        total_orders = 0
        pending_orders = 0
        total_revenue = 0

        for order_id, order_data in all_orders.items():
            if isinstance(order_data, dict) and order_data.get('restaurant_id') == restaurant_id:
                order_data['id'] = order_id
                restaurant_orders.append(order_data)

                # Count total orders
                total_orders += 1

                # Count pending orders (pending, confirmed, preparing, ready - not delivered/cancelled)
                status = order_data.get('status', '').lower()
                if status in ['pending', 'confirmed', 'preparing', 'ready']:
                    pending_orders += 1

                # Calculate total revenue (only delivered orders)
                if status == 'delivered':
                    # Use net_amount if available, otherwise use total_amount
                    order_amount = order_data.get('net_amount', 0) or order_data.get('total_amount', 0)
                    if order_amount:
                        try:
                            total_revenue += float(order_amount)
                        except (ValueError, TypeError):
                            total_revenue += 0

        # Get reviews for this restaurant
        reviews_ref = db.reference(f'restaurant_reviews/{restaurant_id}')
        reviews_data = reviews_ref.get() or {}

        reviews_list = []
        total_stars = 0
        star_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

        for review_id, review_data in reviews_data.items():
            if isinstance(review_data, dict):
                review_data['id'] = review_id
                reviews_list.append(review_data)

                # Calculate star distribution
                try:
                    stars = int(review_data.get('stars', 0) or 0)
                    if 1 <= stars <= 5:
                        total_stars += stars
                        star_distribution[stars] += 1
                except (ValueError, TypeError):
                    pass

        # Sort reviews by created_at (newest first)
        reviews_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)

        # Calculate average rating
        total_reviews = len(reviews_list)
        average_rating = 0.0
        if total_reviews > 0:
            average_rating = total_stars / total_reviews

        # Update restaurant rating in Firebase (async - don't wait)
        if total_reviews > 0:
            rest_ref.update({
                'rating': round(average_rating, 1),
                'reviews': total_reviews
            })

        # Prepare stats dictionary
        stats = {
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'total_revenue': total_revenue,
            'average_rating': round(average_rating, 1),
            'total_reviews': total_reviews,
            'stars_1': star_distribution[1],
            'stars_2': star_distribution[2],
            'stars_3': star_distribution[3],
            'stars_4': star_distribution[4],
            'stars_5': star_distribution[5],
        }

        # Get latest 5 reviews for dashboard
        latest_reviews = reviews_list[:5]

        return render_template(
            'restaurant_dashboard.html',
            restaurant=restaurant,
            stats=stats,
            latest_reviews=latest_reviews
        )

    except Exception as e:
        print(f"Error loading dashboard: {str(e)}")
        flash(f"Error loading dashboard: {str(e)}", "danger")
        return redirect(url_for('restaurant_login'))


# Helper function to format PKR (add to your Jinja filters)
@app.template_filter('pkr')
def format_pkr(value):
    """Format number as PKR currency"""
    try:
        if value is None:
            return "PKR 0"
        amount = float(value)
        return f"PKR {amount:,.0f}"
    except (ValueError, TypeError):
        return "PKR 0"


# Register the filter
app.jinja_env.filters['pkr'] = format_pkr


# Restaurant Reviews Route - Add to app.py

@app.route('/restaurant/reviews')
def restaurant_reviews():
    """Restaurant reviews page with complete ratings and stats"""
    if 'restaurant_email' not in session:
        flash("Please log in to continue.", "warning")
        return redirect(url_for('restaurant_login'))

    try:
        restaurant_id = session.get('restaurant_id')

        # Get restaurant data
        rest_ref = db.reference(f'restaurants/{restaurant_id}')
        restaurant = rest_ref.get() or {}
        restaurant['id'] = restaurant_id

        # Get all reviews for this restaurant
        reviews_ref = db.reference(f'restaurant_reviews/{restaurant_id}')
        reviews_data = reviews_ref.get() or {}

        reviews_list = []
        total_stars = 0
        star_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

        for review_id, review_data in reviews_data.items():
            if isinstance(review_data, dict):
                review_data['id'] = review_id
                reviews_list.append(review_data)

                # Calculate star distribution
                try:
                    stars = int(review_data.get('stars', 0) or 0)
                    if 1 <= stars <= 5:
                        total_stars += stars
                        star_distribution[stars] += 1
                except (ValueError, TypeError):
                    pass

        # Sort reviews by created_at (newest first)
        reviews_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)

        # Calculate average rating
        total_reviews = len(reviews_list)
        average_rating = 0.0
        if total_reviews > 0:
            average_rating = total_stars / total_reviews

        # Prepare stats
        stats = {
            'average_rating': round(average_rating, 1),
            'total_reviews': total_reviews,
            'stars_1': star_distribution[1],
            'stars_2': star_distribution[2],
            'stars_3': star_distribution[3],
            'stars_4': star_distribution[4],
            'stars_5': star_distribution[5],
        }

        return render_template(
            'restaurant_reviews.html',
            restaurant=restaurant,
            reviews=reviews_list,
            stats=stats
        )

    except Exception as e:
        print(f"Error loading reviews: {str(e)}")
        flash(f"Error loading reviews: {str(e)}", "danger")
        return redirect(url_for('restaurant_dashboard'))


@app.route('/restaurant_logout')
def restaurant_logout():
    session.pop('restaurant_email', None)
    session.pop('restaurant_id', None)
    session.pop('restaurant_name', None)
    flash("Restaurant logged out successfully.", "success")
    return redirect(url_for('home'))


# Menu Management Routes - Fixed Version
@app.route('/restaurant/menu')
def restaurant_menu():
    if 'restaurant_email' not in session:
        flash("Please log in to continue.", "warning")
        return redirect(url_for('restaurant_login'))

    # Get restaurant data
    ref = db.reference('restaurants')
    restaurants = ref.get()
    restaurant = None
    restaurant_id = session.get('restaurant_id')

    for rid, rest in restaurants.items():
        if rid == restaurant_id:
            restaurant = rest
            break

    if not restaurant:
        flash("Restaurant not found.", "danger")
        return redirect(url_for('restaurant_login'))

    # Get menu items
    menu_ref = db.reference(f'menu/{restaurant_id}')
    menu_items = menu_ref.get() or {}

    # Convert to list for template
    menu_list = []
    if menu_items:
        for item_id, item_data in menu_items.items():
            if isinstance(item_data, dict):  # Ensure it's a menu item
                item_data['id'] = item_id
                menu_list.append(item_data)

    # Get categories for dropdown
    categories = ['Appetizers', 'Main Course', 'Biryani', 'Chinese', 'BBQ', 'Seafood',
                  'Vegetarian', 'Desserts', 'Beverages', 'Specials']

    return render_template('menu_management.html',
                           restaurant=restaurant,
                           menu_items=menu_list,
                           categories=categories)


@app.route('/restaurant/menu/add', methods=['POST'])
def add_menu_item():
    if 'restaurant_email' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})

    try:
        restaurant_id = session.get('restaurant_id')

        # Get form data
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        price = request.form.get('price', '0').strip()
        category = request.form.get('category', '').strip()
        preparation_time = request.form.get('preparation_time', '15-20 mins').strip()
        spice_level = request.form.get('spice_level', 'Medium')
        is_available = request.form.get('is_available') == 'on'

        # Convert price to float safely
        try:
            price = float(price)
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid price format'})

        # Handle image upload
        image_url = ""
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file and image_file.filename != '' and allowed_file(image_file.filename):
                filename = secure_filename(image_file.filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"menu_{timestamp}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image_file.save(filepath)
                image_url = url_for('static', filename=f'images/{filename}')

        # Validate required fields
        if not name or not category or price <= 0:
            return jsonify({'success': False, 'message': 'Please fill all required fields'})

        # Prepare menu item data
        menu_item = {
            'name': name,
            'description': description,
            'price': price,
            'category': category,
            'preparation_time': preparation_time,
            'spice_level': spice_level,
            'is_available': is_available,
            'image_url': image_url,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'rating': 0,
            'total_orders': 0
        }

        # Save to Firebase
        menu_ref = db.reference(f'menu/{restaurant_id}')
        menu_ref.push(menu_item)

        return jsonify({'success': True, 'message': 'Menu item added successfully!'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/restaurant/menu/update/<item_id>', methods=['POST'])
def update_menu_item(item_id):
    if 'restaurant_email' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})

    try:
        restaurant_id = session.get('restaurant_id')

        # Get form data
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        price = request.form.get('price', '0').strip()
        category = request.form.get('category', '').strip()
        preparation_time = request.form.get('preparation_time', '15-20 mins').strip()
        spice_level = request.form.get('spice_level', 'Medium')
        is_available = request.form.get('is_available') == 'on'

        # Convert price to float safely
        try:
            price = float(price)
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid price format'})

        # Handle image upload
        image_url = request.form.get('current_image', '')
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file and image_file.filename != '' and allowed_file(image_file.filename):
                filename = secure_filename(image_file.filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"menu_{timestamp}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image_file.save(filepath)
                image_url = url_for('static', filename=f'images/{filename}')

        # Validate required fields
        if not name or not category or price <= 0:
            return jsonify({'success': False, 'message': 'Please fill all required fields'})

        # Prepare updated data
        updated_data = {
            'name': name,
            'description': description,
            'price': price,
            'category': category,
            'preparation_time': preparation_time,
            'spice_level': spice_level,
            'is_available': is_available,
            'image_url': image_url
        }

        # Update in Firebase
        menu_ref = db.reference(f'menu/{restaurant_id}/{item_id}')
        current_data = menu_ref.get()

        if not current_data:
            return jsonify({'success': False, 'message': 'Menu item not found'})

        menu_ref.update(updated_data)

        return jsonify({'success': True, 'message': 'Menu item updated successfully!'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/restaurant/menu/delete/<item_id>', methods=['POST'])
def delete_menu_item(item_id):
    if 'restaurant_email' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})

    try:
        restaurant_id = session.get('restaurant_id')

        # Check if item exists
        menu_ref = db.reference(f'menu/{restaurant_id}/{item_id}')
        current_data = menu_ref.get()

        if not current_data:
            return jsonify({'success': False, 'message': 'Menu item not found'})

        # Delete from Firebase
        menu_ref.delete()

        return jsonify({'success': True, 'message': 'Menu item deleted successfully!'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/restaurant/menu/toggle_availability/<item_id>', methods=['POST'])
def toggle_menu_availability(item_id):
    if 'restaurant_email' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})

    try:
        restaurant_id = session.get('restaurant_id')

        # Get current item data
        menu_ref = db.reference(f'menu/{restaurant_id}/{item_id}')
        current_item = menu_ref.get()

        if not current_item:
            return jsonify({'success': False, 'message': 'Menu item not found'})

        # Toggle availability
        new_status = not current_item.get('is_available', True)
        menu_ref.update({'is_available': new_status})

        status_text = "available" if new_status else "unavailable"
        return jsonify({
            'success': True,
            'message': f'Item marked as {status_text}!',
            'is_available': new_status
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})



@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for('home'))
# Add this custom filter for spice level display
@app.template_filter('spice_level_to_number')
def spice_level_to_number(spice_level):
    spice_map = {
        'Mild': 1,
        'Medium': 3,
        'Spicy': 4,
        'Very Spicy': 5
    }
    return spice_map.get(spice_level, 2)



# Email configuration
EMAIL_USER = os.getenv('SMTP_USER', '')
EMAIL_PASSWORD = os.getenv('SMTP_PASSWORD', '')


def send_restaurant_email(restaurant_email, restaurant_name, status, reason=""):
    """Send email notification to restaurant about approval status"""
    try:
        # Initialize yagmail
        yag = mail_client(EMAIL_USER, EMAIL_PASSWORD)

        if status == "approved":
            subject = f"🎉 Your Restaurant {restaurant_name} Has Been Approved!"
            content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #22c55e; text-align: center;">Welcome to Health Tailor! 🎉</h2>

                <div style="background: #f0fdf4; padding: 20px; border-radius: 10px; border-left: 4px solid #22c55e;">
                    <h3 style="color: #166534; margin-top: 0;">Great News!</h3>
                    <p style="color: #166534; font-size: 16px;">
                        Your restaurant <strong>{restaurant_name}</strong> has been approved and is now live on Health Tailor platform.
                    </p>
                </div>

                <div style="margin: 20px 0;">
                    <p style="color: #374151;">You can now:</p>
                    <ul style="color: #374151;">
                        <li>Login to your restaurant dashboard</li>
                        <li>Manage your menu items</li>
                        <li>Receive orders from customers</li>
                        <li>Update your restaurant information</li>
                    </ul>
                </div>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="{url_for('restaurant_login', _external=True)}" 
                       style="background: #22c55e; color: white; padding: 12px 30px; text-decoration: none; border-radius: 8px; font-weight: bold;">
                       Login to Dashboard
                    </a>
                </div>

                <div style="border-top: 1px solid #e5e7eb; padding-top: 20px; color: #6b7280;">
                    <p>If you have any questions, please contact our support team.</p>
                    <p>Best regards,<br>Health Tailor Team</p>
                </div>
            </div>
            """
        else:
            subject = f"❌ Your Restaurant {restaurant_name} Application Status"
            content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #dc2626; text-align: center;">Application Update</h2>

                <div style="background: #fef2f2; padding: 20px; border-radius: 10px; border-left: 4px solid #dc2626;">
                    <h3 style="color: #991b1b; margin-top: 0;">Application Review</h3>
                    <p style="color: #991b1b; font-size: 16px;">
                        After careful review, we regret to inform you that your restaurant <strong>{restaurant_name}</strong> 
                        has not been approved at this time.
                    </p>
                    {f'<p style="color: #991b1b;"><strong>Reason:</strong> {reason}</p>' if reason else ''}
                </div>

                <div style="margin: 20px 0;">
                    <p style="color: #374151;">You may:</p>
                    <ul style="color: #374151;">
                        <li>Review your application information</li>
                        <li>Ensure all required documents are provided</li>
                        <li>Contact support for more information</li>
                        <li>Re-apply with corrected information</li>
                    </ul>
                </div>

                <div style="border-top: 1px solid #e5e7eb; padding-top: 20px; color: #6b7280;">
                    <p>If you have any questions, please contact our support team.</p>
                    <p>Best regards,<br>Health Tailor Team</p>
                </div>
            </div>
            """

        # Send email
        yag.send(
            to=restaurant_email,
            subject=subject,
            contents=content
        )

        return True
    except Exception as e:
        print(f"Email sending failed: {str(e)}")
        return False


# Admin Restaurant Management Routes
@app.route('/admin/restaurants')
def admin_restaurants():
    if not session.get('admin'):
        flash("Please login as admin first.", "warning")
        return redirect(url_for('admin_login'))

    # Get all restaurants
    ref = db.reference('restaurants')
    restaurants_data = ref.get() or {}

    # Convert to list and separate by status
    restaurants_list = []
    pending_restaurants = []
    approved_restaurants = []

    for rest_id, rest_data in restaurants_data.items():
        if isinstance(rest_data, dict):
            rest_data['id'] = rest_id
            restaurants_list.append(rest_data)

            if str(rest_data.get('status', 'false')).lower() == 'true':
                approved_restaurants.append(rest_data)
            else:
                pending_restaurants.append(rest_data)

    stats = {
        'total': len(restaurants_list),
        'pending': len(pending_restaurants),
        'approved': len(approved_restaurants)
    }

    return render_template('admin_restaurants.html',
                           restaurants=restaurants_list,
                           pending_restaurants=pending_restaurants,
                           approved_restaurants=approved_restaurants,
                           stats=stats)


@app.route('/admin/restaurant/view/<restaurant_id>')
def view_restaurant(restaurant_id):
    if not session.get('admin'):
        flash("Please login as admin first.", "warning")
        return redirect(url_for('admin_login'))

    # Get restaurant data
    ref = db.reference(f'restaurants/{restaurant_id}')
    restaurant = ref.get()

    if not restaurant:
        flash("Restaurant not found.", "danger")
        return redirect(url_for('admin_restaurants'))

    restaurant['id'] = restaurant_id

    return render_template('view_restaurant.html', restaurant=restaurant)


@app.route('/admin/restaurant/approve/<restaurant_id>', methods=['POST'])
def approve_restaurant(restaurant_id):
    if not session.get('admin'):
        return jsonify({'success': False, 'message': 'Admin access required'})

    try:
        # Update restaurant status
        ref = db.reference(f'restaurants/{restaurant_id}')
        restaurant = ref.get()

        if not restaurant:
            return jsonify({'success': False, 'message': 'Restaurant not found'})

        # Update status
        ref.update({
            'status': True,
            'approved_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'approved_by': session.get('admin_email', 'admin')
        })

        # Send approval email
        email_sent = send_restaurant_email(
            restaurant.get('email'),
            restaurant.get('restaurant_name'),
            "approved"
        )

        message = "Restaurant approved successfully!"
        if email_sent:
            message += " Notification email sent to restaurant."
        else:
            message += " Failed to send notification email."

        return jsonify({'success': True, 'message': message})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/admin/restaurant/reject/<restaurant_id>', methods=['POST'])
def reject_restaurant(restaurant_id):
    if not session.get('admin'):
        return jsonify({'success': False, 'message': 'Admin access required'})

    try:
        # Get rejection reason from request
        data = request.get_json()
        reason = data.get('reason', 'Does not meet our requirements')

        # Get restaurant data before deletion for email
        ref = db.reference(f'restaurants/{restaurant_id}')
        restaurant = ref.get()

        if not restaurant:
            return jsonify({'success': False, 'message': 'Restaurant not found'})

        # Send rejection email before deletion
        email_sent = send_restaurant_email(
            restaurant.get('email'),
            restaurant.get('restaurant_name'),
            "rejected",
            reason
        )

        # Delete restaurant from database
        ref.delete()

        message = "Restaurant application rejected and removed from system."
        if email_sent:
            message += " Notification email sent to restaurant."
        else:
            message += " Failed to send notification email."

        return jsonify({'success': True, 'message': message})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


# User Restaurant Viewing Routes - FIXED VERSION
@app.route('/user/restaurants')
def user_restaurants():
    if 'user_email' not in session:
        flash("Please log in to continue.", "warning")
        return redirect(url_for('user_login'))

    # Get user data for preferences
    user_ref = db.reference('users')
    users = user_ref.get() or {}
    current_user = None
    user_id = session.get('user_id')

    for uid, user in users.items():
        if uid == user_id:
            current_user = user
            break

    if not current_user:
        flash("User not found.", "danger")
        return redirect(url_for('user_login'))

    # Get all approved restaurants
    rest_ref = db.reference('restaurants')
    restaurants_data = rest_ref.get() or {}

    approved_restaurants = []
    for rest_id, rest_data in restaurants_data.items():
        if isinstance(rest_data, dict) and str(rest_data.get('status', 'false')).lower() == 'true':
            rest_data['id'] = rest_id
            # Get menu items count
            menu_ref = db.reference(f'menu/{rest_id}')
            menu_data = menu_ref.get() or {}
            rest_data['menu_items_count'] = len(menu_data)
            approved_restaurants.append(rest_data)

    # Get user preferences
    user_dishes = current_user.get('dishes', []) if current_user else []
    user_spice = current_user.get('spice', 'Medium')
    user_city = current_user.get('city', '')

    # Filter restaurants based on user preferences
    recommended_restaurants = []
    other_restaurants = []

    for restaurant in approved_restaurants:
        # Check if restaurant matches user preferences
        restaurant_specialties = restaurant.get('specialty', [])
        matches_specialty = any(dish in restaurant_specialties for dish in user_dishes) if user_dishes else False
        matches_city = user_city.lower() in restaurant.get('city', '').lower() if user_city else False

        # Score restaurants based on matches
        score = 0
        if matches_specialty:
            score += 2
        if matches_city:
            score += 1

        restaurant['match_score'] = score

        if score > 0:
            recommended_restaurants.append(restaurant)
        else:
            other_restaurants.append(restaurant)

    # Sort recommended restaurants by match score
    recommended_restaurants.sort(key=lambda x: x['match_score'], reverse=True)

    return render_template('user_restaurants.html',
                           recommended_restaurants=recommended_restaurants,
                           other_restaurants=other_restaurants,
                           user=current_user,
                           total_restaurants=len(approved_restaurants))


@app.route('/user/restaurant/<restaurant_id>')
def user_view_restaurant(restaurant_id):
    if 'user_email' not in session:
        flash("Please log in to continue.", "warning")
        return redirect(url_for('user_login'))

    # Get user data
    user_ref = db.reference('users')
    users = user_ref.get() or {}
    current_user = None
    user_id = session.get('user_id')

    for uid, user in users.items():
        if uid == user_id:
            current_user = user
            break

    if not current_user:
        flash("User not found.", "danger")
        return redirect(url_for('user_login'))

    # Get restaurant data
    rest_ref = db.reference(f'restaurants/{restaurant_id}')
    restaurant = rest_ref.get()

    if not restaurant:
        flash("Restaurant not found.", "danger")
        return redirect(url_for('user_restaurants'))

    restaurant['id'] = restaurant_id

    # Get restaurant menu items
    menu_ref = db.reference(f'menu/{restaurant_id}')
    menu_data = menu_ref.get() or {}

    menu_items = []
    for item_id, item_data in menu_data.items():
        if isinstance(item_data, dict):
            item_data['id'] = item_id
            # Only show available items
            if item_data.get('is_available', True):
                menu_items.append(item_data)

    # Group menu items by category
    menu_by_category = {}
    for item in menu_items:
        category = item.get('category', 'Uncategorized')
        if category not in menu_by_category:
            menu_by_category[category] = []
        menu_by_category[category].append(item)

    # Get similar restaurants in the same city
    city_restaurants = []
    if restaurant.get('city'):
        rest_ref = db.reference('restaurants')
        all_restaurants = rest_ref.get() or {}

        for rid, rest_data in all_restaurants.items():
            if (rid != restaurant_id and
                    isinstance(rest_data, dict) and
                    str(rest_data.get('status', 'false')).lower() == 'true' and
                    rest_data.get('city') == restaurant.get('city')):
                rest_data['id'] = rid
                city_restaurants.append(rest_data)

    # Limit to 4 similar restaurants
    similar_restaurants = city_restaurants[:4]

    return render_template('user_view_restaurant.html',
                           restaurant=restaurant,
                           menu_by_category=menu_by_category,
                           similar_restaurants=similar_restaurants,
                           user=current_user)


@app.route('/user/restaurants/city/<city_name>')
def user_restaurants_by_city(city_name):
    if 'user_email' not in session:
        flash("Please log in to continue.", "warning")
        return redirect(url_for('user_login'))

    # Get user data
    user_ref = db.reference('users')
    users = user_ref.get() or {}
    current_user = None
    user_id = session.get('user_id')

    for uid, user in users.items():
        if uid == user_id:
            current_user = user
            break

    if not current_user:
        flash("User not found.", "danger")
        return redirect(url_for('user_login'))

    # Get restaurants by city (case-insensitive matching)
    rest_ref = db.reference('restaurants')
    restaurants_data = rest_ref.get() or {}

    city_restaurants = []
    for rest_id, rest_data in restaurants_data.items():
        if (isinstance(rest_data, dict) and
                str(rest_data.get('status', 'false')).lower() == 'true'):

            # Case-insensitive city matching
            rest_city = rest_data.get('city', '').lower()
            search_city = city_name.lower()

            if search_city in rest_city or rest_city in search_city:
                rest_data['id'] = rest_id
                # Get menu items count
                menu_ref = db.reference(f'menu/{rest_id}')
                menu_data = menu_ref.get() or {}
                rest_data['menu_items_count'] = len(menu_data)
                city_restaurants.append(rest_data)

    return render_template('user_restaurants_city.html',
                           restaurants=city_restaurants,
                           city_name=city_name.title(),  # Capitalize for display
                           total_restaurants=len(city_restaurants),
                           user=current_user)  # Add user to template context


@app.route('/user/restaurants/category/<category_name>')
def user_restaurants_by_category(category_name):
    if 'user_email' not in session:
        flash("Please log in to continue.", "warning")
        return redirect(url_for('user_login'))

    # Get user data
    user_ref = db.reference('users')
    users = user_ref.get() or {}
    current_user = None
    user_id = session.get('user_id')

    for uid, user in users.items():
        if uid == user_id:
            current_user = user
            break

    if not current_user:
        flash("User not found.", "danger")
        return redirect(url_for('user_login'))

    # Get restaurants by category/specialty
    rest_ref = db.reference('restaurants')
    restaurants_data = rest_ref.get() or {}

    category_restaurants = []
    for rest_id, rest_data in restaurants_data.items():
        if (isinstance(rest_data, dict) and
                str(rest_data.get('status', 'false')).lower() == 'true' and
                category_name in rest_data.get('specialty', [])):
            rest_data['id'] = rest_id
            # Get menu items count
            menu_ref = db.reference(f'menu/{rest_id}')
            menu_data = menu_ref.get() or {}
            rest_data['menu_items_count'] = len(menu_data)
            category_restaurants.append(rest_data)

    return render_template('user_restaurants_category.html',
                           restaurants=category_restaurants,
                           category_name=category_name,
                           total_restaurants=len(category_restaurants),
                           user=current_user)  # Add user to template context


# Cart Management Routes
@app.route('/user/cart')
def user_cart():
    if 'user_email' not in session:
        flash("Please log in to continue.", "warning")
        return redirect(url_for('user_login'))

    # Get user data
    user_ref = db.reference('users')
    users = user_ref.get() or {}
    current_user = None
    user_id = session.get('user_id')

    for uid, user in users.items():
        if uid == user_id:
            current_user = user
            break

    if not current_user:
        flash("User not found.", "danger")
        return redirect(url_for('user_login'))

    # Get cart items
    cart_ref = db.reference(f'carts/{user_id}')
    cart_data = cart_ref.get() or {}

    cart_items = []
    total_amount = 0
    total_items = 0

    if cart_data:
        for item_id, item_data in cart_data.items():
            if isinstance(item_data, dict):
                item_data['cart_item_id'] = item_id
                # Calculate subtotal for each item
                item_data['subtotal'] = item_data.get('price', 0) * item_data.get('quantity', 1)
                total_amount += item_data['subtotal']
                total_items += item_data.get('quantity', 1)
                cart_items.append(item_data)

    return render_template('user_cart.html',
                           cart_items=cart_items,
                           total_amount=total_amount,
                           total_items=total_items,
                           user=current_user)


@app.route('/user/cart/add/<restaurant_id>/<menu_item_id>', methods=['POST'])
def add_to_cart(restaurant_id, menu_item_id):
    if 'user_email' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})

    try:
        user_id = session.get('user_id')

        # Get menu item details
        menu_ref = db.reference(f'menu/{restaurant_id}/{menu_item_id}')
        menu_item = menu_ref.get()

        if not menu_item:
            return jsonify({'success': False, 'message': 'Menu item not found'})

        if not menu_item.get('is_available', True):
            return jsonify({'success': False, 'message': 'This item is currently unavailable'})

        # Get restaurant details
        rest_ref = db.reference(f'restaurants/{restaurant_id}')
        restaurant = rest_ref.get()

        if not restaurant:
            return jsonify({'success': False, 'message': 'Restaurant not found'})

        # Check if cart already has items from different restaurant
        cart_ref = db.reference(f'carts/{user_id}')
        cart_data = cart_ref.get() or {}

        if cart_data:
            # Get the restaurant ID of the first item in cart
            first_item = next(iter(cart_data.values()))
            if first_item.get('restaurant_id') != restaurant_id:
                return jsonify({
                    'success': False,
                    'message': f'Your cart contains items from another restaurant. Please clear your cart or complete that order first.'
                })

        # Prepare cart item data
        cart_item = {
            'menu_item_id': menu_item_id,
            'restaurant_id': restaurant_id,
            'restaurant_name': restaurant.get('restaurant_name'),
            'name': menu_item.get('name'),
            'price': float(menu_item.get('price', 0)),
            'image_url': menu_item.get('image_url', ''),
            'spice_level': menu_item.get('spice_level', 'Medium'),
            'preparation_time': menu_item.get('preparation_time', '15-20 mins'),
            'quantity': 1,
            'added_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Check if item already exists in cart
        existing_item_id = None
        for cart_item_id, item_data in cart_data.items():
            if (isinstance(item_data, dict) and
                    item_data.get('menu_item_id') == menu_item_id and
                    item_data.get('restaurant_id') == restaurant_id):
                existing_item_id = cart_item_id
                break

        if existing_item_id:
            # Update quantity
            existing_ref = db.reference(f'carts/{user_id}/{existing_item_id}')
            existing_data = existing_ref.get()
            new_quantity = existing_data.get('quantity', 1) + 1
            existing_ref.update({
                'quantity': new_quantity,
                'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            message = f'Quantity updated! Now {new_quantity} in cart.'
        else:
            # Add new item
            cart_ref.push(cart_item)
            message = 'Item added to cart successfully!'

        # Get updated cart count
        updated_cart = cart_ref.get() or {}
        cart_count = sum(item.get('quantity', 1) for item in updated_cart.values() if isinstance(item, dict))

        return jsonify({
            'success': True,
            'message': message,
            'cart_count': cart_count
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/user/cart/update/<cart_item_id>', methods=['POST'])
def update_cart_item(cart_item_id):
    if 'user_email' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})

    try:
        user_id = session.get('user_id')
        data = request.get_json()
        quantity = data.get('quantity', 1)

        if quantity < 1:
            return jsonify({'success': False, 'message': 'Quantity must be at least 1'})

        # Update cart item
        cart_ref = db.reference(f'carts/{user_id}/{cart_item_id}')
        cart_ref.update({
            'quantity': quantity,
            'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        # Get updated cart totals
        cart_data = db.reference(f'carts/{user_id}').get() or {}
        total_amount = 0
        total_items = 0

        for item_data in cart_data.values():
            if isinstance(item_data, dict):
                total_amount += item_data.get('price', 0) * item_data.get('quantity', 1)
                total_items += item_data.get('quantity', 1)

        return jsonify({
            'success': True,
            'message': 'Cart updated successfully!',
            'total_amount': total_amount,
            'total_items': total_items
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/user/cart/remove/<cart_item_id>', methods=['POST'])
def remove_cart_item(cart_item_id):
    if 'user_email' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})

    try:
        user_id = session.get('user_id')

        # Remove item from cart
        cart_ref = db.reference(f'carts/{user_id}/{cart_item_id}')
        cart_ref.delete()

        # Get updated cart totals
        cart_data = db.reference(f'carts/{user_id}').get() or {}
        total_amount = 0
        total_items = 0

        for item_data in cart_data.values():
            if isinstance(item_data, dict):
                total_amount += item_data.get('price', 0) * item_data.get('quantity', 1)
                total_items += item_data.get('quantity', 1)

        return jsonify({
            'success': True,
            'message': 'Item removed from cart!',
            'total_amount': total_amount,
            'total_items': total_items
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/user/cart/clear', methods=['POST'])
def clear_cart():
    if 'user_email' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})

    try:
        user_id = session.get('user_id')

        # Clear entire cart
        cart_ref = db.reference(f'carts/{user_id}')
        cart_ref.delete()

        return jsonify({
            'success': True,
            'message': 'Cart cleared successfully!',
            'total_amount': 0,
            'total_items': 0
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


# Update user_base.html to show cart count
@app.context_processor
def inject_cart_count():
    cart_count = 0
    if 'user_email' in session:
        user_id = session.get('user_id')
        if user_id:
            cart_ref = db.reference(f'carts/{user_id}')
            cart_data = cart_ref.get() or {}
            cart_count = sum(item.get('quantity', 1) for item in cart_data.values() if isinstance(item, dict))
    return {'cart_count': cart_count}


# Wallet & Checkout Routes
@app.route('/user/wallet')
def user_wallet():
    if 'user_email' not in session:
        flash("Please log in to continue.", "warning")
        return redirect(url_for('user_login'))

    # Get user data
    user_ref = db.reference('users')
    users = user_ref.get() or {}
    current_user = None
    user_id = session.get('user_id')

    for uid, user in users.items():
        if uid == user_id:
            current_user = user
            break

    if not current_user:
        flash("User not found.", "danger")
        return redirect(url_for('user_login'))

    # Get wallet data
    wallet_ref = db.reference(f'wallets/{user_id}')
    wallet_data = wallet_ref.get() or {}

    # Get wallet transactions
    transactions_ref = db.reference(f'wallet_transactions/{user_id}')
    transactions_data = transactions_ref.get() or {}

    transactions = []
    if transactions_data:
        for trans_id, trans_data in transactions_data.items():
            if isinstance(trans_data, dict):
                trans_data['id'] = trans_id
                transactions.append(trans_data)

    # Sort transactions by date (newest first)
    transactions.sort(key=lambda x: x.get('created_at', ''), reverse=True)

    return render_template('user_wallet.html',
                           wallet=wallet_data,
                           transactions=transactions,
                           user=current_user)


@app.route('/user/wallet/recharge', methods=['POST'])
def wallet_recharge():
    if 'user_email' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})

    try:
        user_id = session.get('user_id')
        data = request.get_json()

        amount = float(data.get('amount', 0))
        cnic = data.get('cnic', '').strip()
        mobile_number = data.get('mobile_number', '').strip()
        payment_method = data.get('payment_method', '')
        receipt_url = data.get('receipt_url', '')

        # Validation
        if not math.isfinite(amount) or amount <= 0:
            return jsonify({'success': False, 'message': 'Invalid amount'})

        if not cnic or len(cnic) != 13:
            return jsonify({'success': False, 'message': 'Invalid CNIC (13 digits required)'})

        if not mobile_number or len(mobile_number) != 11:
            return jsonify({'success': False, 'message': 'Invalid mobile number (11 digits required)'})

        if not payment_method:
            return jsonify({'success': False, 'message': 'Please select payment method'})

        # Create recharge request
        recharge_data = {
            'user_id': user_id,
            'user_email': session.get('user_email'),
            'user_name': session.get('user_name', 'User'),
            'amount': amount,
            'cnic': cnic,
            'mobile_number': mobile_number,
            'payment_method': payment_method,
            'receipt_url': receipt_url,
            'status': 'pending',  # pending, approved, rejected
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'processed_at': None,
            'processed_by': None
        }

        # Save to recharge requests
        recharge_ref = db.reference('wallet_recharge_requests')
        recharge_ref.push(recharge_data)

        return jsonify({
            'success': True,
            'message': 'Recharge request submitted successfully! It will be processed within 24 hours.'
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/user/checkout', methods=['POST'])
def checkout():
    if 'user_email' not in session:
        return jsonify(success=False, message='Please login first'), 401
    try:
        order_id, order, balance = place_order(db, session.get('user_id'), dict(session), request.get_json(silent=True) or {})
        for notify in (send_order_confirmation_email, send_order_notification_to_restaurant):
            try:
                notify(order)
            except Exception:
                app.logger.warning('Order saved; email notification unavailable')
        return jsonify(success=True, message='Order placed.', order_id=order_id, order_number=order['order_number'], new_balance=balance)
    except ValueError as exc:
        return jsonify(success=False, message=str(exc)), 409


# Email Functions
def send_order_confirmation_email(order_data):
    """Send order confirmation email to user"""
    try:
        yag = mail_client(EMAIL_USER, EMAIL_PASSWORD)

        subject = f"🎉 Order Confirmed - #{order_data['order_number']}"
        content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #22c55e; text-align: center;">Order Confirmed! 🎉</h2>

            <div style="background: #f0fdf4; padding: 20px; border-radius: 10px; border-left: 4px solid #22c55e;">
                <h3 style="color: #166534; margin-top: 0;">Order Details</h3>
                <p><strong>Order Number:</strong> {order_data['order_number']}</p>
                <p><strong>Restaurant:</strong> {order_data['restaurant_name']}</p>
                <p><strong>Total Amount:</strong> PKR {order_data['total_amount']:.2f}</p>
                <p><strong>Status:</strong> {order_data['status'].title()}</p>
            </div>

            <div style="margin: 20px 0;">
                <h4 style="color: #374151;">Order Items:</h4>
                <ul>
        """

        for item in order_data['items']:
            content += f"<li>{item['name']} x {item['quantity']} - PKR {item['price'] * item['quantity']:.2f}</li>"

        content += f"""
                </ul>
            </div>

            <div style="border-top: 1px solid #e5e7eb; padding-top: 20px; color: #6b7280;">
                <p>Thank you for your order! We'll notify you when your order is on its way.</p>
                <p>Best regards,<br>Health Tailor Team</p>
            </div>
        </div>
        """

        yag.send(
            to=order_data['user_email'],
            subject=subject,
            contents=content
        )

        return True
    except Exception as e:
        print(f"Order confirmation email failed: {str(e)}")
        return False


def send_order_notification_to_restaurant(order_data):
    """Send order notification to restaurant"""
    try:
        # Get restaurant email
        rest_ref = db.reference(f'restaurants/{order_data["restaurant_id"]}')
        restaurant = rest_ref.get()

        if not restaurant or not restaurant.get('email'):
            return False

        yag = mail_client(EMAIL_USER, EMAIL_PASSWORD)

        subject = f"🆕 New Order - #{order_data['order_number']}"
        content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #3b82f6; text-align: center;">New Order Received! 🆕</h2>

            <div style="background: #eff6ff; padding: 20px; border-radius: 10px; border-left: 4px solid #3b82f6;">
                <h3 style="color: #1e40af; margin-top: 0;">Order Details</h3>
                <p><strong>Order Number:</strong> {order_data['order_number']}</p>
                <p><strong>Customer:</strong> {order_data['user_name']}</p>
                <p><strong>Total Amount:</strong> PKR {order_data['total_amount']:.2f}</p>
                <p><strong>Delivery Instructions:</strong> {order_data.get('delivery_instructions', 'None')}</p>
            </div>

            <div style="margin: 20px 0;">
                <h4 style="color: #374151;">Order Items:</h4>
                <ul>
        """

        for item in order_data['items']:
            content += f"<li>{item['name']} x {item['quantity']} - PKR {item['price'] * item['quantity']:.2f}</li>"

        content += f"""
                </ul>
            </div>

            <div style="text-align: center; margin: 30px 0;">
                <a href="{url_for('restaurant_orders', _external=True)}" 
                   style="background: #3b82f6; color: white; padding: 12px 30px; text-decoration: none; border-radius: 8px; font-weight: bold;">
                   View Order in Dashboard
                </a>
            </div>
        </div>
        """

        yag.send(
            to=restaurant['email'],
            subject=subject,
            contents=content
        )

        return True
    except Exception as e:
        print(f"Restaurant notification email failed: {str(e)}")
        return False


# Admin Routes for Wallet Management
@app.route('/admin/wallet_requests')
def admin_wallet_requests():
    if not session.get('admin'):
        flash("Please login as admin first.", "warning")
        return redirect(url_for('admin_login'))

    # Get all pending recharge requests
    recharge_ref = db.reference('wallet_recharge_requests')
    recharge_data = recharge_ref.get() or {}

    pending_requests = []
    for req_id, req_data in recharge_data.items():
        if isinstance(req_data, dict) and req_data.get('status') == 'pending':
            req_data['id'] = req_id
            pending_requests.append(req_data)

    return render_template('admin_wallet_requests.html',
                           pending_requests=pending_requests)


@app.route('/admin/wallet/approve/<request_id>', methods=['POST'])
def approve_wallet_request(request_id):
    if not session.get('admin'):
        return jsonify(success=False, message='Admin access required'), 403
    try:
        approve_recharge(db, request_id)
        return jsonify(success=True, message='Recharge approved once and recorded.')
    except ValueError as exc:
        return jsonify(success=False, message=str(exc)), 409


@app.route('/admin/wallet/reject/<request_id>', methods=['POST'])
def reject_wallet_request(request_id):
    if not session.get('admin'):
        return jsonify({'success': False, 'message': 'Admin access required'})

    try:
        # Update request status
        recharge_ref = db.reference(f'wallet_recharge_requests/{request_id}')
        recharge_ref.update({
            'status': 'rejected',
            'processed_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'processed_by': session.get('admin_email', 'admin')
        })

        return jsonify({
            'success': True,
            'message': 'Wallet recharge request rejected!'
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


def send_wallet_approval_email(request_data, new_balance):
    """Send wallet approval email to user"""
    try:
        yag = mail_client(EMAIL_USER, EMAIL_PASSWORD)

        subject = "✅ Wallet Recharge Approved"
        content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #22c55e; text-align: center;">Wallet Recharge Approved! ✅</h2>

            <div style="background: #f0fdf4; padding: 20px; border-radius: 10px; border-left: 4px solid #22c55e;">
                <h3 style="color: #166534; margin-top: 0;">Transaction Details</h3>
                <p><strong>Amount Added:</strong> PKR {request_data['amount']:.2f}</p>
                <p><strong>New Balance:</strong> PKR {new_balance:.2f}</p>
                <p><strong>Payment Method:</strong> {request_data['payment_method']}</p>
            </div>

            <div style="margin: 20px 0;">
                <p style="color: #374151;">You can now use your wallet balance to place orders on Health Tailor.</p>
            </div>

            <div style="text-align: center; margin: 30px 0;">
                <a href="{url_for('user_restaurants', _external=True)}" 
                   style="background: #22c55e; color: white; padding: 12px 30px; text-decoration: none; border-radius: 8px; font-weight: bold;">
                   Start Ordering
                </a>
            </div>
        </div>
        """

        yag.send(
            to=request_data['user_email'],
            subject=subject,
            contents=content
        )

        return True
    except Exception as e:
        print(f"Wallet approval email failed: {str(e)}")
        return False


def get_current_user():
    """Helper function to get current user safely"""
    if 'user_email' not in session:
        return None

    user_ref = db.reference('users')
    users = user_ref.get() or {}
    user_id = session.get('user_id')

    if users and user_id:
        for uid, user_data in users.items():
            if uid == user_id and isinstance(user_data, dict):
                return user_data
    return None


@app.route('/user/orders')
def user_orders():
    current_user = get_current_user()
    if not current_user:
        flash("Please log in to continue.", "warning")
        return redirect(url_for('user_login'))

    try:
        user_id = session.get('user_id')

        # Get user orders from Firebase
        orders_ref = db.reference('orders')
        orders_data = orders_ref.get()

        user_orders = []
        if orders_data:
            for order_id, order_data in orders_data.items():
                # Check if order belongs to current user and is a dictionary
                if (isinstance(order_data, dict) and
                        order_data.get('user_id') == user_id):
                    order_data['id'] = order_id
                    user_orders.append(order_data)

        # Sort orders by date (newest first)
        user_orders.sort(key=lambda x: x.get('created_at', ''), reverse=True)

        return render_template('user_orders.html',
                               orders=user_orders,
                               user=current_user)

    except Exception as e:
        print(f"Error in user_orders: {str(e)}")
        flash("Error loading orders. Please try again.", "error")
        return render_template('user_orders.html', orders=[], user=current_user)

@app.route('/user/order/<order_id>')
def user_order_details(order_id):
    if 'user_email' not in session:
        flash("Please log in to continue.", "warning")
        return redirect(url_for('user_login'))

    # Get user data
    user_ref = db.reference('users')
    users = user_ref.get() or {}
    current_user = None
    user_id = session.get('user_id')

    for uid, user in users.items():
        if uid == user_id:
            current_user = user
            break

    if not current_user:
        flash("User not found.", "danger")
        return redirect(url_for('user_login'))

    # Get order data
    order_ref = db.reference(f'orders/{order_id}')
    order_data = order_ref.get()

    if not order_data:
        flash("Order not found.", "danger")
        return redirect(url_for('user_orders'))

    # Check if order belongs to current user
    if order_data.get('user_id') != user_id:
        flash("Access denied.", "danger")
        return redirect(url_for('user_orders'))

    order_data['id'] = order_id

    return render_template('user_order_details.html',
                           order=order_data,
                           user=current_user)


@app.route('/user/order/cancel/<order_id>', methods=['POST'])
def cancel_order(order_id):
    if 'user_email' not in session:
        return jsonify(success=False, message='Please login first'), 401
    try:
        refund_order(db, order_id, session.get('user_id'))
        return jsonify(success=True, message='Order cancelled and refund recorded.')
    except ValueError as exc:
        return jsonify(success=False, message=str(exc)), 409


def send_order_cancellation_email(order_data):
    """Send order cancellation email to user"""
    try:
        yag = mail_client(EMAIL_USER, EMAIL_PASSWORD)

        subject = f"❌ Order Cancelled - #{order_data['order_number']}"
        content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #dc2626; text-align: center;">Order Cancelled ❌</h2>

            <div style="background: #fef2f2; padding: 20px; border-radius: 10px; border-left: 4px solid #dc2626;">
                <h3 style="color: #991b1b; margin-top: 0;">Order Details</h3>
                <p><strong>Order Number:</strong> {order_data['order_number']}</p>
                <p><strong>Restaurant:</strong> {order_data['restaurant_name']}</p>
                <p><strong>Total Amount:</strong> PKR {order_data['total_amount']:.2f}</p>
                <p><strong>Status:</strong> Cancelled</p>
            </div>

            <div style="margin: 20px 0;">
                <p style="color: #374151;">The order amount has been refunded to your wallet balance.</p>
            </div>

            <div style="border-top: 1px solid #e5e7eb; padding-top: 20px; color: #6b7280;">
                <p>If you have any questions, please contact our support team.</p>
                <p>Best regards,<br>Health Tailor Team</p>
            </div>
        </div>
        """

        yag.send(
            to=order_data['user_email'],
            subject=subject,
            contents=content
        )

        return True
    except Exception as e:
        print(f"Order cancellation email failed: {str(e)}")
        return False



@app.route('/restaurant/my_orders')
def restaurant_orders():
    return restaurant_orders_feed()


@app.route('/restaurant/order/<order_id>')
def view_order_details(order_id):
    if 'restaurant_email' not in session:
        flash("Please log in to continue.", "warning")
        return redirect(url_for('restaurant_login'))

    try:
        restaurant_id = session.get('restaurant_id')

        # Get restaurant data
        rest_ref = db.reference(f'restaurants/{restaurant_id}')
        restaurant = rest_ref.get()

        if not restaurant:
            flash("Restaurant not found.", "danger")
            return redirect(url_for('restaurant_login'))

        # Get order data
        order_ref = db.reference(f'orders/{order_id}')
        order_data = order_ref.get()

        if not order_data:
            flash("Order not found.", "danger")
            return redirect(url_for('restaurant_orders'))

        # Check if order belongs to this restaurant
        if order_data.get('restaurant_id') != restaurant_id:
            flash("Access denied.", "danger")
            return redirect(url_for('restaurant_orders'))

        order_data['id'] = order_id

        return render_template('order_details.html',
                               order=order_data,
                               restaurant=restaurant)

    except Exception as e:
        print(f"Error in view_order_details: {str(e)}")
        import traceback
        traceback.print_exc()
        flash("Error loading order details. Please try again.", "error")
        return redirect(url_for('restaurant_orders'))




@app.route('/my_orders')
def my_orders():
    if 'user_email' not in session:
        flash("Please log in to view your orders.", "warning")
        return redirect(url_for('user_login'))

    user_id = session.get('user_id')

    # Get user
    user_ref = db.reference('users')
    users = user_ref.get() or {} or {}
    user = users.get(user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('user_login'))

    # Get restaurants
    restaurant_ref = db.reference('restaurants')
    restaurants = restaurant_ref.get() or {}

    # Get orders
    order_ref = db.reference('orders')
    orders_data = order_ref.get() or {}

    user_orders = []
    for order_id, order in orders_data.items():
        if order.get('user_id') == user_id:
            order['id'] = order_id
            # Get restaurant details
            rest_id = order.get('restaurant_id')
            order['restaurant_info'] = restaurants.get(rest_id, {})
            user_orders.append(order)

    user_orders.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    return render_template("my_orders.html", user=user, orders=user_orders)




# Configure Gemini AI
model = get_model()


@app.route('/health_analysis', methods=['GET', 'POST'])
def health_analysis():
    if 'user_email' not in session:
        flash("Please log in to continue.", "warning")
        return redirect(url_for('user_login'))

    # Get current user data
    user_ref = db.reference('users')
    users = user_ref.get() or {}
    current_user = None
    user_id = session.get('user_id')

    for uid, user in users.items():
        if uid == user_id:
            current_user = user
            break

    if not current_user:
        flash("User not found.", "danger")
        return redirect(url_for('user_dashboard'))

    analysis_result = None
    recommended_dishes = None

    if request.method == 'POST':
        if request.form.get('ai_consent') != 'yes':
            flash('Please consent before sharing your dietary profile with the AI provider.', 'warning')
            return redirect(url_for('health_analysis'))
        try:
            # Check if it's dish analysis or recommendations request
            if 'get_recommendations' in request.form:
                # Get personalized recommendations from Gemini - NO IMAGE NEEDED
                recommended_dishes = get_personalized_recommendations(current_user)
                flash("Food ideas generated. Review ingredients before ordering." if recommended_dishes else "Recommendations are unavailable. Please try again later.", "success" if recommended_dishes else "warning")

            elif 'dish_image' in request.files:
                # Dish image analysis - THIS NEEDS IMAGE
                image_file = request.files['dish_image']

                if image_file.filename == '':
                    flash("Please select an image file for analysis.", "danger")
                    return render_template('health_analysis.html',
                                           user=current_user,
                                           analysis_result=analysis_result,
                                           recommended_dishes=recommended_dishes)

                if image_file and allowed_file(image_file.filename):
                    # Read and process image
                    image_data = image_file.read()

                    # Analyze image with Gemini
                    analysis_result = analyze_dish_with_gemini(image_data, current_user)
                    flash("AI estimate ready. Confirm ingredients and portions with the restaurant." if analysis_result else "Analysis is unavailable. Please try again later; no food assessment was made.", "success" if analysis_result else "warning")

                else:
                    flash("Invalid image format. Please upload PNG, JPG, or JPEG.", "danger")

        except Exception as e:
            flash(f"Analysis failed: {str(e)}", "danger")

    return render_template('health_analysis.html',
                           user=current_user,
                           analysis_result=analysis_result,
                           recommended_dishes=recommended_dishes)


def get_personalized_recommendations(user_data):
    """Get personalized dish recommendations from Gemini AI based on user health data"""
    try:
        # Prepare user health data for Gemini
        user_profile = f"""
        User Health Profile for Dietary Recommendations:

        Personal Information:
        - Identity: not shared
        - Age: {user_data.get('age', 'Not specified')} years
        - Gender: {user_data.get('sex', 'Not specified')}
        - Location: {user_data.get('city', 'Not specified')}

        Medical Conditions:
        - Diabetes: {user_data.get('diabetes', 'No')}
        - Blood Pressure: {user_data.get('bp', 'No')}

        Dietary Preferences:
        - Preferred Spice Level: {user_data.get('spice', 'Medium')}
        - Favorite Food Types: {', '.join(user_data.get('dishes', []))}

        Please provide personalized dish recommendations based on this health profile.
        Focus on managing {user_data.get('diabetes', 'No')} diabetes and {user_data.get('bp', 'No')} blood pressure.
        Consider {user_data.get('spice', 'Medium')} spice preference and local cuisine from {user_data.get('city', 'Unknown')}.
        """

        prompt = f"""
        Suggest general food ideas, not medical advice. Do not claim clinical certainty.

        PATIENT HEALTH PROFILE:
        {user_profile}

        Provide 6 personalized dish recommendations in this exact JSON format:
        {{
          "recommendations": [
            {{
              "dish_name": "Specific dish name",
              "cuisine": "Cuisine type",
              "health_benefits": "Detailed health benefits for this patient",
              "suitability": "Why this dish is suitable for their health conditions",
              "calories": "Low/Medium/High",
              "spice_level": "Mild/Medium/Spicy",
              "preparation_tips": "Healthy preparation methods"
            }}
          ]
        }}

        Make recommendations specific to:
        - Diabetes management: {user_data.get('diabetes', 'No')}
        - Blood pressure control: {user_data.get('bp', 'No')}
        - Age considerations: {user_data.get('age', 'Not specified')}
        - Spice preference: {user_data.get('spice', 'Medium')}
        """

        # Get recommendations from Gemini
        response = model.generate_content(prompt)
        response_text = response.text

        # Parse JSON response
        import json
        import re

        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            recommendations_data = json.loads(json_match.group())
            entries = recommendations_data.get('recommendations')
            if not isinstance(entries, list) or not entries or not all(isinstance(x, dict) and isinstance(x.get('dish_name'), str) for x in entries):
                return None
            return {'recommendations': entries[:6]}
        else:
            # If JSON parsing fails, return fallback
            return get_fallback_recommendations(user_data)

    except Exception as e:
        print(f"Gemini recommendations error: {str(e)}")
        return get_fallback_recommendations(user_data)


def get_fallback_recommendations(user_data):
    return None


def analyze_dish_with_gemini(image_data, user_data):
    """Analyze dish image using Gemini AI"""
    try:
        # Prepare user health data
        user_profile = f"""
        User Health Profile:
        - Diabetes: {user_data.get('diabetes', 'No')}
        - Blood Pressure: {user_data.get('bp', 'No')}
        - Age: {user_data.get('age', 'Not specified')}
        - Preferred Spice: {user_data.get('spice', 'Medium')}
        """

        prompt = f"""
        Analyze this food image and tell if this user should eat it or not based on their health profile.

        User Profile:
        {user_profile}

        Provide simple analysis in this format:
        Dish: [Dish Name]
        Ingredients: [Main Ingredients]
        Health Risk: [Low/Medium/High]
        Should Eat: [Yes/No/In Moderation]
        Reason: [Brief reason]
        """

        # Process image and get analysis from Gemini
        from PIL import Image
        import io
        image = Image.open(io.BytesIO(image_data))
        response = model.generate_content([prompt, image])
        analysis_text = response.text

        return parse_analysis_response(analysis_text, user_data)

    except Exception as e:
        return get_fallback_analysis(user_data)


def parse_analysis_response(response_text, user_data):
    """Parse Gemini analysis response into structured format"""
    lines = response_text.split('\n')
    analysis = {
        'dish_name': 'Unknown Dish',
        'ingredients': 'Not specified',
        'health_risk': 'Medium',
        'should_eat': 'In Moderation',
        'reason': 'Consult with doctor'
    }

    for line in lines:
        line = line.strip()
        if 'Dish:' in line:
            analysis['dish_name'] = line.split('Dish:')[1].strip()
        elif 'Ingredients:' in line:
            analysis['ingredients'] = line.split('Ingredients:')[1].strip()
        elif 'Health Risk:' in line:
            analysis['health_risk'] = line.split('Health Risk:')[1].strip()
        elif 'Should Eat:' in line:
            analysis['should_eat'] = line.split('Should Eat:')[1].strip()
        elif 'Reason:' in line:
            analysis['reason'] = line.split('Reason:')[1].strip()

    if analysis['dish_name'] == 'Unknown Dish' or analysis['ingredients'] == 'Not specified':
        return None

    # Prepare chart data based on analysis
    is_safe = analysis['should_eat'].lower() in ['yes', 'in moderation']
    chart_data = prepare_comprehensive_chart_data(analysis, is_safe, user_data)

    return {
        'analysis': analysis,
        'is_safe': is_safe,
        'chart_data': chart_data
    }


def get_fallback_analysis(user_data):
    return None


def prepare_comprehensive_chart_data(analysis, is_safe, user_data):
    # A photo cannot establish measured nutrition or a clinical safety percentage.
    return None


def calculate_health_score(analysis, user_data):
    """Calculate health score based on analysis and user profile"""
    base_score = 50

    # Adjust based on health risk
    health_risk = analysis['health_risk'].lower()
    if 'low' in health_risk:
        base_score += 30
    elif 'medium' in health_risk:
        base_score += 10
    elif 'high' in health_risk:
        base_score -= 20

    # Adjust based on recommendation
    should_eat = analysis['should_eat'].lower()
    if 'yes' in should_eat:
        base_score += 20
    elif 'moderation' in should_eat:
        base_score += 5
    elif 'no' in should_eat:
        base_score -= 25

    # Adjust for user health conditions
    diabetes = user_data.get('diabetes', 'No').lower()
    bp = user_data.get('bp', 'No').lower()

    if diabetes == 'yes' and 'carb' in analysis['reason'].lower():
        base_score -= 15
    if bp == 'yes' and 'sodium' in analysis['reason'].lower():
        base_score -= 10

    # Ensure score is within 0-100
    return max(0, min(100, base_score))



RESET_EXPIRY_MINUTES = 10  # OTP valid for 10 minutes

def _send_reset_code_email(to_email: str, code: str):
    """
    Sends an HTML email with the 8-digit reset code using yagmail.
    """
    yag = mail_client(EMAIL_USER, EMAIL_PASSWORD)
    subject = "🔐 Health Tailor Password Reset Code"
    content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
      <h2 style="color:#3b82f6; text-align:center; margin-bottom: 10px;">Password Reset</h2>
      <p style="color:#374151; font-size:16px; text-align:center;">
        Use the following <strong>8-digit code</strong> to reset your password:
      </p>
      <div style="text-align:center; margin: 20px 0;">
        <div style="display:inline-block; padding: 14px 24px; border-radius:12px; background:#111827; color:#fff; font-size:24px; letter-spacing:4px;">
          {code}
        </div>
      </div>
      <p style="color:#6b7280; text-align:center; margin-top: 4px;">
        This code will expire in <strong>{RESET_EXPIRY_MINUTES} minutes</strong>.
      </p>
      <hr style="border:none; border-top:1px solid #e5e7eb; margin:24px 0;">
      <p style="color:#6b7280; font-size:14px; text-align:center;">If you didn’t request this, you can ignore this email.</p>
    </div>
    """
    yag.send(to=to_email, subject=subject, contents=content)

def _store_reset_request(uid: str, email: str, code: str):
    """
    Stores reset data in Firebase: /password_resets/<uid>
    """
    expires_at = (datetime.now() + timedelta(minutes=RESET_EXPIRY_MINUTES)).strftime("%Y-%m-%d %H:%M:%S")
    db.reference(f'password_resets/{uid}').set({
        'email': email,
        'code': code,
        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'expires_at': expires_at
    })

def _get_reset_request(uid: str):
    return db.reference(f'password_resets/{uid}').get() or {}

def _delete_reset_request(uid: str):
    db.reference(f'password_resets/{uid}').delete()

def _is_expired(expires_at_str: str) -> bool:
    try:
        expires_at = datetime.strptime(expires_at_str, "%Y-%m-%d %H:%M:%S")
        return datetime.now() > expires_at
    except Exception:
        return True

def _password_strong(pw: str) -> str | None:
    """
    Returns None if strong; otherwise returns error message.
    Matches your signup rules.
    """
    if len(pw) < 8: return "Password must be at least 8 characters."
    if not re.search(r"[A-Z]", pw): return "Include at least one uppercase letter."
    if not re.search(r"[0-9]", pw): return "Include at least one number."
    if not re.search(r"[^A-Za-z0-9]", pw): return "Include at least one special character."
    return None

# =========================================
# 1) /forget_password
# =========================================
@app.route('/forget_password', methods=['GET', 'POST'])
def forget_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        if not email:
            flash("Please enter your email.", "warning")
            return redirect(url_for('forget_password'))

        users = db.reference('users').get() or {}
        target_uid, target_user = None, None
        for uid, info in users.items():
            if isinstance(info, dict) and info.get('email', '').strip().lower() == email:
                target_uid, target_user = uid, info
                break

        if not target_uid:
            flash("This email is not registered.", "danger")
            return redirect(url_for('forget_password'))

        # Make 8-digit OTP
        code = str(__import__('secrets').SystemRandom().randint(10_000_000, 99_999_999))
        try:
            _store_reset_request(target_uid, email, code)
            _send_reset_code_email(email, code)

            # Save minimal info in session to continue flow
            session.pop('reset_verified', None)
            session['reset_uid'] = target_uid
            session['reset_email'] = email

            flash("Verification code sent to your email.", "info")
            return redirect(url_for('verify_code'))
        except Exception as e:
            flash(f"Failed to send code: {str(e)}", "danger")
            return redirect(url_for('forget_password'))

    return render_template('forget_password.html')
# =========================================
# 2) /resend_code  (optional but useful)
# =========================================
@app.route('/resend_code', methods=['POST'])
def resend_code():
    uid = session.get('reset_uid')
    email = session.get('reset_email')
    if not uid or not email:
        flash("Session expired. Start again.", "warning")
        return redirect(url_for('forget_password'))

    code = str(__import__('secrets').SystemRandom().randint(10_000_000, 99_999_999))
    try:
        _store_reset_request(uid, email, code)
        _send_reset_code_email(email, code)
        flash("New code sent. Please check your inbox.", "info")
        return redirect(url_for('verify_code'))
    except Exception as e:
        flash(f"Failed to resend: {str(e)}", "danger")
        return redirect(url_for('verify_code'))
# =========================================
# 3) /verify_code
# =========================================
@app.route('/verify_code', methods=['GET', 'POST'])
def verify_code():
    uid = session.get('reset_uid')
    email = session.get('reset_email')
    if not uid or not email:
        flash("Session expired. Start again.", "warning")
        return redirect(url_for('forget_password'))

    info = _get_reset_request(uid)

    if request.method == 'POST':
        code_input = request.form.get('code', '').strip()
        stored_code = info.get('code', '')
        expires_at = info.get('expires_at', '')

        if not stored_code:
            flash("No active code. Please request again.", "warning")
            return redirect(url_for('forget_password'))

        if _is_expired(expires_at):
            flash("Code expired. Please request a new one.", "warning")
            return redirect(url_for('forget_password'))

        if code_input != stored_code:
            flash("Invalid code. Please try again.", "danger")
            return redirect(url_for('verify_code'))

        # Mark as verified
        session['reset_verified'] = True
        flash("Code verified. Set your new password.", "success")
        return redirect(url_for('reset_password'))

    # GET
    remaining = "unknown"
    if info.get('expires_at'):
        try:
            exp = datetime.strptime(info['expires_at'], "%Y-%m-%d %H:%M:%S")
            delta = exp - datetime.now()
            remaining = max(0, int(delta.total_seconds() // 60))
        except Exception:
            pass

    return render_template('verify_code.html', email=email, minutes_left=remaining)
# =========================================
# 4) /reset_password
# =========================================
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    uid = session.get('reset_uid')
    email = session.get('reset_email')
    verified = session.get('reset_verified', False)

    if not uid or not email:
        flash("Session expired. Start again.", "warning")
        return redirect(url_for('forget_password'))
    if not verified:
        flash("Please verify the code first.", "warning")
        return redirect(url_for('verify_code'))

    if request.method == 'POST':
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if new_password != confirm_password:
            flash("Passwords do not match.", "warning")
            return redirect(url_for('reset_password'))

        bad = _password_strong(new_password)
        if bad:
            flash(bad, "warning")
            return redirect(url_for('reset_password'))

        # Update user
        db.reference(f'users/{uid}').update({'password': generate_password_hash(new_password)})

        # Clean reset request + session
        _delete_reset_request(uid)
        session.pop('reset_uid', None)
        session.pop('reset_email', None)
        session.pop('reset_verified', None)

        flash("Password reset successful! Please log in.", "success")
        return redirect(url_for('user_login'))

    return render_template('reset_password.html', email=email)


REST_RESET_EXPIRY_MINUTES = 10  # 10 minutes validity

def rfp_send_code_email(to_email: str, code: str):
    yag = mail_client(EMAIL_USER, EMAIL_PASSWORD)
    subject = "🔐 Health Tailor Restaurant Password Reset Code"
    content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
      <h2 style="color:#3b82f6; text-align:center;">Restaurant Password Reset</h2>
      <p style="color:#374151; font-size:16px; text-align:center;">
        Use this <strong>8-digit code</strong> to reset your password:
      </p>
      <div style="text-align:center; margin: 20px 0;">
        <div style="display:inline-block; padding: 14px 24px; border-radius:12px; background:#111827; color:#fff; font-size:24px; letter-spacing:4px;">
          {code}
        </div>
      </div>
      <p style="color:#6b7280; text-align:center;">
        This code will expire in <strong>{REST_RESET_EXPIRY_MINUTES} minutes</strong>.
      </p>
      <hr style="border:none; border-top:1px solid #e5e7eb; margin:24px 0;">
      <p style="color:#6b7280; font-size:14px; text-align:center;">If you didn’t request this, ignore this email.</p>
    </div>
    """
    yag.send(to=to_email, subject=subject, contents=content)

def rfp_store(uid: str, email: str, code: str):
    expires_at = (datetime.now() + timedelta(minutes=REST_RESET_EXPIRY_MINUTES)).strftime("%Y-%m-%d %H:%M:%S")
    db.reference(f'rest_password_resets/{uid}').set({
        'email': email,
        'code': code,
        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'expires_at': expires_at
    })

def rfp_get(uid: str):
    return db.reference(f'rest_password_resets/{uid}').get() or {}

def rfp_delete(uid: str):
    db.reference(f'rest_password_resets/{uid}').delete()

def rfp_expired(expires_at_str: str) -> bool:
    try:
        return datetime.now() > datetime.strptime(expires_at_str, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return True

def rfp_password_strong(pw: str) -> str | None:
    if len(pw) < 8: return "Password must be at least 8 characters."
    if not re.search(r"[A-Z]", pw): return "Include at least one uppercase letter."
    if not re.search(r"[0-9]", pw): return "Include at least one number."
    if not re.search(r"[^A-Za-z0-9]", pw): return "Include at least one special character."
    return None

@app.route('/restaurant/forget_password', methods=['GET', 'POST'])
def restaurant_forget_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        if not email:
            flash("Please enter your restaurant email.", "warning")
            return redirect(url_for('restaurant_forget_password'))

        # Find restaurant by email
        restaurants = db.reference('restaurants').get() or {}
        rid, rdata = None, None
        for _rid, info in restaurants.items():
            if isinstance(info, dict) and info.get('email', '').strip().lower() == email:
                rid, rdata = _rid, info
                break

        if not rid:
            flash("This restaurant email is not registered.", "danger")
            return redirect(url_for('restaurant_forget_password'))

        code = str(__import__('secrets').SystemRandom().randint(10_000_000, 99_999_999))
        try:
            rfp_store(rid, email, code)
            rfp_send_code_email(email, code)
            session.pop('rfp_verified', None)
            session['rfp_rid'] = rid
            session['rfp_email'] = email
            flash("Verification code sent to your email.", "info")
            return redirect(url_for('restaurant_verify_code'))
        except Exception as e:
            flash(f"Failed to send code: {str(e)}", "danger")
            return redirect(url_for('restaurant_forget_password'))

    return render_template('restaurant_forget_password.html')
@app.route('/restaurant/resend_code', methods=['POST'])
def restaurant_resend_code():
    rid = session.get('rfp_rid')
    email = session.get('rfp_email')
    if not rid or not email:
        flash("Session expired. Start again.", "warning")
        return redirect(url_for('restaurant_forget_password'))

    code = str(__import__('secrets').SystemRandom().randint(10_000_000, 99_999_999))
    try:
        rfp_store(rid, email, code)
        rfp_send_code_email(email, code)
        flash("New code sent. Please check your inbox.", "info")
        return redirect(url_for('restaurant_verify_code'))
    except Exception as e:
        flash(f"Failed to resend: {str(e)}", "danger")
        return redirect(url_for('restaurant_verify_code'))
@app.route('/restaurant/verify_code', methods=['GET', 'POST'])
def restaurant_verify_code():
    rid = session.get('rfp_rid')
    email = session.get('rfp_email')
    if not rid or not email:
        flash("Session expired. Start again.", "warning")
        return redirect(url_for('restaurant_forget_password'))

    info = rfp_get(rid)

    if request.method == 'POST':
        code_input = request.form.get('code', '').strip()
        stored_code = info.get('code', '')
        expires_at = info.get('expires_at', '')

        if not stored_code:
            flash("No active code. Please request again.", "warning")
            return redirect(url_for('restaurant_forget_password'))

        if rfp_expired(expires_at):
            flash("Code expired. Please request a new one.", "warning")
            return redirect(url_for('restaurant_forget_password'))

        if code_input != stored_code:
            flash("Invalid code. Please try again.", "danger")
            return redirect(url_for('restaurant_verify_code'))

        session['rfp_verified'] = True
        flash("Code verified. Set your new password.", "success")
        return redirect(url_for('restaurant_reset_password'))

    # GET
    minutes_left = "unknown"
    if info.get('expires_at'):
        try:
            delta = datetime.strptime(info['expires_at'], "%Y-%m-%d %H:%M:%S") - datetime.now()
            minutes_left = max(0, int(delta.total_seconds() // 60))
        except Exception:
            pass

    return render_template('restaurant_verify_code.html', email=email, minutes_left=minutes_left)
@app.route('/restaurant/reset_password', methods=['GET', 'POST'])
def restaurant_reset_password():
    rid = session.get('rfp_rid')
    email = session.get('rfp_email')
    verified = session.get('rfp_verified', False)

    if not rid or not email:
        flash("Session expired. Start again.", "warning")
        return redirect(url_for('restaurant_forget_password'))
    if not verified:
        flash("Please verify the code first.", "warning")
        return redirect(url_for('restaurant_verify_code'))

    if request.method == 'POST':
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if new_password != confirm_password:
            flash("Passwords do not match.", "warning")
            return redirect(url_for('restaurant_reset_password'))

        bad = rfp_password_strong(new_password)
        if bad:
            flash(bad, "warning")
            return redirect(url_for('restaurant_reset_password'))

        # Update restaurant password
        db.reference(f'restaurants/{rid}').update({'password': generate_password_hash(new_password)})

        # Clean reset info
        rfp_delete(rid)
        session.pop('rfp_rid', None)
        session.pop('rfp_email', None)
        session.pop('rfp_verified', None)

        flash("Password reset successful! Please log in.", "success")
        return redirect(url_for('restaurant_login'))

    return render_template('restaurant_reset_password.html', email=email)


# ===========================
# 💰 PKR format filter
# ===========================
@app.template_filter('pkr')
def pkr(v):
    try:
        return f"PKR {float(v):,.0f}"
    except Exception:
        return f"PKR {v}"

# ===========================
# 🧮 Payout math helpers
# ===========================
def get_order_net_amount(order: dict) -> float:
    """
    Restaurant ko kitna mila? Default: items subtotal.
    Delivery fee, tax platform ka.
    # Agar commission rakhni ho to:
    # commission_rate = 0.10  # 10%
    # return max(0.0, float(order.get('subtotal', 0)) * (1 - commission_rate))
    """
    return float(order.get('subtotal', 0) or 0)

def credit_restaurant_wallet_if_needed(order_id, order):
    settle_order(db, order_id)
# ===========================
# 📥 Orders Feed (Restaurant)
# ===========================

@app.route('/restaurant/orders_feed')
def restaurant_orders_feed():
    if 'restaurant_email' not in session:
        flash("Please log in to continue.", "warning")
        return redirect(url_for('restaurant_login'))

    restaurant_id = session.get('restaurant_id')

    # Restaurant info
    rest = db.reference(f'restaurants/{restaurant_id}').get() or {}

    # filters
    status_filter = (request.args.get('status') or '').strip().lower()
    q = (request.args.get('q') or '').strip().lower()

    orders_data = db.reference('orders').get() or {}
    feed = []

    def normalize_items(order_dict):
        items = order_dict.get('items') or []
        if isinstance(items, dict):
            return [v for v in items.values() if isinstance(v, dict)]
        if isinstance(items, list):
            return [x for x in items if isinstance(x, dict)]
        return []

    for oid, od in orders_data.items():
        if not (isinstance(od, dict) and od.get('restaurant_id') == restaurant_id):
            continue

        od['id'] = oid
        od['net_amount'] = get_order_net_amount(od)   # already in your file
        od['items_list'] = normalize_items(od)

        # apply status filter
        if status_filter and (od.get('status') or '').lower() != status_filter:
            continue

        # apply search
        if q:
            hay = " ".join([
                str(od.get('order_number', '') or ''),
                str(od.get('user_email', '') or ''),
                str(od.get('user_name', '') or ''),
            ]).lower()
            if q not in hay:
                continue

        feed.append(od)

    feed.sort(key=lambda x: x.get('created_at', ''), reverse=True)

    stats = {
        'total': len(feed),
        'pending': sum(1 for o in feed if o.get('status') == 'pending'),
        'confirmed': sum(1 for o in feed if o.get('status') == 'confirmed'),
        'preparing': sum(1 for o in feed if o.get('status') == 'preparing'),
        'ready': sum(1 for o in feed if o.get('status') == 'ready'),
        'delivered': sum(1 for o in feed if o.get('status') == 'delivered'),
        'cancelled': sum(1 for o in feed if o.get('status') == 'cancelled'),
    }

    w = db.reference(f'restaurant_wallets/{restaurant_id}').get() or {}
    wallet = {'balance': float(w.get('balance', 0) or 0)}

    return render_template(
        'restaurant_orders_feed.html',
        restaurant=rest,
        orders=feed,
        stats=stats,
        wallet=wallet,
        status_filter=status_filter,
        q=q
    )


@app.route('/order_status/<order_id>', methods=['GET', 'POST'])
def order_status(order_id):
    if 'restaurant_email' not in session:
        return redirect(url_for('restaurant_login'))
    order = db.reference(f'orders/{order_id}').get()
    if not order or order.get('restaurant_id') != session.get('restaurant_id'):
        return 'Order not found', 404
    if request.method == 'POST':
        try:
            order = change_order_status(db, order_id, session.get('restaurant_id'), request.form.get('status'))
            db.reference(f'orders/{order_id}/rider').set({'name': request.form.get('rider_name', ''), 'phone': request.form.get('rider_phone', '')})
            try:
                send_order_status_email_v2(order, order['status'])
            except Exception:
                app.logger.warning('Order saved; email notification unavailable')
            flash('Order updated.', 'success')
        except ValueError as exc:
            flash(str(exc), 'warning')
        return redirect(url_for('order_status', order_id=order_id))
    order['id'] = order_id
    order['rider'] = order.get('rider') or {}
    return render_template('order_status.html', order=order)


# ---------------------------
# EMAIL SENDER (Base function)
# ---------------------------
def send_order_status_email(email, order_number, status, rider_name="", rider_phone=""):
    if not email:
        raise ValueError("User email missing in order data.")
    if not order_number:
        order_number = "N/A"

    rider_name = rider_name or "Not assigned"
    rider_phone = rider_phone or "Not available"

    yag = mail_client(EMAIL_USER, EMAIL_PASSWORD)

    subject = f"📦 Order Update - {order_number}"
    content = f"""
    <h2>Order Status Updated</h2>
    <p><b>Order:</b> {order_number}</p>
    <p><b>Status:</b> {status}</p>

    <h3>Rider Information</h3>
    <p><b>Name:</b> {rider_name}</p>
    <p><b>Phone:</b> {rider_phone}</p>

    <p>Thank you for ordering with us </p>
    """

    yag.send(to=email, subject=subject, contents=content)


# ---------------------------
# EMAIL WRAPPER (Recommended)
# ---------------------------
def send_order_status_email_v2(order_data, status):
    rider = order_data.get('rider') or {}

    return send_order_status_email(
        email=order_data.get('user_email', ''),
        order_number=order_data.get('order_number', ''),
        status=status,
        rider_name=rider.get('name', ''),
        rider_phone=rider.get('phone', '')
    )



@app.route('/restaurant/order/update_status/<order_id>', methods=['POST'])
def update_order_status(order_id):
    if 'restaurant_email' not in session:
        return jsonify(success=False, message='Please login first'), 401
    try:
        status = (request.get_json(silent=True) or {}).get('status')
        order = change_order_status(db, order_id, session.get('restaurant_id'), status)
        try:
            send_order_status_email_v2(order, status)
        except Exception:
            app.logger.warning('Order saved; email notification unavailable')
        return jsonify(success=True, message='Order updated.')
    except ValueError as exc:
        return jsonify(success=False, message=str(exc)), 409

@app.route('/orders_view')
def orders_view():
    # restaurant login required
    if 'restaurant_email' not in session:
        flash("Please log in to continue.", "warning")
        return redirect(url_for('restaurant_login'))

    restaurant_id = session.get('restaurant_id')
    orders_data = db.reference('orders').get() or {}

    orders = []
    for oid, od in orders_data.items():
        if isinstance(od, dict) and od.get('restaurant_id') == restaurant_id:
            od['id'] = oid
            orders.append(od)

    orders.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return render_template('orders_view.html', orders=orders)


# ===========================
# 💼 Restaurant Wallet
# ===========================

# Add this route to your app.py

@app.route('/restaurant/wallet')
def restaurant_wallet():
    """Restaurant wallet page with transactions"""
    if 'restaurant_email' not in session:
        flash("Please log in to continue.", "warning")
        return redirect(url_for('restaurant_login'))

    try:
        restaurant_id = session.get('restaurant_id')

        # Get restaurant data
        rest_ref = db.reference(f'restaurants/{restaurant_id}')
        restaurant = rest_ref.get() or {}
        restaurant['id'] = restaurant_id

        # Get wallet balance
        wallet_ref = db.reference(f'restaurant_wallets/{restaurant_id}')
        wallet_data = wallet_ref.get() or {}
        balance = wallet_data.get('balance', 0)

        # Get all transactions
        trans_ref = db.reference(f'restaurant_wallet_transactions/{restaurant_id}')
        trans_data = trans_ref.get() or {}

        transactions = []
        for tid, tdata in trans_data.items():
            if isinstance(tdata, dict):
                tdata['id'] = tid
                transactions.append(tdata)

        # Sort by created_at (newest first)
        transactions.sort(key=lambda x: x.get('created_at', ''), reverse=True)

        # Calculate stats
        total_credits = sum(t.get('amount', 0) for t in transactions if t.get('type') == 'credit')
        total_debits = sum(t.get('amount', 0) for t in transactions if t.get('type') == 'debit')

        stats = {
            'credits': total_credits,
            'debits': total_debits,
            'last_tx': transactions[0].get('created_at', 'N/A') if transactions else 'N/A'
        }

        return render_template('restaurant_wallet.html',
                               restaurant=restaurant,
                               balance=balance,
                               transactions=transactions,
                               stats=stats)

    except Exception as e:
        print(f"Error loading wallet: {str(e)}")
        flash(f"Error loading wallet: {str(e)}", "danger")
        return redirect(url_for('restaurant_dashboard'))


@app.route('/restaurant/wallet/withdraw', methods=['POST'])
def restaurant_wallet_withdraw():
    """Handle withdrawal request"""
    if 'restaurant_email' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})

    try:
        restaurant_id = session.get('restaurant_id')
        data = request.get_json()

        amount = float(data.get('amount', 0))
        bank_details = data.get('bank_details', '')

        # Validate amount
        if not math.isfinite(amount) or amount < 500:
            return jsonify({'success': False, 'message': 'Minimum withdrawal amount is PKR 500'})

        # Get current balance
        wallet_ref = db.reference(f'restaurant_wallets/{restaurant_id}')
        wallet_data = wallet_ref.get() or {}
        current_balance = wallet_data.get('balance', 0)

        if amount > current_balance:
            return jsonify({'success': False, 'message': 'Insufficient balance'})

        # Create withdrawal request
        withdrawal_ref = db.reference('withdrawal_requests')
        withdrawal_ref.push({
            'restaurant_id': restaurant_id,
            'amount': amount,
            'bank_details': bank_details,
            'status': 'pending',
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        # Create notification
        create_notification(
            restaurant_id=restaurant_id,
            title="💰 Withdrawal Request Submitted",
            message=f"Your withdrawal request of PKR {amount} has been submitted",
            notification_type='info'
        )

        return jsonify({
            'success': True,
            'message': 'Withdrawal request submitted successfully! You will be notified once processed.'
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/restaurant/wallet/request', methods=['POST'])
def restaurant_wallet_request():
    """Handle payment request"""
    if 'restaurant_email' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})

    try:
        restaurant_id = session.get('restaurant_id')
        data = request.get_json()

        amount = float(data.get('amount', 0))
        reason = data.get('reason', '')

        # Validate
        if not math.isfinite(amount) or amount <= 0:
            return jsonify({'success': False, 'message': 'Invalid amount'})

        if not reason:
            return jsonify({'success': False, 'message': 'Please provide a reason'})

        # Create payment request
        request_ref = db.reference('payment_requests')
        request_ref.push({
            'restaurant_id': restaurant_id,
            'amount': amount,
            'reason': reason,
            'status': 'pending',
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        # Create notification
        create_notification(
            restaurant_id=restaurant_id,
            title="📨 Payment Request Sent",
            message=f"Payment request of PKR {amount} has been sent for review",
            notification_type='info'
        )

        return jsonify({
            'success': True,
            'message': 'Payment request sent successfully!'
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


# Helper function to add transaction (use this when order is completed)
def add_wallet_transaction(restaurant_id, amount, transaction_type, description):
    """
    Add a transaction to restaurant wallet
    transaction_type: 'credit' or 'debit'
    """
    try:
        # Get current balance
        wallet_ref = db.reference(f'restaurant_wallets/{restaurant_id}')
        wallet_data = wallet_ref.get() or {'balance': 0}
        current_balance = wallet_data.get('balance', 0)

        # Calculate new balance
        if transaction_type == 'credit':
            new_balance = current_balance + amount
        else:  # debit
            new_balance = current_balance - amount

        # Update wallet balance
        wallet_ref.update({
            'balance': new_balance,
            'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        # Add transaction record
        trans_ref = db.reference(f'restaurant_wallet_transactions/{restaurant_id}')
        trans_ref.push({
            'type': transaction_type,
            'amount': amount,
            'description': description,
            'previous_balance': current_balance,
            'new_balance': new_balance,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        # Create notification
        if transaction_type == 'credit':
            create_notification(
                restaurant_id=restaurant_id,
                title="💰 Payment Received",
                message=f"PKR {amount} credited to your wallet",
                notification_type='success'
            )

        return True
    except Exception as e:
        print(f"Error adding transaction: {str(e)}")
        return False


# Example: Add transaction when order is delivered
"""
# In your order status update route, when status becomes 'delivered':
if new_status == 'delivered':
    # Calculate restaurant's earning (total - delivery fee - commission)
    restaurant_earning = order_data.get('net_amount', 0)  # or calculate it

    add_wallet_transaction(
        restaurant_id=restaurant_id,
        amount=restaurant_earning,
        transaction_type='credit',
        description=f"Order #{order_data.get('order_number', '')} payment"
    )
"""

@app.route('/order_check', methods=['GET', 'POST'])
def order_check():
    order = None
    error = None
    restaurant = None
    reviews_list = []
    order_number_input = ''

    def find_order_by_number(order_number: str):
        orders_data = db.reference('orders').get() or {}
        for oid, od in orders_data.items():
            if isinstance(od, dict) and str(od.get('order_number', '')).strip() == order_number:
                od['id'] = oid

                # normalize items for template
                items = od.get('items') or []
                if isinstance(items, dict):
                    od['items_list'] = [v for v in items.values() if isinstance(v, dict)]
                elif isinstance(items, list):
                    od['items_list'] = [x for x in items if isinstance(x, dict)]
                else:
                    od['items_list'] = []

                # safe rider
                if not isinstance(od.get('rider'), dict):
                    od['rider'] = {}

                return od
        return None

    # Support GET with query: /order_check?order_number=XXXX
    if request.method == 'GET':
        qn = (request.args.get('order_number') or '').strip()
        if qn:
            order_number_input = qn
            order = find_order_by_number(qn)
            if not order:
                error = "Order not found"

    if request.method == 'POST':
        order_number = (request.form.get('order_number') or '').strip()
        order_number_input = order_number

        if not order_number:
            error = "Please enter order number"
        else:
            order = find_order_by_number(order_number)
            if not order:
                error = "Order not found"

    # Load restaurant + reviews if order found
    already_reviewed = False
    can_review = False

    if order:
        rest_id = order.get('restaurant_id')
        if not rest_id and order.get('items_list'):
            rest_id = (order['items_list'][0] or {}).get('restaurant_id')

        if rest_id:
            restaurant = db.reference(f"restaurants/{rest_id}").get() or {}
            restaurant['id'] = rest_id

            # load reviews for this restaurant
            data = db.reference(f"restaurant_reviews/{rest_id}").get() or {}
            for rid, rv in data.items():
                if isinstance(rv, dict):
                    rv['id'] = rid
                    reviews_list.append(rv)
            reviews_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)

            # review rules
            can_review = (str(order.get('status', '')).lower() == 'delivered')
            user_email = (order.get('user_email') or '').strip().lower()

            for rv in reviews_list:
                if (rv.get('order_number') or '').strip() == order.get('order_number'):
                    already_reviewed = True
                    break
                if (rv.get('user_email') or '').strip().lower() == user_email:
                    already_reviewed = True
                    break

    return render_template(
        'order_check.html',
        order=order,
        error=error,
        restaurant=restaurant,
        reviews_list=reviews_list,
        can_review=can_review,
        already_reviewed=already_reviewed,
        order_number_input=order_number_input
    )

@app.route('/order_check/review', methods=['POST'])
def submit_review_from_order_check():
    order_number = (request.form.get('order_number') or '').strip()
    user_email = (request.form.get('user_email') or '').strip().lower()
    user_name = (request.form.get('user_name') or 'User').strip()
    review_text = (request.form.get('review_text') or '').strip()

    # stars validate
    try:
        stars = int((request.form.get('stars') or '0').strip())
    except Exception:
        stars = 0

    if not order_number:
        flash("Order number missing.", "danger")
        return redirect(url_for('order_check'))

    # find order
    orders_data = db.reference('orders').get() or {}
    order = None
    for oid, od in orders_data.items():
        if isinstance(od, dict) and str(od.get('order_number', '')).strip() == order_number:
            order = od
            break

    if not order:
        flash("Order not found.", "danger")
        return redirect(url_for('order_check'))

    # security checks
    order_email = (order.get('user_email') or '').strip().lower()
    if not user_email or user_email != order_email:
        flash("Email does not match this order.", "danger")
        return redirect(url_for('order_check', order_number=order_number))

    if str(order.get('status', '')).lower() != 'delivered':
        flash("You can review only after the order is delivered.", "warning")
        return redirect(url_for('order_check', order_number=order_number))

    if stars < 1 or stars > 5:
        flash("Please select stars (1 to 5).", "danger")
        return redirect(url_for('order_check', order_number=order_number))

    if len(review_text) < 3:
        flash("Please write a short review.", "danger")
        return redirect(url_for('order_check', order_number=order_number))

    restaurant_id = order.get('restaurant_id')
    restaurant_name = order.get('restaurant_name', '')

    if not restaurant_id:
        flash("Restaurant id missing in order.", "danger")
        return redirect(url_for('order_check', order_number=order_number))

    # prevent duplicate review
    existing = db.reference(f"restaurant_reviews/{restaurant_id}").get() or {}
    for rid, rv in existing.items():
        if isinstance(rv, dict):
            if (rv.get('order_number') or '') == order_number:
                flash("You already reviewed this order.", "warning")
                return redirect(url_for('order_check', order_number=order_number))
            if (rv.get('user_email') or '').strip().lower() == user_email:
                flash("You already reviewed this restaurant.", "warning")
                return redirect(url_for('order_check', order_number=order_number))

    # save review
    review_ref = db.reference(f"restaurant_reviews/{restaurant_id}").push()
    review_ref.set({
        'order_number': order_number,
        'restaurant_id': restaurant_id,
        'restaurant_name': restaurant_name,
        'user_name': user_name,
        'user_email': user_email,
        'stars': stars,
        'review_text': review_text,
        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    # update restaurant rating + reviews count
    rest_ref = db.reference(f"restaurants/{restaurant_id}")
    rest = rest_ref.get() or {}

    old_avg = float(rest.get('rating', 0) or 0)
    old_count = int(rest.get('reviews', 0) or 0)

    new_count = old_count + 1
    new_avg = ((old_avg * old_count) + stars) / new_count

    rest_ref.update({
        'rating': round(new_avg, 2),
        'reviews': new_count
    })

    flash("Review submitted successfully ✅", "success")
    return redirect(url_for('order_check', order_number=order_number))


# Add these routes to your main Flask app.py file

# ================================
# RESTAURANT PROFILE ROUTES
# ================================

@app.route('/restaurant/profile', methods=['GET', 'POST'])
def restaurant_profile():
    if 'restaurant_email' not in session:
        flash("Please log in to continue.", "warning")
        return redirect(url_for('restaurant_login'))

    restaurant_id = session.get('restaurant_id')
    rest_ref = db.reference(f'restaurants/{restaurant_id}')
    restaurant = rest_ref.get() or {}
    restaurant['id'] = restaurant_id

    if request.method == 'POST':
        try:
            # Get form data
            restaurant_name = request.form.get('restaurant_name', '').strip()
            owner_name = request.form.get('owner_name', '').strip()
            phone = request.form.get('phone', '').strip()
            address = request.form.get('address', '').strip()
            city = request.form.get('city', '').strip()
            description = request.form.get('description', '').strip()
            opening_time = request.form.get('opening_time', '')
            closing_time = request.form.get('closing_time', '')

            # Update restaurant info
            update_data = {
                'restaurant_name': restaurant_name,
                'owner_name': owner_name,
                'phone': phone,
                'address': address,
                'city': city,
                'description': description,
                'opening_time': opening_time,
                'closing_time': closing_time,
                'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            rest_ref.update(update_data)
            session['restaurant_name'] = restaurant_name

            flash("Profile updated successfully!", "success")
            return redirect(url_for('restaurant_profile'))

        except Exception as e:
            flash(f"Error updating profile: {str(e)}", "danger")

    return render_template('restaurant_profile.html', restaurant=restaurant)


# ================================
# RESTAURANT SETTINGS ROUTES
# ================================

@app.route('/restaurant/settings', methods=['GET', 'POST'])
def restaurant_settings():
    if 'restaurant_email' not in session:
        flash("Please log in to continue.", "warning")
        return redirect(url_for('restaurant_login'))

    restaurant_id = session.get('restaurant_id')

    # Get restaurant data
    rest_ref = db.reference(f'restaurants/{restaurant_id}')
    restaurant = rest_ref.get() or {}
    restaurant['id'] = restaurant_id

    # Get notification settings
    settings_ref = db.reference(f'restaurant_settings/{restaurant_id}')
    settings = settings_ref.get() or {
        'email_notifications': True,
        'sms_notifications': True,
        'order_notifications': True,
        'review_notifications': True
    }

    if request.method == 'POST':
        try:
            # Update notification settings
            new_settings = {
                'email_notifications': request.form.get('email_notifications') == 'on',
                'sms_notifications': request.form.get('sms_notifications') == 'on',
                'order_notifications': request.form.get('order_notifications') == 'on',
                'review_notifications': request.form.get('review_notifications') == 'on',
                'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            settings_ref.set(new_settings)
            flash("Settings updated successfully!", "success")
            return redirect(url_for('restaurant_settings'))

        except Exception as e:
            flash(f"Error updating settings: {str(e)}", "danger")

    return render_template('restaurant_settings.html',
                           restaurant=restaurant,
                           settings=settings)


@app.route('/restaurant/change_password', methods=['POST'])
def restaurant_change_password():
    if 'restaurant_email' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})

    try:
        restaurant_id = session.get('restaurant_id')
        data = request.get_json()

        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')

        # Get current restaurant data
        rest_ref = db.reference(f'restaurants/{restaurant_id}')
        restaurant = rest_ref.get()

        if not restaurant:
            return jsonify({'success': False, 'message': 'Restaurant not found'})

        # Verify current password
        if not verify_password(restaurant.get('password'), current_password):
            return jsonify({'success': False, 'message': 'Current password is incorrect'})

        # Validate new password
        if new_password != confirm_password:
            return jsonify({'success': False, 'message': 'New passwords do not match'})

        if len(new_password) < 8:
            return jsonify({'success': False, 'message': 'Password must be at least 8 characters'})

        # Update password
        rest_ref.update({'password': generate_password_hash(new_password)})

        return jsonify({'success': True, 'message': 'Password changed successfully!'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


# ================================
# RESTAURANT NOTIFICATIONS
# ================================

@app.route('/restaurant/notifications')
def restaurant_notifications():
    if 'restaurant_email' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})

    try:
        restaurant_id = session.get('restaurant_id')

        # Get all notifications
        notif_ref = db.reference(f'restaurant_notifications/{restaurant_id}')
        notif_data = notif_ref.get() or {}

        notifications = []
        for nid, ndata in notif_data.items():
            if isinstance(ndata, dict):
                ndata['id'] = nid
                notifications.append(ndata)

        # Sort by created_at (newest first)
        notifications.sort(key=lambda x: x.get('created_at', ''), reverse=True)

        # Count unread
        unread_count = sum(1 for n in notifications if not n.get('read', False))

        return jsonify({
            'success': True,
            'notifications': notifications,
            'unread_count': unread_count
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/restaurant/notifications/mark_read/<notification_id>', methods=['POST'])
def mark_notification_read(notification_id):
    if 'restaurant_email' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})

    try:
        restaurant_id = session.get('restaurant_id')
        notif_ref = db.reference(f'restaurant_notifications/{restaurant_id}/{notification_id}')
        notif_ref.update({'read': True})

        return jsonify({'success': True, 'message': 'Notification marked as read'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/restaurant/notifications/mark_all_read', methods=['POST'])
def mark_all_notifications_read():
    if 'restaurant_email' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})

    try:
        restaurant_id = session.get('restaurant_id')
        notif_ref = db.reference(f'restaurant_notifications/{restaurant_id}')
        notif_data = notif_ref.get() or {}

        for nid in notif_data.keys():
            db.reference(f'restaurant_notifications/{restaurant_id}/{nid}').update({'read': True})

        return jsonify({'success': True, 'message': 'All notifications marked as read'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


# ================================
# RESTAURANT SEARCH
# ================================

@app.route('/restaurant/search')
def restaurant_search():
    if 'restaurant_email' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})

    try:
        restaurant_id = session.get('restaurant_id')
        query = request.args.get('q', '').strip().lower()

        if not query:
            return jsonify({'success': True, 'results': []})

        results = []

        # Search in orders
        orders_ref = db.reference('orders')
        orders_data = orders_ref.get() or {}

        for oid, order in orders_data.items():
            if isinstance(order, dict) and order.get('restaurant_id') == restaurant_id:
                search_text = f"{order.get('order_number', '')} {order.get('user_email', '')} {order.get('user_name', '')}".lower()
                if query in search_text:
                    results.append({
                        'type': 'order',
                        'id': oid,
                        'title': f"Order #{order.get('order_number', '')}",
                        'subtitle': f"{order.get('user_name', 'User')} - PKR {order.get('total_amount', 0)}",
                        'icon': 'shopping-bag',
                        'url': url_for('view_order_details', order_id=oid)
                    })

        # Search in menu items
        menu_ref = db.reference(f'menu/{restaurant_id}')
        menu_data = menu_ref.get() or {}

        for mid, item in menu_data.items():
            if isinstance(item, dict):
                search_text = f"{item.get('name', '')} {item.get('category', '')} {item.get('description', '')}".lower()
                if query in search_text:
                    results.append({
                        'type': 'menu',
                        'id': mid,
                        'title': item.get('name', ''),
                        'subtitle': f"{item.get('category', '')} - PKR {item.get('price', 0)}",
                        'icon': 'utensils',
                        'url': url_for('restaurant_menu')
                    })

        # Limit results to 10
        results = results[:10]

        return jsonify({'success': True, 'results': results})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


# ================================
# RESTAURANT GALLERY
# ================================

@app.route('/restaurant/gallery', methods=['GET', 'POST'])
def restaurant_gallery():
    if 'restaurant_email' not in session:
        flash("Please log in to continue.", "warning")
        return redirect(url_for('restaurant_login'))

    restaurant_id = session.get('restaurant_id')
    rest_ref = db.reference(f'restaurants/{restaurant_id}')
    restaurant = rest_ref.get() or {}
    restaurant['id'] = restaurant_id

    # Get existing images
    images = restaurant.get('images', [])

    if request.method == 'POST':
        try:
            # Handle multiple image uploads
            image_files = request.files.getlist('gallery_images')

            if not image_files or all(f.filename == '' for f in image_files):
                flash("Please select at least one image", "warning")
                return redirect(url_for('restaurant_gallery'))

            new_images = []
            for img_file in image_files:
                if img_file and img_file.filename != '' and allowed_file(img_file.filename):
                    filename = secure_filename(img_file.filename)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"gallery_{restaurant_id}_{timestamp}_{filename}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    img_file.save(filepath)
                    new_images.append(url_for('static', filename=f'images/{filename}'))

            # Append new images to existing
            all_images = images + new_images
            rest_ref.update({'images': all_images})

            flash(f"{len(new_images)} images uploaded successfully!", "success")
            return redirect(url_for('restaurant_gallery'))

        except Exception as e:
            flash(f"Error uploading images: {str(e)}", "danger")

    return render_template('restaurant_gallery.html',
                           restaurant=restaurant,
                           images=images)


@app.route('/restaurant/gallery/delete/<int:image_index>', methods=['POST'])
def delete_gallery_image(image_index):
    if 'restaurant_email' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})

    try:
        restaurant_id = session.get('restaurant_id')
        rest_ref = db.reference(f'restaurants/{restaurant_id}')
        restaurant = rest_ref.get() or {}

        images = restaurant.get('images', [])

        if 0 <= image_index < len(images):
            deleted_image = images.pop(image_index)
            rest_ref.update({'images': images})

            return jsonify({'success': True, 'message': 'Image deleted successfully'})
        else:
            return jsonify({'success': False, 'message': 'Invalid image index'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


# ================================
# HELPER FUNCTION FOR NOTIFICATIONS
# ================================

def create_notification(restaurant_id, title, message, notification_type='info', link=None):
    """
    Create a notification for restaurant
    notification_type: info, success, warning, error
    """
    try:
        notif_ref = db.reference(f'restaurant_notifications/{restaurant_id}')
        notif_ref.push({
            'title': title,
            'message': message,
            'type': notification_type,
            'link': link,
            'read': False,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        return True
    except Exception as e:
        print(f"Error creating notification: {str(e)}")
        return False


# ================================
# UPDATE EXISTING ROUTES TO CREATE NOTIFICATIONS
# ================================

# Update the order status update route to create notifications
# Add this after updating order status in update_order_status route:

"""
# In your update_order_status function, after order_ref.update(), add:
create_notification(
    restaurant_id=restaurant_id,
    title="Order Status Updated",
    message=f"Order #{order_data.get('order_number', '')} status changed to {new_status}",
    notification_type='success',
    link=url_for('view_order_details', order_id=order_id)
)
"""

# Add notification when new order is received
# In your checkout route after order is created, add:

"""
# After saving order to Firebase:
create_notification(
    restaurant_id=restaurant_id,
    title="New Order Received!",
    message=f"New order #{order_number} from {user_name}",
    notification_type='info',
    link=url_for('view_order_details', order_id=order_id)
)
"""


# ================================
# CONTEXT PROCESSOR FOR NOTIFICATIONS COUNT
# ================================

@app.context_processor
def inject_notification_count():
    """Inject unread notification count into all templates"""
    notification_count = 0
    if 'restaurant_email' in session:
        restaurant_id = session.get('restaurant_id')
        if restaurant_id:
            try:
                notif_ref = db.reference(f'restaurant_notifications/{restaurant_id}')
                notif_data = notif_ref.get() or {}
                notification_count = sum(1 for n in notif_data.values()
                                         if isinstance(n, dict) and not n.get('read', False))
            except Exception:
                notification_count = 0

    return {'notification_count': notification_count}


# ================================
# RESTAURANT HELP CENTER
# ================================

@app.route('/restaurant/help')
def restaurant_help():
    if 'restaurant_email' not in session:
        flash("Please log in to continue.", "warning")
        return redirect(url_for('restaurant_login'))

    restaurant_id = session.get('restaurant_id')
    rest_ref = db.reference(f'restaurants/{restaurant_id}')
    restaurant = rest_ref.get() or {}
    restaurant['id'] = restaurant_id

    # FAQ data
    faqs = [
        {
            'question': 'How do I manage orders?',
            'answer': 'Go to Orders section to view, accept, and update order status. You can change status from pending to confirmed, preparing, ready, and delivered.',
            'category': 'orders'
        },
        {
            'question': 'How do I add menu items?',
            'answer': 'Navigate to Menu Management and click "Add New Item". Fill in the details including name, price, description, and upload an image.',
            'category': 'menu'
        },
        {
            'question': 'How do I check my earnings?',
            'answer': 'Go to Wallet & Earnings section to view your balance, transaction history, and withdraw funds.',
            'category': 'wallet'
        },
        {
            'question': 'How do I update restaurant information?',
            'answer': 'Go to Settings and click on "Restaurant Information" to update your details, hours, and contact info.',
            'category': 'settings'
        },
        {
            'question': 'How do I upload restaurant images?',
            'answer': 'Go to Gallery section and click "Upload New Images" to add photos of your restaurant and food.',
            'category': 'gallery'
        }
    ]

    return render_template('restaurant_help.html',
                           restaurant=restaurant,
                           faqs=faqs)


@app.route('/restaurant/help/contact', methods=['POST'])
def restaurant_help_contact():
    if 'restaurant_email' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})

    try:
        data = request.get_json()
        subject = data.get('subject', '')
        message = data.get('message', '')

        restaurant_id = session.get('restaurant_id')
        restaurant_email = session.get('restaurant_email')

        # Save support ticket to Firebase
        support_ref = db.reference('support_tickets')
        support_ref.push({
            'restaurant_id': restaurant_id,
            'email': restaurant_email,
            'subject': subject,
            'message': message,
            'status': 'pending',
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        # Send email to support (optional)
        try:
            yag = mail_client(EMAIL_USER, EMAIL_PASSWORD)
            yag.send(
                to=os.environ['SUPPORT_EMAIL'],
                subject=f'Support Request: {subject}',
                contents=f"""
                <h3>Support Request from Restaurant</h3>
                <p><strong>Restaurant ID:</strong> {restaurant_id}</p>
                <p><strong>Email:</strong> {restaurant_email}</p>
                <p><strong>Subject:</strong> {subject}</p>
                <p><strong>Message:</strong></p>
                <p>{message}</p>
                """
            )
        except Exception:
            pass

        return jsonify({'success': True, 'message': 'Support request sent successfully!'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})
from flask import jsonify, session
from datetime import datetime

# -------------------------------
# Helper: Build multi-path deletes
# -------------------------------
def build_restaurant_delete_updates(restaurant_id: str) -> dict:
    """
    Creates a multi-path update dict where values = None
    (None deletes nodes in Firebase RTDB).
    """
    updates = {}

    # 1) Main restaurant profile
    updates[f"restaurants/{restaurant_id}"] = None

    # 2) Menu of that restaurant
    updates[f"menu/{restaurant_id}"] = None

    # 3) Reviews of that restaurant
    updates[f"restaurant_reviews/{restaurant_id}"] = None

    # 4) Restaurant wallet + transactions
    updates[f"restaurant_wallets/{restaurant_id}"] = None
    updates[f"restaurant_wallet_transactions/{restaurant_id}"] = None

    # 5) Delete cart items that belong to this restaurant
    carts = db.reference("carts").get() or {}
    if isinstance(carts, dict):
        for user_id, user_cart in carts.items():
            if not isinstance(user_cart, dict):
                continue
            for cart_item_id, cart_item in user_cart.items():
                if isinstance(cart_item, dict) and cart_item.get("restaurant_id") == restaurant_id:
                    updates[f"carts/{user_id}/{cart_item_id}"] = None

    # 6) Delete orders that belong to this restaurant
    orders = db.reference("orders").get() or {}
    if isinstance(orders, dict):
        for order_id, order_data in orders.items():
            if isinstance(order_data, dict) and order_data.get("restaurant_id") == restaurant_id:
                updates[f"orders/{order_id}"] = None

    return updates


# -----------------------------------------
# ✅ ADMIN: Delete restaurant everywhere
# -----------------------------------------
@app.route('/admin/restaurant/delete/<restaurant_id>', methods=['POST'])
def admin_delete_restaurant(restaurant_id):
    if not session.get('admin'):
        return jsonify({'success': False, 'message': 'Admin access required'})

    try:
        # Get restaurant info (optional, for message/email)
        rest_ref = db.reference(f"restaurants/{restaurant_id}")
        restaurant = rest_ref.get()

        if not restaurant:
            return jsonify({'success': False, 'message': 'Restaurant not found'})

        restaurant_name = restaurant.get("restaurant_name", "Restaurant")
        restaurant_email = restaurant.get("email")

        # Build delete updates (multi-path)
        updates = build_restaurant_delete_updates(restaurant_id)

        # Apply all deletes in ONE request
        db.reference("/").update(updates)

        # OPTIONAL: send email (if you already have this function)
        # try:
        #     send_restaurant_email(restaurant_email, restaurant_name, "deleted")
        # except:
        #     pass

        return jsonify({
            'success': True,
            'message': f'"{restaurant_name}" deleted everywhere successfully!'
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(os.getenv('PORT', '5000')), debug=False)