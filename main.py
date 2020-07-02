"""Flask RESTful API for sic_app"""

import os
import time
from flask import Flask, abort, request, jsonify, g, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
import jwt




# init app and config
app = Flask(__name__)

app.config['SECRET_KEY'] = 'the quick brown fox jumps over the lazy dog'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/final'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True

# create database, auth objects
db = SQLAlchemy(app)
auth_student = HTTPBasicAuth()
auth_teacher = HTTPBasicAuth()

class Student(db.Model):
    """student model in the database"""

    # set table name and columns
    __tablename__ = 'stulogin'
    STULOGINID = db.Column(db.Integer, primary_key=True, nullable=False)
    STDCODE = db.Column(db.String(255))
    ALTCODE = db.Column(db.String(255))
    NAME = db.Column(db.String(255))
    FNAME = db.Column(db.String(255))
    MOBILE = db.Column(db.String(15), index=True)
    PASSWORD = db.Column(db.String(255))

    def set_password(self, password):
        """set password for the student"""
        self.PASSWORD = password

    def verify_password(self, password):
        """verify password when logging in"""
        return self.PASSWORD == password

    def generate_auth_token(self, expires_in=600):
        """generate token for this session"""
        return jwt.encode(
            {'STULOGINID': self.STULOGINID, 'exp': time.time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_auth_token(token):
        # verify token when accessing a protected resource

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'],
                              algorithms=['HS256'])
        except:
            return
        return Student.query.get(data['STULOGINID'])


class Teacher(db.Model):
    """teacher model in the database"""

    # set table name and columns
    __tablename__ = 'teacher_login'
    loginid = db.Column(db.Integer, primary_key=True, nullable=False)
    EMP_ID = db.Column(db.String(15))
    EMP_NAME = db.Column(db.String(120))
    PASS = db.Column(db.String(255))
    MOBILE = db.Column(db.String(16), index=True)
    ALLOW = db.Column(db.String(2))
    NEW = db.Column(db.Integer, default=0)

    def set_password(self, password):
        """set password for this teacher"""
        self.PASS = password

    def verify_password(self, password):
        """verify password when logging in"""
        return self.PASS == password

    def generate_auth_token(self, expires_in=600):
        """generate auth token for this session"""
        return jwt.encode(
            {'loginid': self.loginid, 'exp': time.time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_auth_token(token):
        """verify auth token when accessing protected resource"""
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'],
                              algorithms=['HS256'])
        except:
            return

        return Teacher.query.get(data['loginid'])


@auth_student.verify_password
def verify_password_student(mobile_or_token, password):
    """verify access by password or token"""

    # try with token
    student = Student.verify_auth_token(mobile_or_token)

    # if auth failed
    if not student:

        # try with mobile/password
        student = Student.query.filter_by(MOBILE=mobile_or_token).first()

        # if mobile not in db or in db but password doesn't match
        if not student or not student.verify_password(password):
            return False

    # set current user if succeeded and return success
    g.user = student
    return True


@auth_teacher.verify_password
def verify_password_teacher(mobile_or_token, password):
    """verify access by password or token"""

    # try with token
    teacher = Teacher.verify_auth_token(mobile_or_token)

    # if auth failed
    if not teacher:

        # try with mobile/password
        teacher = Teacher.query.filter_by(MOBILE=mobile_or_token).first()

        # if mobile not in db or in db but password doesn't match
        if not teacher or not teacher.verify_password(password):
            return False

    # set current user if succeeded and return success
    g.user = teacher
    return True


@app.route('/api/token_student')
@auth_student.login_required
def get_auth_token_student():
    """get token for a student session"""

    token = g.user.generate_auth_token(600)
    return jsonify({'token': token.decode('ascii'), 'duration': 600})


@app.route('/api/token_teacher')
@auth_teacher.login_required
def get_auth_token_teacher():
    """get token for a teacher session"""

    token = g.user.generate_auth_token(600)
    return jsonify({'token': token.decode('ascii'), 'duration': 600})

@app.route('/api/get_sem_schedule')
@auth_teacher.login_required
def get_sem_schedule():
    """get semester schedule for teacher"""

    rows = db.engine.execute(f"SELECT * FROM sem_schedule WHERE EMP_ID =  \"{g.user.EMP_ID}\"")
    res = []
    for row in rows:
        res.append(dict(row))
    return jsonify(res)

@app.route('/api/get_stutimetable')
@auth_student.login_required
def get_timetable():
    """get timetable for student"""
# NAME,DEGREE_CODE,SEM_CODE,EMPLOYEE,SUBJECT,TIMETABLE,EXAMDATE
    rows = db.engine.execute(f"SELECT * FROM stutimetable WHERE ALTCODE = {g.user.ALTCODE}")
    res = []
    for row in rows:
        res.append(dict(row))
    return jsonify(res)

# __________________________
@app.route('/api/get_stulogin')
@auth_student.login_required
def get_stulogin():
    """get student detils for student"""

    rows = db.engine.execute(f"SELECT * FROM stulogin WHERE STULOGINID = {g.user.STULOGINID} ")
    res = []
    for row in rows:
        res.append(dict(row))
    return jsonify(res)

@app.route('/api/get_teacher')
@auth_teacher.login_required
def get_teacher():
    """get login detils for teacher"""

    rows = db.engine.execute(f"SELECT * FROM teacher_login WHERE loginid = {g.user.loginid}")
    res = []
    for row in rows:
        res.append(dict(row))
    return jsonify(res)

@app.route('/api/get_sturesult')
@auth_student.login_required
def get_stulogi():
    """get student detils for student"""

    rows = db.engine.execute(f"SELECT SEM_CODE,SUBJECT,EXAMLOC,EXAMTIME,GRADE FROM stutimetable WHERE ALTCODE = {g.user.ALTCODE} ")
    res = []
    for row in rows:
        res.append(dict(row))
    return jsonify(res)
# ____________________________

if __name__ == '__main__':
    # run the api

    app.run(debug=True)
