import os
from flask import Flask, render_template, redirect, url_for, flash, request, session, abort
from flask_bcrypt import Bcrypt
from flask_login import login_user, logout_user, login_required, current_user, LoginManager
from flask_pymongo import PyMongo
from bson import ObjectId
from bson.errors import InvalidId
import random
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
from models import User, ItemStatusEnum, CourseEnum, BranchEnum

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'd6b5f6a4d1c1e3c9b7d9d2f1e8b9c0a4e5d6f7a8b9c0d1e2f3a4b5c6d7e8f9g0h')
app.config['SECURITY_PASSWORD_SALT'] = os.environ.get('SECURITY_PASSWORD_SALT', 'lf-salt-2026-campus')
app.config['MONGO_URI'] = os.environ.get('MONGO_URI', 'mongodb+srv://kishan9798760468_db_user:joGeYTKH1bfd9neF@cluster0.nro9z2t.mongodb.net/lost_found_db?appName=Cluster0')
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'images')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'shashishe2160@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'bbctalfofplhhkea')
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

mongo = PyMongo(app)
mail = Mail(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

os.makedirs(os.path.join('static', 'images'), exist_ok=True)

# ── Helpers ────────────────────────────────────────────────────────────────────
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg','jpeg','png','gif','webp'}

def get_object_id(id_str):
    try:
        return ObjectId(id_str)
    except (InvalidId, Exception):
        abort(404)

def get_item_or_404(item_id):
    item = mongo.db.items.find_one({'_id': get_object_id(item_id)})
    if not item:
        abort(404)
    return item

@login_manager.user_loader
def load_user(user_id):
    try:
        doc = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    except Exception:
        return None
    return User(doc) if doc else None

@app.context_processor
def inject_notification_count():
    if current_user.is_authenticated:
        count = mongo.db.notifications.count_documents({'user_id': current_user.id})
    else:
        count = 0
    return dict(notification_count=count, now=datetime.utcnow())

def generate_otp():
    return f"{random.randint(100000, 999999)}"

def send_otp_reg(email, otp):
    msg = Message('Email Confirmation OTP Code', sender=app.config['MAIL_USERNAME'], recipients=[email])
    msg.html = f'<div style="font-family:Arial;color:#333"><h2 style="color:#004085">LOST-FOUND Management Team</h2><p>Your OTP: <strong style="font-size:18px;color:#007bff">{otp}</strong></p><p style="color:#6c757d">If you did not request this, ignore this email.</p></div>'
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")
        flash('Failed to send OTP. Please try again later.', 'danger')

def send_otp_forget_pass(email, otp):
    msg = Message('Password Reset OTP Code', sender=app.config['MAIL_USERNAME'], recipients=[email])
    msg.html = f'<div style="font-family:Arial;color:#333"><h2 style="color:#004085">LOST-FOUND Management Team</h2><p>Password reset OTP: <strong style="font-size:18px;color:#007bff">{otp}</strong></p><p style="color:#6c757d">If you did not request this, secure your account immediately.</p></div>'
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")
        flash('Failed to send OTP. Please try again later.', 'danger')

# ── Auth Routes ────────────────────────────────────────────────────────────────
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email       = request.form.get('email')
        first_name  = request.form.get('first_name')
        last_name   = request.form.get('last_name')
        password    = request.form.get('password')
        roll_number = request.form.get('roll_number')
        batch       = request.form.get('batch')
        course      = request.form.get('course')
        branch      = request.form.get('branch')

        if len(password) < 8 or not any(c.isdigit() for c in password) or not any(c.isalpha() for c in password):
            flash('Password must be at least 8 characters long and contain both letters and digits.', 'danger')
            return redirect(url_for('register'))

        if mongo.db.users.find_one({'email': email}):
            flash('Email address already registered.', 'danger')
            return redirect(url_for('register'))

        otp = generate_otp()
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        session['temp_user'] = {
            'email': email, 'first_name': first_name, 'last_name': last_name,
            'password': hashed_password, 'roll_number': roll_number,
            'batch': batch, 'course': course, 'branch': branch,
            'otp': otp, 'otp_generated_at': datetime.utcnow().isoformat()
        }
        send_otp_reg(email, otp)
        flash('An OTP has been sent to your email. Please verify to complete registration.', 'info')
        return redirect(url_for('verify_registration'))
    return render_template('register.html')

@app.route('/verify_registration', methods=['GET', 'POST'])
def verify_registration():
    if request.method == 'POST':
        otp = request.form.get('otp')
        temp_user = session.get('temp_user')
        if not temp_user:
            flash('Session expired. Please register again.', 'danger')
            return redirect(url_for('register'))

        otp_generated_at = datetime.fromisoformat(temp_user['otp_generated_at'])
        if (datetime.utcnow() - otp_generated_at).total_seconds() > 600:
            flash('OTP has expired. Please register again.', 'danger')
            session.pop('temp_user', None)
            return redirect(url_for('register'))

        if temp_user['otp'] == otp:
            mongo.db.users.insert_one({
                'email': temp_user['email'],
                'first_name': temp_user['first_name'],
                'last_name': temp_user['last_name'],
                'password': temp_user['password'],
                'roll_number': temp_user['roll_number'],
                'batch': temp_user['batch'],
                'course': temp_user['course'],
                'branch': temp_user['branch'],
                'is_verified': True,
                'profile_pic': 'default.jpg',
                'created_at': datetime.utcnow()
            })
            session.pop('temp_user', None)
            flash('Your account has been created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Invalid OTP. Please try again.', 'danger')
    return render_template('verify_registration.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form.get('email')
        password = request.form.get('password')
        doc      = mongo.db.users.find_one({'email': email})
        if doc and bcrypt.check_password_hash(doc['password'], password):
            if doc.get('is_verified'):
                login_user(User(doc))
                flash('Login successful!', 'success')
                return redirect(url_for('home_page'))
            else:
                flash('Please verify your email before logging in.', 'danger')
        else:
            flash('Login failed. Check your credentials.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user  = mongo.db.users.find_one({'email': email})
        if user:
            otp        = generate_otp()
            expires_at = datetime.utcnow() + timedelta(minutes=10)
            mongo.db.password_reset_tokens.insert_one({
                'user_id': str(user['_id']), 'otp': otp, 'expires_at': expires_at,
                'created_at': datetime.utcnow()
            })
            send_otp_forget_pass(email, otp)
            session['reset_email'] = email
            flash('An OTP has been sent to your email for password reset.', 'info')
            return redirect(url_for('verify_reset_password'))
        else:
            flash('Email not registered.', 'danger')
    return render_template('forgot_password.html')

@app.route('/verify_reset_password', methods=['GET', 'POST'])
def verify_reset_password():
    email = session.get('reset_email')
    if not email:
        flash('No email found in session. Please try again.', 'danger')
        return redirect(url_for('forgot_password'))
    if request.method == 'POST':
        otp  = request.form.get('otp')
        user = mongo.db.users.find_one({'email': email})
        if user:
            token = mongo.db.password_reset_tokens.find_one({
                'user_id': str(user['_id']), 'otp': otp,
                'expires_at': {'$gt': datetime.utcnow()}
            })
            if token:
                session['reset_user'] = str(user['_id'])
                mongo.db.password_reset_tokens.delete_one({'_id': token['_id']})
                flash('OTP verified. You can now reset your password.', 'success')
                return redirect(url_for('reset_password'))
            else:
                flash('Invalid or expired OTP. Please try again.', 'danger')
        else:
            flash('Email not registered.', 'danger')
    return render_template('verify_reset_password.html', email=email)

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        password = request.form.get('password')
        user_id  = session.get('reset_user')
        if not password or len(password) < 8 or not any(c.isdigit() for c in password) or not any(c.isalpha() for c in password):
            flash('Password must be at least 8 characters long and contain both letters and digits.', 'danger')
            return redirect(url_for('reset_password'))
        if user_id:
            hashed = bcrypt.generate_password_hash(password).decode('utf-8')
            mongo.db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'password': hashed}})
            session.pop('reset_user', None)
            flash('Your password has been reset successfully!', 'success')
            return redirect(url_for('login'))
        else:
            flash('No user session found. Please try again.', 'danger')
    return render_template('reset_password.html')

