from flask import Flask, render_template, flash , redirect ,url_for , session ,request ,logging
from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form , StringField , TextAreaField , PasswordField , validators # all the fields that we require
from passlib.hash import sha256_crypt # for encrypting the password
from functools import wraps

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
    # create cursor 
    cur = mysql.connection.cursor()

    # get articles 
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
       return render_template('articles.html', articles=articles) 
    else:
        msg= 'No articles Found'
        return render_template('articles.html' , msg=msg)
    # close the connection 
    cur.close()
    
# single article 
@app.route('/article/<string:id>/')
def article(id):
    # create cursor 
    cur = mysql.connection.cursor()
        
    # get articles 
    result = cur.execute("SELECT * FROM articles WHERE id=%s" , [id])

    article = cur.fetchone()
    return render_template('article.html', article=article)


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

# check if user logged in 
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
        
    return decorated_function

# logout 
@app.route('/logout')
def logout():
    session.clear()
    flash("You are now logged out" , 'success')
    return redirect(url_for('login'))

# dashboard 
@app.route('/dashboard')
@login_required
def dashboard():
    # create cursor 
    cur = mysql.connection.cursor()

    # get articles 
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
       return render_template('dashboard.html', articles=articles) 
    else:
        msg= 'No articles Found'
        return render_template('dashboard.html' , msg=msg)
    # close the connection 
    cur.close()

# Article Form class
class ArticlesForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])

# add article 
@app.route('/add_article',methods=['GET' , 'POST'] )
@login_required
def add_article():
    form = ArticlesForm(request.form)
    if request.method == 'POST' and form.validate():
        title= form.title.data
        body = form.body.data

        # create the cursor 
        cur = mysql.connection.cursor()

        # executing commands 
        cur.execute("INSERT INTO articles(title,body,author) VALUES(%s,%s,%s)", (title,body,session['username']))

        # commit to DB
        mysql.connection.commit()

        # close the connection 
        cur.close()

        # flash messages 
        flash('Article created' , 'success')
        return redirect(url_for('dashboard'))

    return render_template('add_article.html' , form=form)

# edit article 
@app.route('/edit_article/<string:id>/',methods=['GET' , 'POST'] )
@login_required
def edit_article(id):
    # create cursor 
    cur = mysql.connection.cursor()

    # get the article by the id 
    result = cur.execute("SELECT * FROM articles WHERE id = %s" ,[id] )

    # fetch one article 
    article = cur.fetchone()

    # get the form 
    form = ArticlesForm(request.form)

    # populate the article form fields with title and body from the database
    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title= request.form['title']
        body = request.form['body']

        # create the cursor 
        cur = mysql.connection.cursor()

        # executing commands => update the articles table with the fields below.
        cur.execute("UPDATE articles SET title=%s,body=%s WHERE id=%s", (title,body,id))

        # commit to DB
        mysql.connection.commit()

        # close the connection 
        cur.close()

        # flash messages 
        flash('Article Updated' , 'success')
        return redirect(url_for('dashboard'))

    return render_template('edit_article.html' , form=form)

#  delete article 
@app.route('/delete_article/<string:id>/',methods=['POST'])
@login_required
def delete_article(id):
    # create cursor             
    cur = mysql.connection.cursor()

    # executing commands => delete from the articles table the article with that specific id.
    cur.execute("DELETE FROM articles WHERE id=%s", [id])

    # commit to DB
    mysql.connection.commit()

    # close the connection 
    cur.close()

    # flash messages 
    flash('Article Deleted' , 'success')

    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.secret_key = 'secret123'
    app.run(debug=True)
