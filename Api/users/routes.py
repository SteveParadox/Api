import datetime
import os

from flask import *
from flask_login import login_user, logout_user, login_required, current_user
from Api.models import Users, UsersSchema, Data, DataSchema, Friend, FriendSchema, Activities, ActivitiesSchema, \
    Exciting, ExcitingSchema
from Api import db, bcrypt
from flask_cors import cross_origin
import cloudinary as Cloud
import cloudinary.uploader
from Api.utils import save_img
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from Api.config import Config

users = Blueprint('users', __name__)


# registering a user
@users.route('/api/sign_up', methods=['POST'])
@cross_origin()
def sign_up():
    data = request.get_json()
    name = data['name']
    dob = data['dob']
    phone_no = data['phone_no']
    country= data['country']
    email = data['email']
    password = data['password']
    user = Users.query.filter_by(email=email).first()
    if user:
        return jsonify({
            "message": "User already registered"
        })
    else:
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        users = Users()
        users.name = name
        users.dob = dob
        users.email = email
        users.phone_no = phone_no
        users.country= country
        users.password = hashed_password
        try:
            db.session.add(users)
            db.session.commit()
        except:
            return jsonify({
                "status": "error",
                "message": "Could not add user"
            }), 401

        return jsonify({
            "status": "success",
            "message": "User added successfully"
        }), 201


# logging in
@users.route('/api/login', methods=['POST'])
@cross_origin()
def login(expires_sec=1800):
    data = request.get_json()
    email = data['email']
    user = Users.query.filter_by(email=email).first()
    if user and bcrypt.check_password_hash(user.password, data['password']):
        login_user(user)
        user.logged_in = True
        db.session.commit()
        s = Serializer(Config.SECRET_KEY , expires_sec)
        payload= {
                "id": user.id,
                "name": user.name
            }
        return jsonify({
            "status": "success",
            "message": "login successful",
            "data": {
                "id": user.id,
                "name": user.name,
                "token": "Bearer " + s.dumps(payload).decode('utf-8')
            }
        }), 200
    return jsonify({
        "status": "failed",
        "message": "Failed getting user"
    }), 401


# registering user's preferred genre for data processing
@users.route('/api/select/genre', methods=['POST'])
@cross_origin()
@login_required
def genre():
    data = request.get_json()
    action = data['action']
    comedy = data['comedy']
    horror = data['horror']
    documentary = data['documentary']
    mystery = data['mystery']
    animation = data['animation']
    sci_fi = data['sci-fi']
    romance = data['romance']
    erotic = data['erotic']
    fantasy = data['fantasy']
    drama = data['drama']
    thriller = data['thriller']
    children = data['children']
    family = data['family']
    crime = data['crime']
    try:
        user = Data(love=current_user)
        user.action = action
        user.comedy = comedy
        user.horror = horror
        user.documentary = documentary
        user.mystery = mystery
        user.animation = animation
        user.sci_fi = sci_fi
        user.romance = romance
        user.erotic = erotic
        user.fantasy = fantasy
        user.drama = drama
        user.thriller = thriller
        user.children = children
        user.crime = crime
        user.family = family
        db.session.add(user)
        db.session.commit()
        return jsonify({
            "message": "committed"
        })
    except:
        return jsonify({

            "message": 'error'
        })


@users.route('/logout')
@cross_origin()
@login_required
def logout_users():
    user = Users.query.filter_by(email=current_user.email).first()
    user.logged_in = False
    db.session.commit()
    logout_user()

    return redirect(url_for('api.home'))


# logging out
@users.route('/api/logout', methods=['POST'])
@cross_origin()
@login_required
def logout():
    user = Users.query.filter_by(email=current_user.email).first()
    user.logged_in = False
    db.session.commit()
    logout_user()
    # return redirect(url_for('api.home'))
    return jsonify({
        'message': 'logged out successfully'
    })


