from flask import Flask, render_template, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, FileField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange
from werkzeug.utils import secure_filename
from pathlib import Path
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Vitaly'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db'
app.config['MAX_CONTENT_LENGTH'] = 3 * 1024**2

db = SQLAlchemy(app)

BASEDIR = Path(__file__).parent
UPLOAD_DIR = BASEDIR / 'static' / 'img'


class Movie(db.Model):
    m_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    cover = db.Column(db.String(255), nullable=False)
    reviews = db.relationship('Review', back_populates='movie')
    created = db.Column(db.DateTime, default=datetime.utcnow())

    def __repr__(self):
        return f'Movie {self.m_id}: ({self.title[:20]}...)'


class Review(db.Model):
    r_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    text = db.Column(db.Text, nullable=False)
    score = db.Column(db.Integer, nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.m_id', ondelete='CASCADE'))
    movie = db.relationship('Movie', back_populates='reviews')
    created = db.Column(db.DateTime, default=datetime.utcnow())


class MovieForm(FlaskForm):
    title = StringField(
        'Title',
        validators=[
            DataRequired(
                message='Title cant be empty!'
            ),
            Length(
                max=255,
                message='Title is too big!'
            )
        ]
    )
    description = TextAreaField(
        'Description',
        validators=[
            DataRequired(
                message='Description cant be empty!'
            )
        ]
    )
    cover = FileField(
        'Cover',
        validators=[
            FileRequired(
                message='Cover cant be empty!'
            ),
            FileAllowed(
                ['png', 'jpg'],
                message='Only PNG/JPG are allowed!'
            )
        ]
    )
    submit = SubmitField('Add')


class ReviewForm(FlaskForm):
    name = StringField(
        'Name',
        validators=[
            DataRequired(
                message='Name cant be empty!'
            ),
            Length(
                max=64,
                message='Name is too big!'
            )
        ]
    )
    text = TextAreaField(
        'Text',
        validators=[
            DataRequired(
                message='Text cant be empty!'
            )
        ]
    )
    score = SelectField(
        'Score',
        choices=range(11),
        coerce=int,
        validators=[
            DataRequired(
                message='Score cant be empty!'
            ),
            NumberRange(
                min=0,
                max=10,
                message='Score should be from 0 to 10!'
            )
        ]
    )
    submit = SubmitField('Send')


with app.app_context():
    db.create_all()


@app.route('/')
def home():
    movies = Movie.query.all()

    context = {'movies': movies}

    return render_template('home.html', **context)


@app.route('/movie/<int:m_id>', methods=['GET', 'POST'])
def get_movie(m_id):
    movie = Movie.query.get(m_id)

    if movie is None:
        return redirect(url_for('home'))

    if movie.reviews:
        average_score = round(sum(review.score for review in movie.reviews) / len(movie.reviews), 2)

    else:
        average_score = 0

    form = ReviewForm(score=10)

    if form.validate_on_submit():
        review = Review(
            name=form.name.data,
            text=form.text.data,
            score=form.score.data,
            movie_id=movie.m_id
        )

        db.session.add(review)
        db.session.commit()

        return redirect(url_for('get_movie', m_id=movie.m_id))

    context = {
        'movie': movie,
        'average_score': average_score,
        'form': form
    }

    return render_template('movie.html', **context)


@app.route('/add-movie', methods=['GET', 'POST'])
def add_movie():
    form = MovieForm()

    if form.validate_on_submit():
        cover = form.cover.data
        cover_name = secure_filename(cover.filename)
        UPLOAD_DIR.mkdir(exist_ok=True)
        cover.save(UPLOAD_DIR / cover_name)

        movie = Movie(
            title=form.title.data,
            description=form.description.data,
            cover=cover_name
        )

        db.session.add(movie)
        db.session.commit()

        return redirect(url_for('get_movie', m_id=movie.m_id))

    context = {'form': form}

    return render_template('add-movie.html', **context)


app.run(debug=True)
