from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators # Validators : Kullanıcıya sınırlandırma getirmek için 5 karakter olsun . İşaret olsun vs.
from passlib.hash import sha256_crypt
from functools import wraps
import os
from werkzeug.utils import secure_filename


# Kullanıcı giriş Decarator'ı = Kullanıcı giriş yapmasa bile localhost:5000/dashboard 
# yazdığında siteye girebiliyordu bunu yaptığımız zaman uyarı alıp ana sayfaya gönderiyoruz.
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için lütfen giriş yapınız...","danger")
            return redirect(url_for("login"))
    return decorated_function
# Kullanıcı Kayıt Formu
class RegisterForm(Form):
    last_name = StringField("Surname",validators=[validators.length(min = 4,max = 25)])
    first_name = StringField("Name ",validators=[validators.length(min = 4,max = 25)])
    username = StringField("Nickname",validators=[validators.length(min = 5,max = 35)])
    email = StringField("E-Mail Address",validators=[validators.DataRequired(message="Please enter a valid e-mail address ..")])
    password = PasswordField("Password",validators=[
        validators.DataRequired(message="Please set a password."),
        validators.EqualTo(fieldname = "confirm",message="Your password does not match!")
    ])
    job = StringField("Job")
    office_phone = StringField("Mobile Phone",validators=[validators.length(min=10,max=11)])
    phone = StringField("Office Phone",validators=[validators.length(min=10,max=11)])
    adress = StringField("Home address")
    confirm = PasswordField("Confirm Password")

# Kullanıcı Giriş Formu
class LoginForm(Form):
    username = StringField("Nickname")
    password = PasswordField("Password")


app  = Flask(__name__)


app.secret_key = "ybblog"  
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "ybblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)

#Ana Sayfa
@app.route("/") 

def index():
    
    return render_template("index.html")

#profil 
@app.route("/profile")
def profil():
    

    return render_template("profile.html")

#Makale Sayfası
@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()

    sorgu = "select*from articles"

    result = cursor.execute(sorgu)

    if result > 0 :
        articles = cursor.fetchall()

        return render_template("articles.html",articles = articles)
        
    
    else:
        return render_template("articles.html")




@app.route("/dashboard")
@login_required #Decaratorler için bu gereklidir.
def dashboard():
    cursor = mysql.connection.cursor()

    sorgu = "Select*from articles where author = %s"

    result = cursor.execute(sorgu,(session["username"],))

    if result > 0 :
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles = articles)
    else:
        return render_template("dashboard.html")

#Kayıt Olma
@app.route("/register",methods = ["GET","POST"])
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():
        first_name = form.first_name.data
        last_name= form.last_name.data
        username = form.username.data
        email = form.email.data
        job = form.job.data
        office_phone = form.office_phone.data
        phone = form.phone.data
        adress = form.adress.data
        password = sha256_crypt.encrypt(form.password.data)
        cursor = mysql.connection.cursor()
        sorgu = "Insert into users(first_name,last_name,email,username,password,job,office_phone,phone,adress) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)"

        cursor.execute(sorgu,(first_name,last_name,email,username,password,job,office_phone,phone,adress))# Tek elemanlı demet vermek için cursor.execute(sorgu,(name,)) gibi
        mysql.connection.commit()

        cursor.close()

        flash("Başarıyla kayıt oldunuz...","success")

        return redirect(url_for("login"))
    else:
        return render_template("register.html", form = form)

#login işlemi
@app.route("/login",methods = ["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data
        cursor = mysql.connection.cursor()
        sorgu = "Select*from users where username = %s"

        result = cursor.execute(sorgu,(username,))

        if result > 0 :
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered,real_password):
                flash("Başarıyla Giriş Yaptınız...","success")

                session["logged_in"] = True
                session["username"] = username 

                return redirect(url_for("index"))
            else:
                flash("Parolanızı kontrol ediniz.","danger")
                return redirect(url_for("login"))
        else:
            flash("Böyle Bir Kullanıcı Bulunmamaktadır...","danger")
            return redirect(url_for("login"))



    return render_template("login.html",form=form)

#Kullanıcı çıkış yapma formu
@app.route("/logout",methods = ["GET","POST"])

def logout():
    session.clear()
    flash("Başarıyla çıkış yapıldı...","success")
    return redirect(url_for("index"))

#Makale ekleme
@app.route("/addarticle",methods = ["GET","POST"])

def addarticle():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data

        content = form.content.data

        cursor = mysql.connection.cursor()

        sorgu = "Insert into articles(title,author,content) VALUES (%s,%s,%s)"

        cursor.execute(sorgu,(title,session["username"],content))

        mysql.connection.commit()

        cursor.close()

        flash("Makale başarıyla eklenmiştir.","success")

        return redirect(url_for("dashboard"))

    return render_template("addarticle.html",form=form)

# Makale Formu
class ArticleForm(Form):
    title = StringField("Makale Başlığı",validators=[validators.length(min = 5 , max = 100)])
    
    content = TextAreaField("Makale İçeriği",validators=[validators.length(min = 10)])

#Detay Sayfası
@app.route("/article/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()
    sorgu = "select * from articles where id = %s"
    result = cursor.execute(sorgu,(id,))

    if result > 0 :
        article = cursor.fetchone()
        return render_template("article.html",article = article)
    else:
        return render_template("article.html")
#Makale Silme
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()

    sorgu = "select * from articles where author= %s and id = %s"

    result = cursor.execute(sorgu,(session["username"],id))

    if result > 0 :
        sorgu2 = "delete from articles where id = %s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        return redirect(url_for("dashboard"))
    else:
        flash("Böyle bir makale yok veya bu işlem için yetkiniz yok ...!","danger")
        return redirect(url_for("index"))

#Who_Am_I
@app.route("/who_am_ı")
def ben():
    return render_template("ben.html")



#Makale Güncelleme
@app.route("/edit/<string:id>",methods = ["GET","POST"])
@login_required
def update(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        sorgu = "Select*from articles where id = %s and author = %s"
        result = cursor.execute(sorgu,(id,session["username"]))
        if result == 0:
            flash("Böyle bir makale yok veya bu işleme yetkiniz yok","danger")
            return redirect(url_for("index"))

        else:
            article = cursor.fetchone()
            form = ArticleForm()

            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html",form = form)

    else:
        # POST REQUEST

        form = ArticleForm(request.form)
        newTitle = form.title.data
        newContent = form.content.data

        sorgu2 = "Update articles Set title = %s,content = %s where id = %s"

        cursor = mysql.connection.cursor()

        cursor.execute(sorgu2,(newTitle,newContent,id))

        mysql.connect.commit()

        flash("Makale başarıyla güncellenmiştir...","success")

        return redirect(url_for("dashboard"))

#Makale Arama
@app.route("/search" , methods = ["GET","POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")
        cursor = mysql.connection.cursor()

        sorgu = "Select * from articles where title like '%"+ keyword +"%' "

        result = cursor.execute(sorgu)

        if result == 0 :
            flash("Aranan kelimeye uygun makale bulunamadı..","warning")
            return redirect(url_for("articles"))

        else:
            articles = cursor.fetchall()

            return render_template("articles.html",articles = articles)





if __name__ == "__main__":
    app.run(debug=True)
