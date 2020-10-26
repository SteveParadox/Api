import uuid
import os
from flask import Blueprint, jsonify
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import FileField, StringField, SubmitField
from wtforms.validators import DataRequired

from Api import db, request, render_template
from Api.models import Movie, MovieSchema, Users, UsersSchema
from Api.utils import save_img
import requests
import json
import imdb

r = requests.request("GET", "https://api.themoviedb.org/3/movie/550?api_key=03fe919b123d0ced4b33dd633638527a")

# creating instance of IMDb
ia = imdb.IMDb()

api = Blueprint('api', __name__)
CHUNK_SIZE = 512


@api.route('/', methods=['GET'])
def home():
    movies = Movie.query.all()
    movie_schema = MovieSchema(many=True)
    result = movie_schema.dump(movies)
    return jsonify(result), 200

# registering 
@api.route('/sign_up', methods=['POST'])
def sign_up():
  data= request.get_json()
  name= data['name']
  dob=data['dob']
  email=data['email']
  password= data['password']
  user = User.query.filter_by(email=email).first()
  if user:
    return jsonify({
      "message" : "User already registered"
    })
  else:
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    users= Users()
    users.name=name
    users.dob=dob
    users.email=email
    users.password=hashed_password
    try:
      db.session.add(users)
      db.session.commit()
      
    except:
      return jsonify({
                "status": "error",
                "message": "Could not add user"
            })
    return jsonify({
            "status": "success",
            "message": "User added successfully"
        }), 201
  
  #registering user's preferred genre
@api.route('/sign_up/genre', methods=['POST'])
def genre():
  pass
#logging in  
@api.route('/login')
def login():
    data = request.get_json()
    name = data['name']
    password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    user = User.query.filter_by(name=name).first()
    if not  user and bcrypt.check_password_hash(user.password, data['password']):
          return jsonify({
              "status": "failed",
              "message": "Failed getting user"
          }), 401
    login_user(user)
    return jsonify({
            "status": "success",
            "message": "login successful",
            "data": {
                "id": user.id,
                "name": user.name
            }
       }), 200



#logging out
@api.route('/logout')
@login_required
def logout():
    logout_user()

            
  
class Movies_(FlaskForm):
    movie = FileField('Video', validators=[FileAllowed(['mp4', 'webm', 'hd'])])
    name = StringField(validators=[DataRequired()])
    submit = SubmitField('Submit ')


    
    
@api.route('/upload', methods=['GET', 'POST'])
def upload():
    # data = request.get_json()
    form = Movies_()
    id = ''
    if form.validate_on_submit():
        name = str(form.name.data)
        search = ia.search_movie(name)
        for i in range(0, 1):
            # getting the id
            id = search[i].movieID
        movie = requests.get(
            f"https://api.themoviedb.org/3/movie/tt{id}?api_key=03fe919b123d0ced4b33dd633638527a&language=en-US"
        )
        CONFIG_PATTERN = 'http://api.themoviedb.org/3/configuration?api_key={key}'
        KEY = '03fe919b123d0ced4b33dd633638527a'

        url = CONFIG_PATTERN.format(key=KEY)
        r = requests.get(url)
        config = r.json()
        base_url = config['images']['base_url']
        sizes = config['images']['poster_sizes']

        def size_str_to_int(x):
            return float("inf") if x == 'original' else int(x[1:])

        filename = ''
        max_size = max(sizes, key=size_str_to_int)

        IMG_PATTERN = 'http://api.themoviedb.org/3/movie/{imdbid}/images?api_key={key}'
        r = requests.get(IMG_PATTERN.format(key=KEY, imdbid=f'tt{id}'))
        api_response = r.json()

        posters = api_response['posters']
        poster_urls = []
        for poster in posters:
            rel_path = poster['file_path']
            url = "{0}{1}{2}".format(base_url, max_size, rel_path)
            poster_urls.append(url)
        for nr, url in enumerate(poster_urls):
            r = requests.get(url)
            filetype = r.headers['content-type'].split('/')[-1]
            filename = 'poster_{0}.{1}'.format(nr + 1, filetype)
        with open(os.path.join(os.path.abspath('Api/static/movies/'), filename), 'wb') as w:
            w.write(r.content)
        movie_detail = movie.text
        dict_movie = json.loads(movie_detail)
        movie_name = save_img(form.movie.data)
        video_file = request.files['movie']
        description = str(dict_movie['overview'])
        review = str(dict_movie["vote_average"])
        movies = Movie()
        movies.public_id = str(uuid.uuid4())
        movies.name = str(dict_movie['original_title'])
        movies.description = description
        movies.review = review
        movies.poster = filename
        movies.movies = movie_name
        movies.movie_data = video_file.read(CHUNK_SIZE)
        db.session.add(movies)
        db.session.commit()
    c = Movie.query.all()
    return render_template('_.html', form=form, c=c)

#link to redirect to selected movie
@api.route('/get/movie/<string:u_id>/')
def get_by_name(u_id):
    movie_name = Movie.query.filter_by(public_id=u_id).first()
    movie_schema = MovieSchema()
    result = movie_schema.dump(movie_name)
    try:
      return jsonify({
          'name': result['name'],
          'description': result['description'],
          'review': result['review'],
          'poster': result['poster'],
          'movies': result['movies']
      }), 200
    except:
      return jsonify({
        'message' : "could mot load data"
      })

#searching for movie
@api.route('/search/movie', methods=['POST'])
def search():
    data = request.get_json()
    print(data["name"])
    movie_name = Movie.query.filter_by(name=data['name']).first()
    if not movie_name:
        return jsonify({
            "message": " Could not find Name"
        }), 404
    else:
        movie_schema = MovieSchema()
        result = movie_schema.dump(movie_name)
        return jsonify({
            'name': result['name'],
            'description': result['description'],
            'review': result['review'],
            'poster': result['poster'],
            #'movies': result['movies']
        }), 200
      
      
@api.route('/')
def user_com():
  pass