# ── Main Routes ────────────────────────────────────────────────────────────────
@app.route('/')
def home_page():
    search_term   = request.args.get('search', '')
    category_id   = request.args.get('category', '')
    status_filter = request.args.get('status', '')
    page          = request.args.get('page', 1, type=int)
    per_page      = 9

    query = {}
    if search_term:
        query['$or'] = [
            {'name': {'$regex': search_term, '$options': 'i'}},
            {'description': {'$regex': search_term, '$options': 'i'}}
        ]
    if category_id:
        query['category_id'] = category_id
    if status_filter in ('lost', 'found'):
        query['status'] = status_filter

    total = mongo.db.items.count_documents(query)
    items_cursor = (mongo.db.items.find(query)
                    .sort('date', -1)
                    .skip((page - 1) * per_page)
                    .limit(per_page))
    items      = list(items_cursor)
    categories = list(mongo.db.categories.find())

    # Simple pagination object
    class Pagination:
        def __init__(self, page, per_page, total):
            self.page      = page
            self.per_page  = per_page
            self.total     = total
            self.pages     = max(1, (total + per_page - 1) // per_page)
            self.has_prev  = page > 1
            self.has_next  = page < self.pages
            self.prev_num  = page - 1
            self.next_num  = page + 1
        def iter_pages(self, left_edge=2, right_edge=2, left_current=2, right_current=3):
            last = 0
            for num in range(1, self.pages + 1):
                if (num <= left_edge or
                    (self.page - left_current - 1 < num < self.page + right_current) or
                        num > self.pages - right_edge):
                    if last + 1 != num:
                        yield None
                    yield num
                    last = num

    pagination = Pagination(page, per_page, total)
    return render_template('home.html', items=items, categories=categories,
                           pagination=pagination, search_term=search_term,
                           category_id=category_id, status_filter=status_filter)

@app.route('/add_item', methods=['GET', 'POST'])
@login_required
def add_item():
    if request.method == 'POST':
        name        = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        category_id = request.form.get('category', '')
        status      = request.form.get('status')
        date_str    = request.form.get('date')
        location    = request.form.get('location', '').strip()
        image       = request.files.get('image')

        if not name or not description or not status or not date_str:
            flash('Please fill in all required fields.', 'danger')
            return redirect(url_for('add_item'))

        try:
            item_date = datetime.strptime(date_str, '%Y-%m-%d')
            if item_date.date() > datetime.utcnow().date():
                flash('Date cannot be in the future.', 'danger')
                return redirect(url_for('add_item'))
        except ValueError:
            flash('Invalid date format.', 'danger')
            return redirect(url_for('add_item'))

        image_filename = 'default.jpg'
        if image and image.filename:
            if not allowed_file(image.filename):
                flash('Only image files (JPG, PNG, GIF, WEBP) are allowed.', 'danger')
                return redirect(url_for('add_item'))
            image_filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

        result = mongo.db.items.insert_one({
            'name': name, 'description': description,
            'category_id': category_id, 'status': status,
            'date': item_date, 'location': location,
            'image_file': image_filename, 'user_id': current_user.id,
            'claimed': False, 'resolved': False,
            'created_at': datetime.utcnow()
        })
        flash('Item reported successfully!', 'success')
        return redirect(url_for('item_detail', item_id=str(result.inserted_id)))

    categories = list(mongo.db.categories.find())
    return render_template('add_item.html', categories=categories)

@app.route('/edit_item/<item_id>', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    item = get_item_or_404(item_id)
    if item['user_id'] != current_user.id:
        flash('You are not authorized to edit this item.', 'danger')
        return redirect(url_for('item_detail', item_id=item_id))
    if item.get('resolved'):
        flash('Resolved items cannot be edited.', 'warning')
        return redirect(url_for('item_detail', item_id=item_id))

    if request.method == 'POST':
        name        = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        date_str    = request.form.get('date_lost_or_found', '').strip()
        location    = request.form.get('location', '').strip()
        category_id = request.form.get('category', '')

        if not name or not description or not date_str:
            flash('Name, description and date are required.', 'danger')
            return redirect(url_for('edit_item', item_id=item_id))

        try:
            item_date = datetime.strptime(date_str, '%Y-%m-%d')
            if item_date.date() > datetime.utcnow().date():
                flash('Date cannot be in the future.', 'danger')
                return redirect(url_for('edit_item', item_id=item_id))
        except ValueError:
            flash('Invalid date format.', 'danger')
            return redirect(url_for('edit_item', item_id=item_id))

        update = {'name': name, 'description': description, 'date': item_date,
                  'location': location, 'category_id': category_id}

        image_file = request.files.get('image')
        if image_file and image_file.filename:
            if not allowed_file(image_file.filename):
                flash('Only image files (JPG, PNG, GIF, WEBP) are allowed.', 'danger')
                return redirect(url_for('edit_item', item_id=item_id))
            fn = secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], fn))
            update['image_file'] = fn

        mongo.db.items.update_one({'_id': ObjectId(item_id)}, {'$set': update})
        flash('Item updated successfully.', 'success')
        return redirect(url_for('item_detail', item_id=item_id))

    categories = list(mongo.db.categories.find())
    return render_template('edit_item.html', item=item, categories=categories)

