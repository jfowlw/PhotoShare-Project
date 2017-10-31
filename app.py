######################################
# author ben lawson <balawson@bu.edu> 
# Edited by: Baichuan Zhou (baichuan@bu.edu) and Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from 
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login as flask_login

# for image uploading
# from werkzeug import secure_filename
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

# These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'password'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

# begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email FROM Users")
users = cursor.fetchall()


def getUserList():
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM Users")
    return cursor.fetchall()


class User(flask_login.UserMixin):
    pass


@login_manager.user_loader
def user_loader(email):
    users = getUserList()
    if not (email) or email not in str(users):
        return
    user = User()
    user.id = email
    return user


@login_manager.request_loader
def request_loader(request):
    users = getUserList()
    email = request.form.get('email')
    if not (email) or email not in str(users):
        return
    user = User()
    user.id = email
    cursor = mysql.connect().cursor()
    cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
    data = cursor.fetchall()
    pwd = str(data[0][0])
    user.is_authenticated = request.form['password'] == pwd
    return user


'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''


@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'GET':
        return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
    # The request method is POST (page is recieving data)
    email = flask.request.form['email']
    cursor = conn.cursor()
    # check if email is registered
    if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
        data = cursor.fetchall()
        pwd = str(data[0][0])
        if flask.request.form['password'] == pwd:
            user = User()
            user.id = email
            flask_login.login_user(user)  # okay login in user
            return flask.redirect(flask.url_for('protected'))  # protected is a function defined in this file

    # information did not match
    return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"


@app.route('/logout')
def logout():
    flask_login.logout_user()
    return render_template('hello.html', message='Logged out')


@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('unauth.html')


# you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
    return render_template('register.html', supress='True')


@app.route("/register", methods=['POST'])
def register_user():
    try:
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first name')
        last_name = request.form.get('last name')
        dob = request.form.get('dob')
    except:
        print(
            "couldn't find all tokens")  # this prints to shell, end users will not see this (all print statements go to shell)
        return flask.redirect(flask.url_for('register'))
    cursor = conn.cursor()
    test = isEmailUnique(email)
    if test:
        print(cursor.execute("INSERT INTO Users (email, password,first_name,last_name,dob) VALUES ('{0}', '{1}','{2}','{3}','{4}')".format(email, password,first_name,last_name,dob)))
        #print(cursor.execute("INSERT INTO Users (email, password, first_name, last_name,dob) VALUES ('{0}', '{1}')".format(email, password)))
        conn.commit()
        # log user in
        user = User()
        user.id = email
        flask_login.login_user(user)
        return render_template('hello.html', name=email, message='Account Created!')
    else:
        print("email already exists")
        return flask.redirect(flask.url_for('register',supress=False))


def getUsersPhotos(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT imgpath, picture_id, caption FROM Pictures WHERE user_id = '{0}'".format(uid))
    return cursor.fetchall()  # NOTE list of tuples, [(imgpath, pid), ...]

def getUserIdFromEmail(email):
    cursor = conn.cursor()
    cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
    return cursor.fetchone()[0]


def isEmailUnique(email):
    # use this to check if a email has already been registered
    cursor = conn.cursor()
    if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
        # this means there are greater than zero entries with that email
        return False
    else:
        return True


# end login code

@app.route('/profile')
@flask_login.login_required
def protected():
    return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile")


# begin photo uploading code
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cursor = conn.cursor()
    aid = request.args.get('album_id')

    imgfile = request.files['photo']
    print(str(imgfile))
    print(imgfile.filename)
    filename = "static/uploads/"+imgfile.filename
    print(imgfile.save(filename))
    caption = request.form.get('caption')
    photo_path = filename

    cursor.execute("INSERT INTO Pictures (imgpath, user_id, caption, album_id) VALUES (%s, %s, %s, %s)", (photo_path, uid, caption, aid))
    conn.commit()
    # The method is GET so we return a  HTML form to upload the a photo.

    return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!',
                           photos=getUsersPhotos(uid))
# end photo uploading code

#### 10-15 created methods for getting albums, adding albums, and viewing pictures in an album

