from flask import Flask, request, redirect, url_for, render_template, flash, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import boto3
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'supersecretkey'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# In-memory user database for simplicity
users = {}

# AWS S3 configuration
s3 = boto3.client('s3')
BUCKET_NAME = 'your-s3-bucket-name'

class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in [user.username for user in users.values()]:
            flash('Username already exists.')
            return redirect(url_for('signup'))
        password_hash = generate_password_hash(password)
        user_id = str(len(users) + 1)
        new_user = User(user_id, username, password_hash)
        users[user_id] = new_user
        login_user(new_user)
        return redirect(url_for('upload'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST'):
        username = request.form['username']
        password = request.form['password']
        user = next((user for user in users.values() if user.username == username), None)
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('upload'))
        else:
            flash('Invalid username or password.')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            s3.upload_fileobj(file, BUCKET_NAME, file.filename)
            flash('File uploaded successfully.')
            return redirect(url_for('upload'))
    return render_template('upload.html')

@app.route('/download/<filename>')
@login_required
def download(filename):
    try:
        file_obj = s3.get_object(Bucket=BUCKET_NAME, Key=filename)
        return send_file(BytesIO(file_obj['Body'].read()), attachment_filename=filename)
    except Exception as e:
        flash(f'Error downloading file: {str(e)}')
        return redirect(url_for('upload'))

if __name__ == '__main__':
    app.run(debug=True)
