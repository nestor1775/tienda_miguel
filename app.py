# app.py
from flask import Flask, render_template, redirect, url_for, flash, request
from config import Config
from models import db, User, bcrypt, Carritodb
from forms import RegistrationForm, LoginForm
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from flask_mail import Mail, Message


app = Flask(__name__)
app.config.from_object(Config)

app.config['MAIL_SERVER'] = 'smtp.example.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@example.com'
app.config['MAIL_PASSWORD'] = 'your-password'
mail = Mail(app)

db.init_app(app)
bcrypt.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_request
def create_tables():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('cuenta creada con exito ;)')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('algo salio mal')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/products')
def products():
    return render_template('products.html')


# @login_required


@app.route('/carrito', methods=['GET','POST','DELETE'])
def ver_carrito():
    if request.method == 'POST':
        id_borrar= request.form.get('id_borrar')
        if id_borrar:
            lista = Carritodb.query.filter_by(id=id_borrar).first()
            if lista:
                db.session.delete(lista)
                db.session.commit()
                return redirect(url_for('carrito'))
    listas = Carritodb.query.all()
    return render_template('carrito.html', listas=listas)

@app.route('/buy', methods=['POST'])
@login_required
def buy():
    user_email = current_user.email
    carritos = Carritodb.query.filter_by(idUsuario=user_email).all()

    msg = Message('Compra Realizada', sender='your-email@example.com', recipients=[user_email])
    msg.body = f'Gracias por tu compra. Has comprado {len(carritos)} productos.'
    mail.send(msg)

    # Borrar todos los elementos del carrito
    for carrito in carritos:
        db.session.delete(carrito)
    db.session.commit()

    flash('Compra realizada. Se ha enviado un correo de confirmación.')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