def getUsersAlbums():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute("SELECT * FROM Album WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall()

@app.route('/albums')
@flask_login.login_required
def albums():
    usersalbums = getUsersAlbums()
    print(str(usersalbums))
    return render_template('album.html',albumList= usersalbums)

@app.route('/addAlbum', methods=['GET', 'POST'])
def addAlbum():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    name = request.form.get('name')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Album (name, user_id, date_of_creation) VALUES ('{0}','{1}', NOW())".format( name, uid))
    conn.commit()
    usersAlbums = getUsersAlbums()
    return render_template('album.html', albumList = list(usersAlbums))

@app.route('/viewAlbum', methods=['GET', 'POST'])
def pictures():
    aid = request.args.get('album_id')
    print(aid)
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM Album WHERE album_id = '{0}'".format(aid))
    albumName = cursor.fetchall()
    cursor.execute("SELECT imgpath, picture_id, album_id, caption, user_id FROM Pictures WHERE user_id = '{0}' AND album_id = '{1}'".format(uid,aid))
    pictures = formatPictureType(list(cursor.fetchall()))

    return render_template('pictures.html', name = albumName , photos = pictures)

def formatPictureType(pictures):
    for i in range(len(pictures)):
        pic = pictures[i]
        pid = pic[1]
        path = pic[0]
        caption = pic[3]
        aidi= pic[2]
        uidi= pic[4]
        cursor.execute("SELECT word FROM associated_with WHERE picture_id = '{0}'".format(pid))
        tags = list(cursor.fetchall())
        cursor.execute("SELECT U.first_name, U.last_name FROM Users AS U, Likes as L WHERE L.picture_id = '{0}' AND U.user_id = L.user_id".format(pid))
        likes = list(cursor.fetchall())
        temp = (path, pid, aidi, caption, tags, likes,uidi)
        pictures[i] = temp
    return pictures

@app.route('/like', methods=['GET','POST'])
def like():
    pid = request.form.get("photo_id")
    aid = request.form.get("album_id")
    uid = getUserIdFromEmail(flask_login.current_user.id)

    cursor = conn.cursor()
    cursor.execute("SELECT name FROM Album WHERE album_id = '{0}'".format(aid))
    albumName = cursor.fetchall()
    cursor.execute("SELECT * FROM Likes WHERE user_id = '{0}' AND picture_id = '{1}'".format(uid,pid))
    results = cursor.fetchall()
    if(len(results)==0): #if this user has not liked this picture already
        cursor.execute("INSERT INTO Likes (user_id, picture_id) VALUES ('{0}','{1}')".format(uid,pid))
        conn.commit()
    cursor.execute(
        "SELECT imgpath, picture_id, album_id, caption, user_id FROM Pictures WHERE user_id = '{0}' AND album_id = '{1}'".format(
            uid, aid))
    pictures = formatPictureType(list(cursor.fetchall()))
    return render_template('pictures.html', name = albumName , photos = pictures, id = aid)


@app.route('/delete', methods=['GET','POST'])
def delete():
    pid = request.form.get("photo_id")
    uid = getUserIdFromEmail(flask_login.current_user.id)
    puid = request.form.get("user_id")
    aid = request.form.get("album_id")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM Album WHERE album_id = '{0}'".format(aid))
    albumName = cursor.fetchall()
    if int(uid) == int(puid):
        delete_file(pid)
    cursor.execute(
        "SELECT imgpath, picture_id, album_id, caption, user_id FROM Pictures WHERE user_id = '{0}' AND album_id = '{1}'".format(
            uid, aid))
    pictures = formatPictureType(list(cursor.fetchall()))
    return render_template('pictures.html', name=albumName, photos=pictures)
#end album code


#begin friends code
def listAllFriends():
    cursor = conn.cursor()
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cursor.execute(
        "SELECT U.first_name,U.last_name,U.email, U.user_id FROM Users AS U, Friends AS F WHERE U.user_id = F.user_id2 AND F.user_id1 = '{0}'".format(
            uid))
    usersfriends = cursor.fetchall()
    return usersfriends

@app.route('/friends')
def friends():
    usersfriends = listAllFriends()
    print(usersfriends)
    return render_template('friends.html',userFriends= usersfriends)
#changed query to have name LIKE 'searched name' instead of =
@app.route('/findfriends', methods=['GET', 'POST'])
def searchFriends():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    name = request.form.get('name')
    names = name.split()
    print(str(uid))
    print(str(names))
    cursor = conn.cursor()
    if len(names) == 1:
        cursor.execute("SELECT first_name,last_name, email, user_id FROM Users WHERE last_name LIKE '{0}'".format(names[0]))
        A = list(cursor.fetchall())
        print(A)
        cursor.execute("SELECT first_name,last_name, email, user_id FROM Users WHERE first_name LIKE '{0}'".format(names[0]))
        B = list(cursor.fetchall())
        friendsList = A+B
        print(friendsList)
    else:
        if len(names) == 2:
            cursor.execute("SELECT first_name,last_name, email, user_id FROM Users WHERE last_name LIKE '{0}' and first_name LIKE '{1}'".format(names[0], names[1]))
            A = cursor.fetchall()
            cursor.execute("SELECT first_name,last_name, email, user_id FROM Users WHERE first_name LIKE '{0}' and last_name LIKE '{1}'".format(names[0], names[1]))
            B = cursor.fetchall()
            friendsList= A + B
        else:
            friendsList = []
    usersfriends = listAllFriends()
    print(usersfriends)
    return render_template('friends.html',friends=friendsList,userFriends = usersfriends)

@app.route('/addfriends', methods=['GET', 'POST'])
def addFriend():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    fid = request.form.get('uid')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Friends WHERE user_id1 = '{0}' AND user_id2 = '{1}'".format(uid,fid))
    results = cursor.fetchall()
    if (len(results)==0): #if this friendship does not already exist
        cursor.execute("INSERT INTO Friends (user_id1, user_id2, since) VALUES ('{0}','{1}',NOW())".format(uid,fid))
    #cursor.execute("INSERT INTO Friends (user_id1, user_id2, since) VALUES ('{0}','{1}',NOW())".format(fid, uid)) this is if we're saying that friendships are mutual by default, not one sided
    conn.commit()
    usersfriends = listAllFriends()
    return render_template('friends.html', userFriends=usersfriends)
# end friends code

@app.route('/topUsers', methods=['GET', 'POST'])
def topTenUsers():
    cursor = conn.cursor()
    cursor.execute("select U.first_name, U.last_name from users as U, Pictures as P, Comment as C WHERE P.user_id = U.user_id "
                   "AND U.user_id = C.comment_id group by u.user_id order by count(p.picture_id)")
    users = list(cursor.fetchall())
    print(len(users))
    names = [str(first)+' '+str(last) for (first,last) in users]
    print(len(names))
    return render_template('topUsers.html',topUsers = names)



#### browsing code not yet completed
@app.route('/browse', methods=['GET', 'POST'])
def browse():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cursor = conn.cursor() # not sure what we want to display on the browsing page, but at some point we'll need all info associated with each photo
    cursor.execute("SELECT  P.picture_id, P.album_id, P.user_id, P.imgpath, P.caption, A.word, L.user_id "
                   "FROM Pictures AS P, associated_with AS A, Likes as L, Comment AS C "
                   "WHERE P.picture_id = A.picture_id AND P.picture_id = L.picture_id AND P.picture_id = C.picture_id")
    results = cursor.fetchall()
# photo viewing code


def delete_file(pid):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Pictures WHERE picture_id = '{0}'".format(pid))
    conn.commit()

def getAllPhotos():
    cursor = conn.cursor()
    cursor.execute("SELECT imgpath, picture_id, caption FROM Pictures")
    return cursor.fetchall()

def getAllPhotosByTag(tagword):
    cursor = conn.cursor()
    cursor.execute("SELECT P.imgpath, P.picture_id, P.caption FROM Pictures AS P, associated_with AS a WHERE A.word = '{0}', A.picture_id = P.picture_id".format(tagword))
    return cursor.fetchall()

def getUsersPhotosByTag(tagword, uid):
    cursor = conn.cursor()
    cursor.execute("SELECT P.imgpath, P.picture_id, P.caption FROM Pictures AS P, associated_with AS a WHERE A.word = '{0}', P.user_id = '{1}' ,A.picture_id = P.picture_id".format(tagword,uid))
    return cursor.fetchall()

def photoSearch(searchString):
    words = searchString.split()
    results =[]
    finalOutput = []
    for word in words:
        cursor = conn.cursor()
        cursor.execute("SELECT P.imgpath, P.picture_id, P.caption FROM Pictures AS P, associated_with AS a WHERE A.word = '{0}', A.picture_id = P.picture_id".format(word))
        results+=[list(cursor.fetchall())]
    for photo in results[0]:
        if inAllLists(photo,results):
            finalOutput+=photo
    return finalOutput

def inAllLists(element,lists):
    for list in lists:
        if element not in list:
            return False
    return True

def mostPopularTags():
    cursor = conn.cursor()
    cursor.execute("SELECT word, COUNT(picture_id) FROM associated_with GROUP BY word ORDER BY COUNT(picture_id) LIMIT 10")
    return cursor.fetchall()


def tagAPhoto(word,pid):
    cursor = conn.cursor()
    cursor.execute("SELECT word FROM Comment WHERE word = '{0}'".format(word))
    results = cursor.fetchall()
    if len(results)==0:
        cursor.execute("INSERT INTO Tag (word) VALUES ('{0}')".format(word))
        conn.commit()
    cursor.execute("INSERT INTO associated_with (word, picture_id) VALUES ('{0}', '{1}')".format(word, pid))
    conn.commit()


#comment code
def createComment(comment,uid,pid):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Comment (date_left, text, user_id, picture_id) VALUES (NOW(), '{0}','{1}','{2}')".format(comment, uid, pid))
    conn.commit()

def searchOnComments(searchString):
    cursor = conn.cursor()
    cursor.execute("SELECT U.first_name, U.last_name, U.user_id FROM Comment AS C, Users AS U WHERE C.text LIKE '%{0}%' "
                   "AND C.user_id = U.user_id GROUP BY C.user_id ORDER BY COUNT(C.comment_id)".format(searchString))
    results = list(cursor.fetchall())
    return results





#album code
def createAlbum(name,uid):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Album (name, user_id,date_of_creation) VALUES ('{0}','{1}',NOW())".format(name,uid))
    conn.commit()
def deleteAlbum(aid):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Album WHERE album_id = '{0}'".format(aid))
    conn.commit()



#### end new code

# default page
@app.route("/", methods=['GET'])
def hello():
    return render_template('hello.html', message='Welecome to Photoshare')


if __name__ == "__main__":
    # this is invoked when in the shell  you run
    # $ python app.py
    app.run(port=5000, debug=True)
