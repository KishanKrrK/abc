from flask import Flask, Blueprint, render_template, redirect, url_for, flash, request, session
from flask_bcrypt import Bcrypt
from flask_login import login_user, logout_user, login_required, current_user, LoginManager
import random
import os
from datetime import datetime, timezone, timedelta
from werkzeug.utils import secure_filename
from itsdangerous import URLSafeTimedSerializer as Serializer, SignatureExpired
from flask_mail import Mail, Message
from models import db, User, PasswordResetToken, Item, Category, Notification, ItemStatusEnum, ClaimedItem, Feedback
app = Flask(__name__)

app.config['SECRET_KEY'] = 'd6b5f6a4d1c1e3c9b7d9d2f1e8b9c0a4e5d6f7a8b9c0d1e2f3a4b5c6d7e8f9g0h'
app.config['SECURITY_PASSWORD_SALT'] = 'lf-salt-2026-campus'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234@localhost/lost_found_db'
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'images')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB upload limit
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'shashishe2160@gmail.com'
app.config['MAIL_PASSWORD'] = 'bbctalfofplhhkea'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

db.init_app(app)
mail = Mail(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Inject unread notification count into every template
@app.context_processor
def inject_notification_count():
    if current_user.is_authenticated:
        count = Notification.query.filter_by(user_id=current_user.id).count()
    else:
        count = 0
    return dict(notification_count=count, now=datetime.utcnow())

def send_otp_reg(email, otp):
    msg = Message('Email Confirmation OTP Code', sender=app.config['MAIL_USERNAME'], recipients=[email])
    msg.html = f'''
    <div style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: #004085; text-align: centre;">LOST-FOUND Management Team</h2>
        <p>Welcome!</p>
        <p>Thank you for signing up! Please confirm your college email ID.</p>
        <p style="font-size: 18px; color: #007bff;"><strong>Your OTP code is: {otp}</strong></p>
        <p style="color: #6c757d;">If you did not request this, please ignore this email.</p>
        <hr>
        <p style="font-size: 12px; color: #6c757d;">This is an automated message, please do not reply.</p>
    </div>
    '''
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")
        flash('Failed to send OTP. Please try again later.', category='danger')

def send_otp_forget_pass(email, otp):
    msg = Message('Password Reset OTP Code', sender=app.config['MAIL_USERNAME'], recipients=[email])
    msg.html = f'''
    <div style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: #004085;  text-align: centre;">LOST-FOUND Management Team</h2>
        <p>You have requested a password reset.</p>
        <p style="font-size: 18px; color: #007bff;"><strong>Your OTP code is: {otp}</strong></p>
        <p style="color: #6c757d;">If you did not request this, please secure your account immediately.</p>
        <hr>
        <p style="font-size: 12px; color: #6c757d;">This is an automated message, please do not reply.</p>
    </div>
    '''
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")
        flash('Failed to send OTP. Please try again later.', category='danger')


def generate_otp():
    return f"{random.randint(100000, 999999)}"

EXPIRATION_TIME = 600

def generate_token(data, expiration=EXPIRATION_TIME):
    s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
    return s.dumps(data).decode('utf-8')

def verify_token(token):
    s = Serializer(app.config['SECRET_KEY'])
    try:
        data = s.loads(token)
    except SignatureExpired:
        return None
    return data


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        password = request.form.get('password')
        roll_number = request.form.get('roll_number')
        batch = request.form.get('batch')
        course = request.form.get('course')
        branch = request.form.get('branch')

       

        if len(password) < 8 or not any(char.isdigit() for char in password) or not any(
                char.isalpha() for char in password):
            flash('Password must be at least 8 characters long and contain both letters and digits.', category='danger')
            return redirect(url_for('register'))

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email address already registered.', category='danger')
            return redirect(url_for('register'))

        otp = generate_otp()  # Ensure this function is defined to generate an OTP
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        session['temp_user'] = {
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'password': hashed_password,
            'roll_number': roll_number,
            'batch': batch,
            'course': course,
            'branch': branch,
            'otp': otp,
            'otp_generated_at': datetime.utcnow().replace(tzinfo=None)
        }

        send_otp_reg(email, otp)  # Ensure this function is defined to send an OTP
        flash('An OTP has been sent to your email. Please verify to complete registration.', category='info')
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

        # BUG FIX: Compare naive datetimes directly (no astimezone)
        otp_generated_at = temp_user.get('otp_generated_at')
        if isinstance(otp_generated_at, str):
            otp_generated_at = datetime.fromisoformat(otp_generated_at)
        otp_age = (datetime.utcnow() - otp_generated_at).total_seconds()

        if otp_age > 600:  # 10 minutes
            flash('OTP has expired. Please register again.', 'danger')
            session.pop('temp_user', None)
            return redirect(url_for('register'))

        if temp_user['otp'] == otp:
            new_user = User(
                email=temp_user['email'],
                first_name=temp_user['first_name'],
                last_name=temp_user['last_name'],
                password=temp_user['password'],
                roll_number=temp_user['roll_number'],
                batch=temp_user['batch'],
                course=temp_user['course'],
                branch=temp_user['branch'],
                is_verified=True
            )
            db.session.add(new_user)
            db.session.commit()
            session.pop('temp_user', None)
            flash('Your account has been created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Invalid OTP. Please try again.', 'danger')

    return render_template('verify_registration.html')

# Route for user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            if user.is_verified:
                login_user(user)
                flash('Login successful!', category='success')
                return redirect(url_for('home_page'))
            else:
                flash('Please verify your email before logging in.', category='danger')
        else:
            flash('Login failed. Check your credentials.', category='danger')
    return render_template('login.html')


# Route for user logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', category='info')
    return redirect(url_for('login'))


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            otp = generate_otp()
            expires_at = datetime.utcnow() + timedelta(minutes=10)
            reset_token = PasswordResetToken(user_id=user.id, otp=otp, expires_at=expires_at)
            db.session.add(reset_token)
            db.session.commit()
            send_otp_forget_pass(email, otp)
            session['reset_email'] = email  # Store email in session
            flash('An OTP has been sent to your email for password reset.', category='info')
            return redirect(url_for('verify_reset_password'))
        else:
            flash('Email not registered.', category='danger')

    return render_template('forgot_password.html')

# Route for verifying password reset
@app.route('/verify_reset_password', methods=['GET', 'POST'])
def verify_reset_password():
    email = session.get('reset_email')  # Retrieve email from session
    if not email:
        flash('No email found in session. Please try again.', category='danger')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        otp = request.form.get('otp')
        user = User.query.filter_by(email=email).first()
        if user:
            reset_token = PasswordResetToken.query.filter_by(user_id=user.id, otp=otp).first()
            if reset_token and reset_token.expires_at > datetime.utcnow():
                session['reset_user'] = user.id
                db.session.delete(reset_token)
                db.session.commit()
                flash('OTP verified. You can now reset your password.', category='success')
                return redirect(url_for('reset_password'))
            else:
                flash('Invalid or expired OTP. Please try again.', category='danger')
        else:
            flash('Email not registered.', category='danger')

    return render_template('verify_reset_password.html', email=email)

# Route for resetting password
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        password = request.form.get('password')
        user_id = session.get('reset_user')

        # Check if the password is None
        if password is None or len(password) < 8 or not any(char.isdigit() for char in password) or not any(
                char.isalpha() for char in password):
            flash('Password must be at least 8 characters long and contain both letters and digits.', category='danger')
            return redirect(url_for('reset_password'))

        if user_id:
            user = User.query.get(user_id)
            user.password = bcrypt.generate_password_hash(password).decode('utf-8')
            db.session.commit()
            session.pop('reset_user', None)
            flash('Your password has been reset successfully!', category='success')
            return redirect(url_for('login'))
        else:
            flash('No user session found. Please try again.', category='danger')

    return render_template('reset_password.html')



@app.route('/')
def home_page():
    search_term   = request.args.get('search', '')
    category_id   = request.args.get('category', '')
    status_filter = request.args.get('status', '')   # 'lost', 'found', or ''
    page          = request.args.get('page', 1, type=int)
    per_page      = 9

    query = Item.query.order_by(Item.date.desc())

    if search_term:
        query = query.filter(
            (Item.name.ilike(f'%{search_term}%')) |
            (Item.description.ilike(f'%{search_term}%'))
        )
    if category_id:
        query = query.filter(Item.category_id == category_id)
    if status_filter in ('lost', 'found'):
        query = query.filter(Item.status == status_filter)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    items      = pagination.items
    categories = Category.query.all()

    return render_template('home.html', items=items, categories=categories,
                           pagination=pagination, search_term=search_term,
                           category_id=category_id, status_filter=status_filter)


@app.route('/add_item', methods=['GET', 'POST'])
@login_required
def add_item():
    if request.method == 'POST':
        name        = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        category_id = request.form.get('category')
        status      = request.form.get('status')
        date_str    = request.form.get('date')
        location    = request.form.get('location', '').strip()
        image       = request.files.get('image')

        # Validate required fields
        if not name or not description or not status or not date_str:
            flash('Please fill in all required fields.', 'danger')
            return redirect(url_for('add_item'))

        # Validate date is not in the future
        try:
            item_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            if item_date > datetime.utcnow().date():
                flash('Date cannot be in the future.', 'danger')
                return redirect(url_for('add_item'))
        except ValueError:
            flash('Invalid date format.', 'danger')
            return redirect(url_for('add_item'))

        # Handle image upload
        image_filename = 'default.jpg'
        if image and image.filename:
            if not allowed_file(image.filename):
                flash('Only image files (JPG, PNG, GIF, WEBP) are allowed.', 'danger')
                return redirect(url_for('add_item'))
            image_filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
            image.save(image_path)

        new_item = Item(
            name=name,
            description=description,
            category_id=category_id if category_id else None,
            status=status,
            date=item_date,
            location=location,
            image_file=image_filename,
            user_id=current_user.id
        )
        db.session.add(new_item)
        db.session.commit()

        flash('Item reported successfully!', 'success')
        return redirect(url_for('item_detail', item_id=new_item.id))

    categories = Category.query.all()
    return render_template('add_item.html', categories=categories)


@app.route('/edit_item/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    item = Item.query.get_or_404(item_id)

    # BUG FIX: Only owner can edit
    if item.user_id != current_user.id:
        flash('You are not authorized to edit this item.', 'danger')
        return redirect(url_for('item_detail', item_id=item_id))

    # BUG FIX: Resolved items cannot be edited
    if item.resolved:
        flash('Resolved items cannot be edited.', 'warning')
        return redirect(url_for('item_detail', item_id=item_id))

    if request.method == 'POST':
        name        = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        date_str    = request.form.get('date_lost_or_found', '').strip()
        location    = request.form.get('location', '').strip()
        category_id = request.form.get('category')

        if not name or not description or not date_str:
            flash('Name, description and date are required.', 'danger')
            return redirect(url_for('edit_item', item_id=item_id))

        # BUG FIX: Validate date
        try:
            item_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            if item_date > datetime.utcnow().date():
                flash('Date cannot be in the future.', 'danger')
                return redirect(url_for('edit_item', item_id=item_id))
        except ValueError:
            flash('Invalid date format.', 'danger')
            return redirect(url_for('edit_item', item_id=item_id))

        item.name        = name
        item.description = description
        item.date        = item_date
        item.location    = location
        item.category_id = category_id if category_id else None

        image_file = request.files.get('image')
        if image_file and image_file.filename:
            if not allowed_file(image_file.filename):
                flash('Only image files (JPG, PNG, GIF, WEBP) are allowed.', 'danger')
                return redirect(url_for('edit_item', item_id=item_id))
            image_filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
            item.image_file = image_filename

        db.session.commit()
        flash('Item updated successfully.', 'success')
        # BUG FIX: Redirect to item detail, not home
        return redirect(url_for('item_detail', item_id=item_id))

    categories = Category.query.all()
    return render_template('edit_item.html', item=item, categories=categories)


@app.route('/delete_item/<int:item_id>', methods=['POST'])
@login_required
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    # BUG FIX: Only owner can delete
    if item.user_id != current_user.id:
        flash('You are not authorized to delete this item.', 'danger')
        return redirect(url_for('item_detail', item_id=item_id))
    # Delete related claims and notifications first to avoid FK constraint errors
    ClaimedItem.query.filter_by(item_id=item_id).delete()
    Notification.query.filter_by(item_id=item_id).delete()
    db.session.delete(item)
    db.session.commit()
    flash('Item deleted successfully.', 'success')
    return redirect(url_for('home_page'))

@app.route('/confirm_delete/<int:item_id>')
@login_required
def confirm_delete(item_id):
    item = Item.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('You are not authorized to delete this item.', 'danger')
        return redirect(url_for('item_detail', item_id=item_id))
    return render_template('confirm_delete.html', item=item)

@app.route('/item/<int:item_id>')
def item_detail(item_id):
    item = Item.query.get_or_404(item_id)
    # Pass claimer info to owner so they can see who contacted them
    claimer = None
    if item.claimed:
        claim_record = ClaimedItem.query.filter_by(item_id=item_id).first()
        if claim_record:
            claimer = User.query.get(claim_record.claimer_id)
    return render_template('item_details.html', item=item, claimer=claimer)


@app.route('/notifications')
@login_required
def view_notifications():
    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.sent_at.desc()).all()
    return render_template('notifications.html', notifications=notifications)


@app.route('/profile')
@login_required
def view_profile():
    claimed_items = (
        db.session.query(Item, ClaimedItem)
        .join(ClaimedItem, ClaimedItem.item_id == Item.id)
        .filter(ClaimedItem.claimer_id == current_user.id)
        .order_by(ClaimedItem.claimed_at.desc())
        .all()
    )
    return render_template('profile.html', claimed_items=claimed_items)



@app.route('/update_profile', methods=['GET', 'POST'])
@login_required
def update_profile():
    from models import CourseEnum, BranchEnum
    if request.method == 'POST':
        user = User.query.get(current_user.id)
        user.first_name  = request.form.get('first_name', '').strip()
        user.last_name   = request.form.get('last_name', '').strip()
        user.roll_number = request.form.get('roll_number', '').strip()

        batch = request.form.get('batch', '')
        try:
            user.batch = int(batch)
        except (ValueError, TypeError):
            flash('Invalid batch year.', 'danger')
            return redirect(url_for('update_profile'))

        # BUG FIX: Convert string form values to Enum members
        course_val = request.form.get('course', '')
        branch_val = request.form.get('branch', '')
        try:
            user.course = CourseEnum[course_val]
        except KeyError:
            # Try matching by value
            user.course = next((c for c in CourseEnum if c.value == course_val), user.course)
        try:
            user.branch = BranchEnum[branch_val]
        except KeyError:
            user.branch = next((b for b in BranchEnum if b.value == branch_val), user.branch)

        # Handle profile picture upload
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                user.profile_pic = filename

        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('view_profile'))

    return render_template('edit_profile.html')


