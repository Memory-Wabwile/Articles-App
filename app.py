from flask import Flask, render_template, flash , redirect ,url_for , session ,request ,logging
from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form , StringField , TextAreaField , PasswordField , validators # all the fields that we require
from passlib.hash import sha256_crypt # for encrypting the password

app = Flask(__name__)

# configuring MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'new_password' # insert your password for mysql
app.config['MYSQL_DB'] = 'articlesapp' # name of the database 
app.config['MYSQL_CURSORCLASS'] = 'DictCursor' # will set the default cursor to a dictionary


# initializing MySQL 
mysql = MySQL(app)

Articles = Articles()

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/articles')
def articles():
    return render_template('articles.html', articles = Articles)

@app.route('/article/<string:id>/')
def article(id):
    return render_template('article.html', id=id)


class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=1, max=50)])
    password = PasswordField('Password' , [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')


@app.route('/register' , methods=['GET' , 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        # declaring variables for storing form values 
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # create a cursor 
        cur = mysql.connection.cursor()

        # executing commands 
        cur.execute("INSERT INTO users(name,email,username,password) VALUES(%s,%s,%s,%s)", (name, email, username, password))

        # commit to DB
        mysql.connection.commit()

        # close the connection 
        cur.close()

        # flash messages 
        flash('You are now registered and can log in' , 'success')

        # redirecting to login page once successfully registered 
        return redirect(url_for('login'))
        
    return render_template('register.html' , form=form)

# user login 
@app.route('/login' , methods=['GET' , 'POST'])
def login():
    if request.method == 'POST' :
        # get form fields 
        username = request.form['username']
        password_login = request.form['password']

        # create a cursor 
        cur = mysql.connection.cursor()

        # get user by username 
        result = cur.execute("SELECT * FROM users WHERE username = %s" ,[username] )

        if result > 0:
            # Get stored hash 
            data = cur.fetchone()
            password = data['password']

            # compare password 
            if sha256_crypt.verify(password_login, password):
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in' , 'success')
                return redirect(url_for('dashboard'))
            else:
                error = "invalid login credentials"
                return render_template('login.html', error=error)
            #  close the connection 
            cur.close() 
        else:
            error = "Username not found"
            return render_template('login.html', error=error)

        
    return render_template('login.html')

# logout 
@app.route('/logout')
def logout():
    session.clear()
    flash("You are now logged out" , 'success')
    return redirect(url_for('login'))

# dashboard 
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


if __name__ == '__main__':
    app.secret_key = 'secret123'
    app.run(debug=True)
