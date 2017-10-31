######################################
# author ben lawson <balawson@bu.edu> 
# Edited by: Baichuan Zhou (baichuan@bu.edu) and Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from 
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
####################################################
import ast

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
    cursor.execute("SELECT user_id FROM Users WHERE email = '{0}'".format(email))
    if int(cursor.fetchone()[0])!=1: # if it equals 1, someone is trying to log in using the guest account created to allow unregistered users to comment
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
        mandatory = [email,password,first_name,last_name,dob]
        if '' in mandatory:
            raise Exception("empty field")
        hometown = request.form.get('hometown')
        gender = request.form.get('gender')
        last_name = last_name.replace("'", "''")
        first_name = first_name.replace("'", "''")
        emailmod = email.replace("'", "''")
        hometown = hometown.replace("'", "''")
    except:
        print(
            "couldn't find all tokens")
        return flask.redirect(flask.url_for('register'))
    cursor = conn.cursor()

    test = isEmailUnique(email)
    if test:
        if hometown =='':
            hometown = 'NULL'
        if gender == None:
            gender = 'NULL'
        cursor.execute("INSERT INTO Users (email, password,first_name,last_name,dob, hometown,gender) VALUES "
                       "('{0}', '{1}','{2}','{3}','{4}','{5}','{6}')".format(email, password,first_name,last_name,dob,hometown,gender))
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
    url = request.form.get("current_url")
    if request.method == 'POST':
        uid = getUserIdFromEmail(flask_login.current_user.id)
        imgfile = request.files['photo']
        filename = "static/uploads/"+imgfile.filename
        imgfile.save(filename)
        caption = request.form.get('caption')
        aid = request.form.get('album_id')
        photo_path = filename.replace(" ","%20") #this is to avoid 404 errors on pictures with spaces in their filenames
        tagString = request.form.get('tag')
        tagString = tagString.replace("'","''")
        cursor.execute("INSERT INTO Pictures (imgpath, user_id, caption, album_id) VALUES (%s, %s, %s, %s)", (photo_path, uid, caption,aid))
        conn.commit()
        cursor.execute("SELECT picture_id FROM Pictures ORDER BY picture_id DESC LIMIT 1;")
        pid = cursor.fetchall()[0][0]
        tagAPhoto(tagString, pid)
    return redirect(url)

#uploading functions
def tagAPhoto(tagString,pid):
    tags = tagString.split('#')
    tags = [tag for tag in tags if tag!='']
    for word in tags:
        word = word.replace(' ','')
        cursor = conn.cursor()
        cursor.execute("SELECT word FROM Tag WHERE word = '{0}'".format(word))
        results = cursor.fetchall()
        if len(results)==0:
            cursor.execute("INSERT INTO Tag (word) VALUES ('{0}')".format(word))
            conn.commit()
        cursor.execute("INSERT INTO associated_with (word, picture_id) VALUES ('{0}', '{1}')".format(word, pid))
        conn.commit()
    return

# end photo uploading code


#begin user specific album and photo code
@app.route('/albums')
@flask_login.login_required
def albums():
    usersalbums = getUsersAlbums()
    return render_template('album.html',albumList= usersalbums)

@app.route('/addAlbum', methods=['GET', 'POST'])
def addAlbum():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    name = request.form.get('name')
    name = name.replace("'","''")
    if name!='':
        createAlbum(name,uid)
    usersAlbums = getUsersAlbums()
    return render_template('album.html', albumList = list(usersAlbums))

@app.route('/viewAlbum', methods=['GET', 'POST'])
def pictures():
    aid = request.args.get('album_id')
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cursor = conn.cursor()
    cursor.execute("SELECT name, user_id FROM Album WHERE album_id = '{0}'".format(aid))
    results = cursor.fetchall()
    albumName = results[0][0]
    auid = results[0][1]
    userMode = (auid==uid)
    cursor.execute("SELECT p.imgpath, p.picture_id, p.album_id, p.caption, p.user_id, u.first_name, u.last_name FROM Pictures as p natural join users as u "
                   "WHERE user_id = '{0}' AND album_id = '{1}'".format(auid,aid))
    pictures = formatPictureType(list(cursor.fetchall()))
    print(pictures)
    return render_template('pictures.html', name = albumName, album_id = aid , photos = pictures, displayAll = userMode)

@app.route('/delete_album', methods=['GET','POST'])
def delete_album():
    aid = request.form.get("album_id")
    deleteAlbum(aid)
    return redirect(url_for("albums"))

