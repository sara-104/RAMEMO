import os, base64, re, secrets

from flask import Flask, render_template, request, redirect
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash   #ログイン機能パスワード
from datetime import datetime
from plotly.offline import plot
from sqlalchemy import func
import plotly.graph_objs as go
from plotly.subplots import make_subplots


UPLOAD_FOLDER = './static/images'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'heif'}

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ramemo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = os.urandom(24)

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

class Post(db.Model):
    __tablename__ = 'post'
    id = db.Column(db.Integer, primary_key=True)
    shop = db.Column(db.String(64), nullable=False)
    item = db.Column(db.String(64), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Integer, nullable=True)
    memo = db.Column(db.String(120))
    adress = db.Column(db.String(64))
    date = db.Column(db.Date)
    image = db.Column(db.String(100))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), nullable=False, unique=True)
    password = db.Column(db.String(15))
    
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def hello():
    return render_template('hello.html', methods=['GET', 'POST'])

@app.route("/index", methods=['GET','POST'])
@login_required
def index():
    posts = Post.query.order_by(Post.date.desc()).all()
    ramen_count = Post.query.count()
    filebinary = []
    for post in posts :
        img_base64_string = re.sub('b\'|\'', '', str(post.image))
        filebinary.append(f'data:image/png;base64,{img_base64_string}')
    return render_template('index.html', posts=posts, filebinary = filebinary, ramen_count=ramen_count)

@app.route("/search", methods=['GET'])
def search():
    query = request.args.get('query', '')
    posts = Post.query.filter(Post.shop.ilike(f'%{query}%')| Post.item.ilike(f'%{query}%')| Post.date.ilike(f'%{query}%')| Post.memo.ilike(f'%{query}%')| Post.adress.ilike(f'%{query}%')).all()
    ramen_search_count = Post.query.filter(Post.shop.ilike(f'%{query}%')| Post.item.ilike(f'%{query}%')| Post.date.ilike(f'%{query}%')| Post.memo.ilike(f'%{query}%')| Post.adress.ilike(f'%{query}%')).count()
    filebinary = []
    for post in posts :
        img_base64_string = re.sub('b\'|\'', '', str(post.image))
        filebinary.append(f'data:image/png;base64,{img_base64_string}')

    return render_template('search_results.html', posts=posts, filebinary = filebinary, query=query, ramen_search_count=ramen_search_count)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_monthly_post_counts():
    # 月ごとのラーメンの数をデータベースから取得
    result = db.session.query(func.strftime('%Y-%m', Post.date).label('year_month'), func.count(Post.id)).group_by('year_month').all()

    # 結果を辞書に変換
    monthly_counts = {entry[0]: entry[1] for entry in result}

    return monthly_counts

def plot_monthly_post_counts(monthly_counts):
    fig = make_subplots()
    fig.add_trace(go.Bar(x=list(monthly_counts.keys()),
                         y=list(monthly_counts.values()),
                         marker_color='#F21D1D'
                         ))

    # レイアウトの設定
    fig.update_layout(
        
        yaxis=dict(title='食べたラーメンの数'),
        plot_bgcolor='#F5DEB3',  # グラフ領域の背景色
        barmode='group',  # 棒グラフのモード（'group'はグループ化）
        bargap=0.3,  # 棒グラフ間の隙間
        font_color='#333',
        font_family= 'MOBO',
        font_size= 15,
        paper_bgcolor='#FFFDF5',
    )
    fig.update_traces(
        textfont_size=12,
        textangle=0,
        textposition='outside',
        cliponaxis=False
        )
    
    graph_html = fig.to_html(full_html=False, include_plotlyjs='cdn')

    return graph_html

@app.route("/monthly_post_counts")
@login_required
def monthly_post_counts():
    # 月ごとの投稿数を取得
    monthly_counts = get_monthly_post_counts()

    # グラフをHTMLに変換
    graph_html = plot_monthly_post_counts(monthly_counts)

    return render_template('monthly_post_counts.html', graph_html=graph_html)

@app.route('/create', methods=['GET','POST'])
@login_required
def create():
    if request.method == 'POST':
        shop = request.form.get('shop')
        item = request.form.get('item')
        price = request.form.get('price')
        adress = request.form.get('adress')
        date_str = request.form.get('date')
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        rating = request.form.get('rating')
        memo = request.form.get('memo')
        file = request.files['image']
        img_base64 = base64.b64encode(file.stream.read())

        post = Post(shop=shop, adress=adress, item=item, price=price, rating=rating, memo=memo, date=date_obj, image=img_base64)

        db.session.add(post)
        db.session.commit()

        posts = Post.query.all()
        ramen_count = Post.query.count()
        filebinary = []
        for post in posts :
            img_base64_string = re.sub('b\'|\'', '', str(post.image))
            filebinary.append(f'data:image/png;base64,{img_base64_string}')

        return render_template('index.html', posts=posts, filebinary = filebinary, ramen_count=ramen_count)
    else:
        return render_template('create.html')
    
@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User(username=username, password=generate_password_hash(password))

        db.session.add(user)
        db.session.commit()
        return redirect('/login')
    else:        
        return render_template('signup.html')
    
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if check_password_hash(user.password, password):
            login_user(user)
            return redirect('/index')
    else:        
        return render_template('login.html')
    
@app.route('/logout')
@login_required #ログインしている人じゃないとアクセスできない
def logout():
    logout_user()
    return redirect('/login')

@app.route('/<int:id>/detail', methods=['GET'])
@login_required
def detail(id):
    post = Post.query.get(id)
    img_base64_string = re.sub('b\'|\'', '', str(post.image))
    image = f'data:image/png;base64,{img_base64_string}'
    return render_template('detail.html' , post = post, image = image)

@app.route("/<int:id>/update", methods=['GET', 'POST'])
@login_required
def update(id):
    post = Post.query.get(id)
    if request.method == 'GET':
         return render_template('update.html', post=post)
    else: 
        post.shop = request.form.get('shop')
        post.item = request.form.get('item')
        post.price = request.form.get('price')
        post.adress = request.form.get('adress')
        post.date_str = request.form.get('date')
        post.date_obj = datetime.strptime(post.date_str, '%Y-%m-%d').date()
        post.rating = request.form.get('rating')
        post.memo = request.form.get('memo')
        post.file = request.files.get('image')
        post.img_base64 = base64.b64encode(post.file.stream.read())

        db.session.commit()

        posts = Post.query.all()
        ramen_count = Post.query.count()
        filebinary = []
        for post in posts :
            img_base64_string = re.sub('b\'|\'', '', str(post.image))
            filebinary.append(f'data:image/png;base64,{img_base64_string}')

        return render_template('index.html', posts=posts, filebinary = filebinary, ramen_count=ramen_count)       

    
@app.route("/<int:id>/delete", methods=['GET'])
@login_required
def delete(id):
    post = Post.query.get(id)

    db.session.delete(post)
    db.session.commit()
    return redirect('/index')

@app.route("/calender")
@login_required
def calender():
    return render_template('calender.html', methods=['GET', 'POST'])

@app.route("/get_posts_by_date", methods=['POST'])
@login_required
def get_posts_by_date():
    date_str = request.form.get('date')
    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    posts = Post.query.filter_by(date=date_obj).all()
    
    # postsをJSON形式でクライアントに返す
    return render_template('posts_by_date.html', posts=posts)

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)