@app.route('/delete_item/<item_id>', methods=['POST'])
@login_required
def delete_item(item_id):
    item = get_item_or_404(item_id)
    if item['user_id'] != current_user.id:
        flash('You are not authorized to delete this item.', 'danger')
        return redirect(url_for('item_detail', item_id=item_id))
    mongo.db.claimed_items.delete_many({'item_id': item_id})
    mongo.db.notifications.delete_many({'item_id': item_id})
    mongo.db.items.delete_one({'_id': ObjectId(item_id)})
    flash('Item deleted successfully.', 'success')
    return redirect(url_for('home_page'))

@app.route('/confirm_delete/<item_id>')
@login_required
def confirm_delete(item_id):
    item = get_item_or_404(item_id)
    if item['user_id'] != current_user.id:
        flash('You are not authorized to delete this item.', 'danger')
        return redirect(url_for('item_detail', item_id=item_id))
    return render_template('confirm_delete.html', item=item)

@app.route('/item/<item_id>')
def item_detail(item_id):
    item    = get_item_or_404(item_id)
    claimer = None
    if item.get('claimed'):
        claim = mongo.db.claimed_items.find_one({'item_id': item_id})
        if claim:
            claimer_doc = mongo.db.users.find_one({'_id': ObjectId(claim['claimer_id'])})
            claimer = User(claimer_doc) if claimer_doc else None
    return render_template('item_details.html', item=item, claimer=claimer)