def allowed_file(filename):
    allowed_extensions = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


# ── RESOLVE / MARK AS RETURNED ────────────────────────────────────
@app.route('/resolve_item/<int:item_id>', methods=['POST'])
@login_required
def resolve_item(item_id):
    item = Item.query.get_or_404(item_id)

    # Only owner can resolve
    if item.user_id != current_user.id:
        flash('You are not authorized to resolve this item.', 'danger')
        return redirect(url_for('item_detail', item_id=item_id))

    item.resolved = True
    item.claimed  = True  # ensure claimed is set too

    # Create a notification for the claimer if one exists
    claim = ClaimedItem.query.filter_by(item_id=item_id).first()
    if claim:
        notif = Notification(
            user_id=claim.claimer_id,
            item_id=item_id,
            message=f'Great news! The owner has marked "{item.name}" as returned/resolved.'
        )
        db.session.add(notif)

    db.session.commit()
    flash(f'"{item.name}" has been marked as returned/resolved!', 'success')
    return redirect(url_for('item_detail', item_id=item_id))


# ── CLAIM ITEM ────────────────────────────────────────────────────
@app.route('/claim_item/<int:item_id>', methods=['POST'])
@login_required
def claim_item(item_id):
    item = Item.query.get_or_404(item_id)

    # Can't claim your own item
    if item.user_id == current_user.id:
        flash('You cannot claim your own item.', 'danger')
        return redirect(url_for('item_detail', item_id=item_id))

    # BUG FIX: Can't claim an already resolved item
    if item.resolved:
        flash('This item has already been returned and resolved.', 'warning')
        return redirect(url_for('item_detail', item_id=item_id))

    # Already claimed
    if item.claimed:
        flash('This item has already been claimed.', 'warning')
        return redirect(url_for('item_detail', item_id=item_id))

    # Already claimed by this user
    existing = ClaimedItem.query.filter_by(item_id=item_id, claimer_id=current_user.id).first()
    if existing:
        flash('You have already submitted a claim for this item.', 'warning')
        return redirect(url_for('item_detail', item_id=item_id))

    # Create claim
    claim = ClaimedItem(item_id=item_id, claimer_id=current_user.id)
    item.claimed = True
    db.session.add(claim)

    # Status-aware notification to the owner in-app
    if item.status == 'lost':
        # LOST item: claimer = finder
        notif_msg  = (f'{current_user.first_name} {current_user.last_name} '
                      f'says they found your "{item.name}"! '
                      f'Contact them at {current_user.email}.')
        email_subj = f'Someone found your lost item: {item.name}!'
        email_body = (f'<p>Hi {{}},</p>'
                      f'<p><strong>{current_user.first_name} {current_user.last_name}</strong> '
                      f'says they have found your lost item: <strong>{item.name}</strong>.</p>'
                      f'<p>Contact them directly at: '
                      f'<a href="mailto:{current_user.email}">{current_user.email}</a></p>'
                      f'<p>Log in to view the item details and mark it as resolved once returned.</p>')
        flash_msg  = (f'You have reported finding "{item.name}"! '
                      f'The owner has been notified and will contact you.')
    else:
        # FOUND item: claimer = original owner (person who lost it)
        notif_msg  = (f'{current_user.first_name} {current_user.last_name} '
                      f'is claiming "{item.name}" as their lost item! '
                      f'Contact them at {current_user.email}.')
        email_subj = f'Someone is claiming the item you found: {item.name}!'
        email_body = (f'<p>Hi {{}},</p>'
                      f'<p><strong>{current_user.first_name} {current_user.last_name}</strong> '
                      f'is claiming that <strong>{item.name}</strong> belongs to them.</p>'
                      f'<p>Contact them directly at: '
                      f'<a href="mailto:{current_user.email}">{current_user.email}</a></p>'
                      f'<p>Log in to view the claim and mark as resolved once you hand it back.</p>')
        flash_msg  = (f'You have claimed "{item.name}" as yours! '
                      f'The finder has been notified and will contact you.')

    # Save notification to the owner
    owner = User.query.get(item.user_id)
    notif = Notification(
        user_id=item.user_id,
        item_id=item_id,
        message=notif_msg
    )
    db.session.add(notif)
    db.session.commit()

    # Send email to the owner
    if owner:
        try:
            msg = Message(
                email_subj,
                sender=app.config['MAIL_USERNAME'],
                recipients=[owner.email]
            )
            msg.html = f'''
            <div style="font-family:Arial,sans-serif;color:#333;max-width:500px;">
                <h2 style="color:#6c63ff;">Smart Lost &amp; Found System</h2>
                {email_body.format(owner.first_name)}
                <hr>
                <p style="font-size:12px;color:#999;">Automated message — do not reply.</p>
            </div>
            '''
            mail.send(msg)
        except Exception as e:
            print(f"Claim notification email failed: {e}")

    flash(flash_msg, 'success')
    return redirect(url_for('item_detail', item_id=item_id))


# ── FEEDBACK ──────────────────────────────────────────────────────
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

        user_id = current_user.id if current_user.is_authenticated else None

        fb = Feedback(
            user_id=user_id,
            name=name,
            email=email,
            rating=rating,
            category=category,
            message=message
        )
        db.session.add(fb)
        db.session.commit()

        flash('Thank you for your feedback! We really appreciate it.', 'success')
        return redirect(url_for('home_page'))

    return render_template('feedback.html')


# ── ERROR HANDLERS ────────────────────────────────────────────────
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    db.session.rollback()
    return render_template('500.html'), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
