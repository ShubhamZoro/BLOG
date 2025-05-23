from flask import Flask, render_template, redirect, url_for, flash, session 
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
# from functools import wraps
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import LoginForm, RegisterForm, CreatePostForm, CommentForm,Reset,SearchForm
from flask_gravatar import Gravatar
from flask_mail import Mail,Message
from itsdangerous import URLSafeTimedSerializer
import mysql.connector
import random

mydb=mysql.connector.connect(host='localhost',user='root',password=f"{os.getenv('mysql_password')}",database='users',auth_plugin = 'mysql_native_password')
my_cursor=mydb.cursor()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('secret_key')
ckeditor = CKEditor(app)
Bootstrap(app)
gravatar = Gravatar(app, size=100, rating='g', default='retro', force_default=False, force_lower=False, use_ssl=False, base_url=None)
emailg=""
nameg=""
passwordg=""

# from sqlalchemy import create_engine
# connection_string = "mysql+mysqlconnector://root:20gcebcs091@localhost:3306/users"
# engine = create_engine(connection_string, echo=True)
#CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://root:{os.getenv('mysql_password')}@localhost/users"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT']=465
app.config['MAIL_USERNAME']=os.getenv('email')
app.config['MAIL_PASSWORD']=os.getenv('password')
app.config['MAIL_USE_TLS']=False
app.config['MAIL_USE_SSL']=True
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
mail=Mail(app)
s=URLSafeTimedSerializer(os.getenv('secret_key'))



@login_manager.user_loader
def load_user(user_id):
    print(user_id)
    return User.query.get(int(user_id))


