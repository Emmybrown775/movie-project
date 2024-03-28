from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired
import os
import requests

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ["SECRET_KEY"]
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies.db"
API_KEY = os.environ["API_KEY"]

Bootstrap(app)
app.app_context().push()
db = SQLAlchemy(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    title = db.Column(db.String, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String, nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String, nullable=True)
    img_url = db.Column(db.String, nullable=False)


db.create_all()


class Add(FlaskForm):
    title = StringField(label="Movie Title", validators=[DataRequired()])
    submit = SubmitField(label="Add Movie")


class Edit(FlaskForm):
    new_rating = FloatField(label="Your rating out of 10 e.g 7.5", validators=[DataRequired()])
    new_review = StringField(label="Your Review", validators=[DataRequired()])
    submit = SubmitField(label="Done")




@app.route("/")
def home():
    movies = Movie.query.order_by(Movie.rating).all()
    for i in range(len(movies)):
        movies[i].ranking = len(movies) - i
    db.session.commit()
    return render_template("index.html", movies=movies)

@app.route("/add", methods=["GET", "POST"])
def add():
    form = Add()
    if form.validate():
        data = get_movies(form.title.data)
        return render_template("select.html", movies=data)

    return render_template("add.html", form=form)



@app.route("/edit", methods=["GET", "POST"])
def edit():
    id = request.args["id"]
    selected_movie = Movie.query.get(id)
    form = Edit()
    if request.method == "POST" and form.validate():
        selected_movie.rating = form.new_rating.data
        selected_movie.review = form.new_review.data
        db.session.commit()
        return redirect(url_for("home"))

    return render_template("edit.html", form=form)


@app.route("/delete")
def delete():
    id = request.args["id"]
    selected_movie = Movie.query.get(id)
    db.session.delete(selected_movie)
    db.session.commit()

    return redirect(url_for("home"))

def get_movies(title):
    params = {
        "api_key": API_KEY,
        "query": title
    }
    response = requests.get(url="https://api.themoviedb.org/3/search/movie", params=params)
    data = response.json()["results"]
    return data

@app.route("/add_movie/<id>")
def add_movie(id):
    params = {
        "api_key": API_KEY,
    }
    response = requests.get(f"https://api.themoviedb.org/3/movie/{id}", params=params)
    data = response.json()

    title = data["title"]
    img_url = f"https://image.tmdb.org/t/p/original/{data['poster_path']}"
    year = int(data["release_date"][:4])
    description = data["overview"]
    
    movie = Movie(
        title=title,
        img_url=img_url,
        year=year,
        description=description
    )

    db.session.add(movie)
    db.session.commit()

    new_movie = Movie.query.filter_by(title=title).first()
    id = new_movie.id
    return redirect(f"{url_for('edit')}?id={id}")


if __name__ == '__main__':
    app.run(debug=True)