#album functions
def getUsersAlbums():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute("SELECT * FROM Album WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall()
def createAlbum(name,uid):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Album (name, user_id,date_of_creation) VALUES ('{0}','{1}',NOW())".format(name,uid))
    conn.commit()
def deleteAlbum(aid):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Album WHERE album_id = '{0}'".format(aid))
    conn.commit()

#photo functions
@app.route('/delete', methods=['GET','POST'])
def delete():
    pid = request.form.get("photo_id")
    uid = getUserIdFromEmail(flask_login.current_user.id)
    puid = request.form.get("user_id")
    aid = request.form.get("album_id")
    url = request.form.get("current_url")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM Album WHERE album_id = '{0}'".format(aid))
    if int(uid) == int(puid):
        delete_file(pid)
    return redirect(url)
def formatPictureType(pictures):
    for i in range(len(pictures)):
        pic = pictures[i]
        pid = pic[1]
        path = pic[0]
        caption = pic[3]
        aidi= pic[2]
        uidi= pic[4]
        ufirst = pic[5]
        ulast = pic[6]
        uname = str(ufirst)+" "+str(ulast)
        cursor.execute("SELECT word FROM associated_with WHERE picture_id = '{0}'".format(pid))
        tags = list(cursor.fetchall())
        temptags = [tag[0] for tag in tags]
        tags = temptags
        cursor.execute("SELECT U.first_name, U.last_name FROM Users AS U, Likes as L WHERE L.picture_id = '{0}' AND "
                       "U.user_id = L.user_id".format(pid))
        likes = list(cursor.fetchall())
        templikes = [str(like[0])+' '+str(like[1]) for like in likes]
        likes = templikes
        tempphoto = (path, pid, aidi, caption, tags, likes,uidi,uname)
        pictures[i] = tempphoto
    return pictures

def delete_file(pid):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Pictures WHERE picture_id = '{0}'".format(pid))
    conn.commit()

def getAllPhotos(uid = 1):
    cursor = conn.cursor()
    if uid ==1:
        cursor.execute("SELECT P.imgpath, P.picture_id, P.album_id, P.caption, P.user_id, u.first_name, u.last_name FROM Pictures AS P natural join users as u")
    else:
        cursor.execute("SELECT P.imgpath, P.picture_id, P.album_id, P.caption, P.user_id, u.first_name, u.last_name FROM Pictures AS P natural join users as u WHERE P.user_id = '{0}'".format(uid))
    return cursor.fetchall()

@app.route('/alsoLike', methods=['GET','POST'])
@flask_login.login_required
def alsoLike():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cursor = conn.cursor()
    cursor.execute("select g.imgpath, g.picture_id, g.album_id, g.caption, g.user_id, u.first_name, u.last_name from "
                   "(select p.*, a.word from (pictures as p natural join associated_with as a)) as g natural join "
                   "(select picture_id, word as tag from associated_with) as a2 natural join users as u natural join "
                   "(select a.word from associated_with as a, pictures as p where p.picture_id = a.picture_id And "
                   "p.user_id = 3 group by a.word order by count(a.picture_id) DESC limit 5) as f where g.user_id <> 3 "
                   "group by g.picture_id order by count(distinct f.word) DESC, count(distinct a2.tag) ASC;".format(uid))
    pictures = formatPictureType(list(cursor.fetchall()))
    return render_template('alsoLike.html', photos = pictures)
#end user album and photo code


#begin browsing, searching, and tags code
@app.route('/topTags', methods=['GET','POST'])
def topTags():
    tags = list(mostPopularTags())
    tagsFull = []
    if len(tags)>0:
        tagsFull = [(i+1,tags[i][0],tags[i][1]) for i in range(len(tags))]
    return render_template('topTags.html', topTags = tagsFull)

@app.route('/search/<tags>/<users>', methods=['GET','POST'])
def search(tags,users):
    searchTags = ast.literal_eval(tags)
    try:
        uid = getUserIdFromEmail(flask_login.current_user.id)
    except:
        uid = 1

    if len(searchTags) != 0:
        photos = photoSearch(searchTags,users)
    else:

        if users == 'all':
            photos = getAllPhotos()
        else:
            photos = getAllPhotos(uid)
    pictures = formatPictureType(list(photos))
    return render_template('browse.html', photos=pictures)

@app.route('/browse', methods=['GET','POST'])
def browse():
    photos = getAllPhotos()
    if flask.request.method == "POST":
        searchTerm = request.form.get('searchText')
        who = request.form.get('users')
        if who==None:
            who = 'all'
        tags = searchTerm.split('#')
        tags = [tag for tag in tags if tag!='']
        if len(tags) != 0:
            tags = [tag.replace(' ','') for tag in tags]
            string = '/search?tag1='+tags[0]
            for i in range(1,len(tags)):
                string+='tag'+str(i+1)+'='+str(tags[i])
        return flask.redirect(url_for('search', tags = tags, users = who))
    else:
        tag = request.args.get('TAG')
        if tag!=None:
            photos = photoSearch([tag])
    pictures = formatPictureType(list(photos))
    return render_template('browse.html', photos=pictures)

#tags and photo searching functions
def photoSearch(words,users = 'all'):

    results =[]
    finalOutput = []
    for word in words:
        cursor = conn.cursor()
        cursor.execute("SELECT P.imgpath, P.picture_id, P.album_id, P.caption, P.user_id, u.first_name, u.last_name FROM Pictures AS P natural join users as u, associated_with "
                       "AS A WHERE A.word = '{0}' AND A.picture_id = P.picture_id".format(word))
        temp = list(cursor.fetchall())
        results += [temp]
    for photo in results[0]:
        if inAllLists(photo,results):
            finalOutput+=[photo]
    if users =='you':
        uid = getUserIdFromEmail(flask_login.current_user.id)
        if uid!=1:
            temp = [photo for photo in finalOutput if int(photo[4]) == uid]
            finalOutput = temp
        else:
            finalOutput = []
    return finalOutput

def inAllLists(element,lists):
    for list in lists:
        if element not in list:
            return False
    return True

def mostPopularTags():
    cursor = conn.cursor()
    cursor.execute("SELECT word, COUNT(picture_id) FROM associated_with GROUP BY word ORDER BY COUNT(picture_id) DESC LIMIT 10")
    return cursor.fetchall()

#end tags code


#like code
@app.route('/like', methods=['GET','POST'])
@flask_login.login_required
def like():
    pid = request.form.get("photo_id")
    uid = getUserIdFromEmail(flask_login.current_user.id)
    url = request.form.get("current_url")

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Likes WHERE user_id = '{0}' AND picture_id = '{1}'".format(uid,pid))
    results = cursor.fetchall()
    puid = request.form.get("user_id")
    if(len(results)==0 and int(puid)!=int(uid)): #if this user has not liked this picture already and it is not their picture
        cursor.execute("INSERT INTO Likes (user_id, picture_id) VALUES ('{0}','{1}')".format(uid,pid))
        conn.commit()
    return redirect(url)

#end like code

#begin friends code

@app.route('/friends', methods = ['GET','POST'])
@flask_login.login_required
def friends():
    usersfriends = listAllFriends()
    if request.method == 'POST':
        name = request.form.get('name')
        if name != '':
            return redirect(url_for('findfriends',search = name))
    return render_template('friends.html',userFriends= usersfriends)

@app.route('/findfriends/<search>', methods=['GET', 'POST'])
@flask_login.login_required
def findfriends(search):
    uid = getUserIdFromEmail(flask_login.current_user.id)
    name = search

    names = name.split()
    cursor = conn.cursor()
    if len(names) == 1:
        cursor.execute(
            "SELECT first_name,last_name, email, user_id FROM Users WHERE (last_name LIKE '{0}' OR first_name LIKE '{0}') "
            "AND user_id <> 1".format(
                names[0]))
        A = list(cursor.fetchall())
        friendsList = A
    else:
        if len(names) == 2:
            cursor.execute(
                "SELECT first_name,last_name, email, user_id FROM Users WHERE ((last_name LIKE '{0}' and first_name LIKE"
                " '{1}') OR (first_name LIKE '{0}' and last_name LIKE '{1}')) AND user_id <> 1".format(
                    names[0], names[1]))
            A = cursor.fetchall()
            friendsList = A
        else:
            friendsList = []
    usersfriends = listAllFriends()
    return render_template('friends.html',friends=set(friendsList),userFriends = usersfriends)

@app.route('/addfriends', methods=['GET', 'POST'])
def addFriend():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    fid = request.form.get('uid')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Friends WHERE user_id1 = '{0}' AND user_id2 = '{1}'".format(uid,fid))
    results = cursor.fetchall()
    if (len(results)==0 and (int(uid)!=int(fid))): #if this friendship does not already exist, and the user isnt trying to friend themselves
        cursor.execute("INSERT INTO Friends (user_id1, user_id2, since) VALUES ('{0}','{1}',NOW())".format(uid,fid))
        conn.commit()
    usersfriends = listAllFriends()
    return render_template('friends.html', userFriends=usersfriends)

@app.route('/recommendFriends', methods=['GET', 'POST'])
def recFriends():
    uid = getUserIdFromEmail(flask_login.current_user.id)

    cursor.execute("SELECT U.first_name,U.last_name, U.email, U.user_id FROM Users AS U, Friends AS F1 INNER JOIN "
                   "Friends AS F2 ON F1.user_id2=F2.user_id1 WHERE U.user_id=F2.user_id2 AND NOT EXISTS "
                   "(SELECT * FROM Friends AS F3 WHERE F3.user_id2 = F2.user_id2 AND F3.user_id1='{0}')".format(uid))
    recFriends = list(cursor.fetchall())
    message = None
    if len(recFriends)==0:
        message = 'No friends to recommend'
    return render_template('recommendFriends.html',recFriends=recFriends, message = message)

#friends functions
def listAllFriends():
    cursor = conn.cursor()
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cursor.execute(
        "SELECT U.first_name,U.last_name,U.email, U.user_id FROM Users AS U, Friends AS F WHERE U.user_id = F.user_id2 AND F.user_id1 = '{0}'".format(
            uid))
    usersfriends = cursor.fetchall()
    return usersfriends

@app.route('/topUsers', methods=['GET', 'POST'])
def topTenUsers():
    cursor = conn.cursor()
    cursor.execute("select u.first_name, u.last_name,u.user_id "
                   "from users as u,(select user_id from comment union all select user_id from pictures) as w "
                   "where u.user_id = w.user_id and w.user_id <> 1 group by u.user_id order by count(w.user_id) desc limit 10")
    users = list(cursor.fetchall())
    names = [str(first)+' '+str(last) for (first,last, id) in users]
    return render_template('topUsers.html',topUsers = names)
# end friends code


# begin comments code
@app.route('/comment', methods=['GET','POST'])
def comment():
    user_comments=[]
    photo_id=request.args.get('photo_id')
    message = ''
    cursor=conn.cursor()
    try:
        uid =getUserIdFromEmail(flask_login.current_user.id)
    except:
        uid = 1

    cursor.execute("SELECT C.text, U.first_name, U.last_name FROM comment as C, Users as U WHERE picture_id='{0}' AND C.user_id = U.user_id ORDER BY C.date_left".format(photo_id))
    comments = cursor.fetchall()
    for c_row in comments:
        temp_comment = c_row
        user_comments.append(temp_comment)
    cursor.execute("Select p.imgpath, p.user_id, p.picture_id, u.first_name, u.last_name from pictures as p natural join users as u where picture_id = '{0}'".format(photo_id))
    photo = cursor.fetchone()
    temp = (photo[0],photo[1],photo[2], str(photo[3])+" "+str(photo[4]))
    photo = temp
    return render_template('comments.html', message = message, picture_id = photo_id, picture = photo, user_id = uid, comments = user_comments)

@app.route('/postComment', methods=['POST','GET'])
def postComment():
    url = request.form.get("current_url")
    if request.method == 'POST':
        photo_id = request.form.get('picture_id')
        cursor.execute("SELECT user_id FROM pictures WHERE picture_id='{0}'".format(photo_id))
        pic_temp = cursor.fetchall()
        puid = pic_temp[0]
        try:
            uid = getUserIdFromEmail(flask_login.current_user.id)
            cursor.execute("SELECT first_name, last_name FROM users WHERE user_id='{0}'".format(uid))
        except:
            uid = 1
        if(uid == 1 or puid!=uid):
            comment = request.form.get('comment')
            comment = comment.replace("'","''")
            createComment(comment,uid,photo_id)
            message = ""
            return redirect(url)
        else:
            message = "You Cannot Post a Comment on Your Own Picture"

@app.route('/searchOnComments', methods=['GET', 'POST'])
def commentsSearch():
    results = []
    if request.method == 'POST':
        searchText = request.form.get('searchText')
        results = searchOnComments(searchText)
    return render_template('searchOnComments.html', commentors = results)

#comment functions
def createComment(comment,uid,pid):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Comment (date_left, text, user_id, picture_id) VALUES (NOW(), '{0}','{1}','{2}')".format(comment, uid, pid))
    conn.commit()

def searchOnComments(searchString):
    cursor = conn.cursor()
    cursor.execute("SELECT U.first_name, U.last_name, COUNT(C.comment_id) FROM Comment AS C, Users AS U "
                   "WHERE C.text LIKE '%{0}%' AND C.user_id = U.user_id GROUP BY C.user_id ORDER BY COUNT(C.comment_id) DESC".format(searchString))
    results = list(cursor.fetchall())
    return results

#end comments code


# default page
@app.route("/", methods=['GET'])
def hello():
    return render_template('hello.html', message='Welecome to Photoshare')


if __name__ == "__main__":
    # this is invoked when in the shell  you run
    # $ python app.py
    app.run(port=5000, debug=True)