##CONFIGURE TABLE
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="comment_author")


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
    title = db.Column(db.String(250), unique=False, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    genre=db.Column(db.String(40),nullable=False)
    date = db.Column(db.String(250), nullable=False)
    overview=db.Column(db.String(5000), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    comments =relationship("Comment", back_populates="parent_post")


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    parent_post = relationship("BlogPost", back_populates="comments")
    comment_author = relationship("User", back_populates="comments")
    text = db.Column(db.Text, nullable=False)

# class UserLookups(db.Model):
#     __tablename__ = "lookups"
#     id = db.Column(db.Integer, primary_key=True)
#     user_id=db.Column(db.Integer, db.ForeignKey("users.id"))
#     title = db.Column(db.String(250), unique=False, nullable=False)
#     subtitle = db.Column(db.String(250), nullable=False)
#     genre=db.Column(db.String(40),nullable=False)
#     overview=db.Column(db.String(250), nullable=False)


with app.app_context():
    db.create_all()
#
# sql_select_query1 = f"""DROP TABLE users,blog_posts,comments, lookups"""
#
# my_cursor.execute(sql_select_query1)
# def admin_only(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         if current_user.id != 1:
#             return abort(403)
#         return f(*args, **kwargs)
#     return decorated_function

@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    if len(posts)>5:
        posts=random.choice(posts)[0:5]
    return render_template("index.html", all_posts=posts, current_user=current_user)


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():

        if User.query.filter_by(email=form.email.data).first():
            print(User.query.filter_by(email=form.email.data).first())
            #User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )

        global emailg,nameg,passwordg

        emailg=form.email.data
        nameg=form.name.data
        passwordg=hash_and_salted_password



        token = s.dumps(form.email.data,salt='email-confirm')
        print(token)
        msg=Message("This is an conformation link",sender='s9905020863@gmail.com',recipients=[form.email.data])
        link=url_for('confirm_email',token=token,_external=True)
        print(link)
        msg.body='your link is {}'.format(link)
        mail.send(msg)

        return render_template("verify.html")

    return render_template("register.html", form=form, current_user=current_user)

@app.route('/confirm_email/<token>')
def confirm_email(token):
    memail = s.loads(token, salt='email-confirm', max_age=300)
    global emailg,nameg,passwordg
    new_user = User(
            email=emailg,
            name=nameg,
            password=passwordg
        )



    db.session.add(new_user)
    db.session.commit()
    login_user(new_user)


    return redirect(url_for("get_all_posts"))

@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        print(type(email))
        password = form.password.data

        user1 = User.query.filter_by(email=email).first()
        query = f"SELECT id,email,password FROM users WHERE email='{email}'"
        print(email)
        my_cursor.execute(query)
        user= my_cursor.fetchone()

        print(user)
        # Email doesn't exist or password incorrect.
        if not user[0]:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user[2], password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            session['loggedin'] = True
            session['id'] = user[0]
            session['email'] = user[1]
            login_user(user1)
            return redirect(url_for('get_all_posts'))
    return render_template("login.html", form=form, current_user=current_user)

@app.route('/ResetPassword', methods=["GET", "POST"])
def ResetPassword():
    form = Reset()
    if form.validate_on_submit():
        email = form.email.data
        password1 = form.password1.data
        password2=form.password2.data

        if (password1 == password2):
            hash_and_salted_password = generate_password_hash(
                form.password1.data,
                method='pbkdf2:sha256',
                salt_length=8
            )
            global emailg,passwordg;
            emailg=email
            passwordg=hash_and_salted_password

            token = s.dumps(form.email.data, salt='reset')
            print(token)
            msg = Message("This is an conformation link", sender='s9905020863@gmail.com', recipients=[form.email.data])
            link = url_for('reset', token=token, _external=True)
            print(link)
            msg.body = 'your link is {}'.format(link)
            mail.send(msg)

            return render_template("verify.html")

        else:
            flash('please enter valid Email or Password does not match.')
            return redirect(url_for('ResetPassword'))

    return render_template("ResetPassword.html", form=form, )

@app.route('/reset/<token>')
def reset(token):
    global emailg ,passwordg
    memail = s.loads(token, salt='reset', max_age=300)
    user = User.query.filter_by(email=emailg).first()
    sql = f"UPDATE users SET password = '{passwordg}' WHERE email = '{emailg}'"
    my_cursor.execute(sql)

    mydb.commit()
    # user.password = passwordg
    # db.session.commit()
    login_user(user)

    return redirect(url_for("get_all_posts"))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    form = CommentForm()
    requested_post = BlogPost.query.get(post_id)
    # sql_select_query = f"""SELECT *
    #                       FROM users,blog_posts WHERE users.id={post_id}"""

    # my_cursor.execute(sql_select_query)
    # out = my_cursor.fetchall()
    #
    # requested_post = out

    print(requested_post)
#     try:
#         print(current_user.id)
#         lookups=UserLookups(title=requested_post.title,
#                             user_id=current_user.id,
#                              overview=requested_post.overview,
#                              subtitle=requested_post.title,
#                              genre=requested_post.genre
#                              )
#         db.session.add(lookups)
#         db.session.commit()
    
    print("not found")
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.")
            return redirect(url_for("login"))

        new_comment = Comment(
            text=form.comment_text.data,
            comment_author=current_user,
            parent_post=requested_post
        )
        db.session.add(new_comment)
        db.session.commit()

    return render_template("post.html", post=requested_post, form=form, current_user=current_user)


@app.route("/about")
def about():
    return render_template("about.html", current_user=current_user)


@app.route("/contact")
def contact():
    return render_template("contact.html", current_user=current_user)


@app.route("/new-post", methods=["GET", "POST"])
@login_required
def add_new_post():
    form = CreatePostForm()

    if form.validate_on_submit():

        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            genre=form.genre.data,
            body=form.body.data,
            overview=form.overview.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))

    return render_template("make-post.html", form=form, current_user=current_user)




@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        genre=post.genre,
        img_url=post.img_url,
        author=current_user,
        body=post.body,
        overview=post.overview
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.body = edit_form.body.data
        post.overview=edit_form.overview.data
        post.genre=edit_form.genre.data

        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form, is_edit=True, current_user=current_user)


@app.route("/delete/<int:post_id>")
# @admin_only
def delete_post(post_id):
    # post_to_delete = BlogPost.query.get(post_id)
    # db.session.delete(post_to_delete)
    # db.session.commit()
    sql_Delete_query = f"""Delete from blog_posts where id = {post_id}"""
    my_cursor.execute(sql_Delete_query)
    mydb.commit()
    return redirect(url_for('get_all_posts'))

@app.context_processor
def base():
    form=SearchForm()
    return dict(form=form)

@app.route('/search',methods=["POST"])
def search():
    form=SearchForm()
    posts=BlogPost.query
    if form.validate_on_submit():
        searched=form.searched.data
        posts=posts.filter(BlogPost.body.like('%' + searched + '%'))
        posts =posts.order_by(BlogPost.title).all()
        return render_template("Search.html",form=form,searched=searched,posts=posts)

@app.route('/my_posts')
@login_required
def my_posts():
    post=current_user.posts

    return render_template("mypost.html",posts=post)
if __name__=='__main__':
    app.run(debug=True)