@app.route('/notifications')
@login_required
def view_notifications():
    notifications = list(mongo.db.notifications.find(
        {'user_id': current_user.id}).sort('sent_at', -1))
    return render_template('notifications.html', notifications=notifications)

@app.route('/profile')
@login_required
def view_profile():
    pipeline = [
        {'$match': {'claimer_id': current_user.id}},
        {'$sort': {'claimed_at': -1}},
        {'$addFields': {'item_oid': {'$toObjectId': '$item_id'}}},
        {'$lookup': {'from': 'items', 'localField': 'item_oid',
                     'foreignField': '_id', 'as': 'item_data'}},
        {'$unwind': '$item_data'}
    ]
    claimed_items = list(mongo.db.claimed_items.aggregate(pipeline))
    return render_template('profile.html', claimed_items=claimed_items)

@app.route('/update_profile', methods=['GET', 'POST'])
@login_required
def update_profile():
    if request.method == 'POST':
        batch = request.form.get('batch', '')
        try:
            batch = int(batch)
        except (ValueError, TypeError):
            flash('Invalid batch year.', 'danger')
            return redirect(url_for('update_profile'))

        update = {
            'first_name':  request.form.get('first_name', '').strip(),
            'last_name':   request.form.get('last_name', '').strip(),
            'roll_number': request.form.get('roll_number', '').strip(),
            'batch':       batch,
            'course':      request.form.get('course', ''),
            'branch':      request.form.get('branch', ''),
        }
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and file.filename and allowed_file(file.filename):
                fn = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], fn))
                update['profile_pic'] = fn

        mongo.db.users.update_one({'_id': ObjectId(current_user.id)}, {'$set': update})
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('view_profile'))
    return render_template('edit_profile.html')