# getting profile of a user
@users.route('/api/user/profile', methods=['GET'])
@cross_origin()
@login_required
def profile():
    try:
        # changing profile name
        data = request.get_json()
        if data:
            name = Users.query.filter_by(name=data['name']).first()
            if name and name != current_user:
                return jsonify({
                    "message": "This name is already used by another user",

                })
            elif current_user.name == data['name']:
                return jsonify({
                    "message": "You are currently using this name",

                })

            else:
                current_user.name = data['name']
                db.session.commit()
        # uploading photo
        try:
            profile_pics = save_img(request.files['picture'])
            current_user.profile = profile_pics
            db.session.commit()
            user_photo = str(profile_pics).partition('.')
            if user_photo[-1] == 'jpg' or user_photo[-1] == 'png':
                Cloud.uploader.upload(f"{os.path.join(os.path.abspath('Api/static/movies/'), profile_pics)}",
                                      chunk_size=6000000,
                                      public_id=current_user.name,
                                      overwrite=True,
                                      eager=[
                                          {"width": 300, "height": 300, "crop": "pad", "audio_codec": "none"},
                                          {"width": 160, "height": 100, "crop": "crop", "gravity": "south",
                                           "audio_codec": "none"}],
                                      eager_async=True,
                                      notification_url="https://mysite.example.com/notify_endpoint",
                                      resource_type="image")
                return jsonify({

                    "message": 'Uploaded'
                })
            else:

                return jsonify({

                    "message": 'Only image extensions allowed'
                })
        except:
            pass
    except:
        pass
    name = current_user.name
    email = current_user.email
    dob = current_user.dob
    friends = Friend.query.filter_by(get=current_user).filter(Friend.u_friend != 'null').all()
    total = len(friends)

    return jsonify({
        "name": name,
        'email': email,
        "dob": dob,
        # 'image' : getting cloudinary link / current user's name,
        'friends': total
    })


# uploading a story
@users.route('/api/upload/story', methods=['POST'])
@cross_origin()
@login_required
def upload_story():
    data = request.get_json()
    file = request.files['story']
    socials = Activities(social=current_user)
    try:
        # add text as a table to the database
        socials.text = data['text']
    except:
        pass
    socials.story = data['name']
    socials.story_data = file.read()
    socials.time_uploaded = datetime.datetime.now()
    db.session.add(socials)
    db.session.commit()
    return jsonify({
        'message': 'uploaded'
    })


# list of current user's story
@users.route('/api/user/story', methods=['GET'])
@cross_origin()
@login_required
def my_story():
    socials = Activities.query.filter_by(social=current_user).all()
    activities_schema = ActivitiesSchema(many=True)
    result = activities_schema.dump(socials)

    return jsonify({
        "data": result
    })


# list of current user's friend's story
@users.route('/api/friend/story', methods=['GET'])
@cross_origin()
@login_required
def friend_story():
    friends = Friend.query.filter_by(get=current_user).all()
    for friend in friends:
        socials = Activities.query.filter_by(social=friend).all()
        activities_schema = ActivitiesSchema(many=True)
        result = activities_schema.dump(socials)

        return jsonify({
            "data": result
        })


# all users
@users.route('/api/users')
def user():
    pair = Users.query.all()
    users_schema = UsersSchema(many=True)
    result = users_schema.dump(pair)
    return jsonify(result)


# all users choice
@users.route('/api/data')
def datas():
    pair = Data.query.all()
    datas_schema = DataSchema(many=True)
    result = datas_schema.dump(pair)
    return jsonify(result)


@users.route('/api/_')
def s():
    pair = Exciting.query.all()
    datas_schema = ExcitingSchema(many=True)
    result = datas_schema.dump(pair)
    return jsonify(result)


# deleting all users
@users.route('/users', methods=['DELETE'])
def delete_users():
    pair = Users.query.all()
    for i in pair:
        db.session.delete(i)
        db.session.commit()
    return jsonify({
        'msg': 'deleted'
    })