@app.route('/resolve_item/<item_id>', methods=['POST'])
@login_required
def resolve_item(item_id):
    item = get_item_or_404(item_id)
    if item['user_id'] != current_user.id:
        flash('You are not authorized to resolve this item.', 'danger')
        return redirect(url_for('item_detail', item_id=item_id))
    mongo.db.items.update_one({'_id': ObjectId(item_id)}, {'$set': {'resolved': True, 'claimed': True}})
    claim = mongo.db.claimed_items.find_one({'item_id': item_id})
    if claim:
        mongo.db.notifications.insert_one({
            'user_id': claim['claimer_id'], 'item_id': item_id,
            'message': f'Great news! The owner has marked "{item["name"]}" as returned/resolved.',
            'sent_at': datetime.utcnow()
        })
    flash(f'"{item["name"]}" has been marked as returned/resolved!', 'success')
    return redirect(url_for('item_detail', item_id=item_id))

@app.route('/claim_item/<item_id>', methods=['POST'])
@login_required
def claim_item(item_id):
    item = get_item_or_404(item_id)
    if item['user_id'] == current_user.id:
        flash('You cannot claim your own item.', 'danger')
        return redirect(url_for('item_detail', item_id=item_id))
    if item.get('resolved'):
        flash('This item has already been returned and resolved.', 'warning')
        return redirect(url_for('item_detail', item_id=item_id))
    if item.get('claimed'):
        flash('This item has already been claimed.', 'warning')
        return redirect(url_for('item_detail', item_id=item_id))
    if mongo.db.claimed_items.find_one({'item_id': item_id, 'claimer_id': current_user.id}):
        flash('You have already submitted a claim for this item.', 'warning')
        return redirect(url_for('item_detail', item_id=item_id))

    mongo.db.claimed_items.insert_one({
        'item_id': item_id, 'claimer_id': current_user.id,
        'claimed_at': datetime.utcnow()
    })
    mongo.db.items.update_one({'_id': ObjectId(item_id)}, {'$set': {'claimed': True}})

    if item['status'] == 'lost':
        notif_msg  = (f'{current_user.first_name} {current_user.last_name} says they found your "{item["name"]}"! '
                      f'Contact them at {current_user.email}.')
        email_subj = f'Someone found your lost item: {item["name"]}!'
        flash_msg  = f'You have reported finding "{item["name"]}"! The owner has been notified.'
    else:
        notif_msg  = (f'{current_user.first_name} {current_user.last_name} is claiming "{item["name"]}" as their lost item! '
                      f'Contact them at {current_user.email}.')
        email_subj = f'Someone is claiming the item you found: {item["name"]}!'
        flash_msg  = f'You have claimed "{item["name"]}" as yours! The finder has been notified.'

    mongo.db.notifications.insert_one({
        'user_id': item['user_id'], 'item_id': item_id,
        'message': notif_msg, 'sent_at': datetime.utcnow()
    })

    owner_doc = mongo.db.users.find_one({'_id': ObjectId(item['user_id'])})
    if owner_doc:
        try:
            msg = Message(email_subj, sender=app.config['MAIL_USERNAME'], recipients=[owner_doc['email']])
            msg.html = f'<div style="font-family:Arial;color:#333;max-width:500px"><h2 style="color:#6c63ff">Smart Lost &amp; Found System</h2><p>Hi {owner_doc["first_name"]},</p><p>{notif_msg}</p><hr><p style="font-size:12px;color:#999">Automated message — do not reply.</p></div>'
            mail.send(msg)
        except Exception as e:
            print(f"Claim notification email failed: {e}")

    flash(flash_msg, 'success')
    return redirect(url_for('item_detail', item_id=item_id))

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        email    = request.form.get('email', '').strip()
        rating   = int(request.form.get('rating', 5))
        category = request.form.get('category', 'General')
        message  = request.form.get('message', '').strip()
        if not name or not email or not message:
            flash('Please fill in all required fields.', 'danger')
            return redirect(url_for('feedback'))
        mongo.db.feedback.insert_one({
            'user_id': current_user.id if current_user.is_authenticated else None,
            'name': name, 'email': email, 'rating': rating,
            'category': category, 'message': message,
            'created_at': datetime.utcnow()
        })
        flash('Thank you for your feedback! We really appreciate it.', 'success')
        return redirect(url_for('home_page'))
    return render_template('feedback.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)
