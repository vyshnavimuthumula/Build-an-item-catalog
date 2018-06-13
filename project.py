from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Company, Article, User
# Import Login session
from flask import session as login_session
import random
import string
# imports for gconnect
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
# import login decorator
from functools import wraps
from flask import Flask, render_template
from flask import request, redirect, jsonify, url_for, flash
app = Flask(__name__)

CLIENT_ID = json.loads(open('client_secrets.json',
                            'r').read())['web']['client_id']
APPLICATION_NAME = "Build an Item Catalog"

engine = create_engine('sqlite:///watches.db')
Base.metadata.bind = engine


DBSession = sessionmaker(bind=engine)
session = DBSession()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' in login_session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
@app.route('/login')
def showlogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application-json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # upgrade the authorization code in credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps('Failed to upgrade\
                                            the authorization code'), 401)
        response.headers['Content-Type'] = 'application-json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1].decode("utf-8"))
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response
    # Access token within the app
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user\
                                            is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.

    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id
    response = make_response(json.dumps('Succesfully connected'), 200)

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # See if user exists or if it doesn't make a new one
    print('User email is' + str(login_session['email']))
    user_id = getUserID(login_session['email'])
    if user_id:
        print('Existing user#' + str(user_id) + 'matches this email')
    else:
        user_id = createUser(login_session)
        print('New user_id#' + str(user_id) + 'created')
        login_session['user_id'] = user_id
        print('Login session is tied to :id#' + str(login_session['user_id']))

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 200px; height: 200px;border-radius:100px;- \
      webkit-border-radius:100px;-moz-border-radius: 100px;">'
    flash("you are now logged in as %s" % login_session['username'])
    print("done!")
    return output

# Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).first()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).first()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).first()
        return user.id
    except:
        return None


# DISCONNECT - Revoke a current user's token and reset their login_session.
@app.route('/gdisconnect')
def gdisconnect():
    # only disconnect a connected User
    access_token = login_session.get('access_token')
    print('In gdisconnect access token is %s', access_token)
    print('User name is: ')
    print(login_session['username'])
    if access_token is None:
        print('Access Token is None')
        response = make_response(json.dumps('Current user not connected'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.c\
           om/o/oauth2/revoke?token = %s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print('result is')
    print(result)
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke\
                                            token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/logout')
def logout():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
            del login_session['username']
            del login_session['email']
            del login_session['picture']
            del login_session['user_id']
            del login_session['provider']
            flash("You have succesfully been logout")
            return redirect(url_for('showCompanies'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showCompanies'))


@app.route('/comapny/<int:company_id>/article/JSON')
def companyArticleJSON(brand_id):
    company = session.query(Company).filter_by(id=company_id).one()
    details = session.query(Article).filter_by(
        company_id=company_id).all()
    return jsonify(Article=[i.serialize for i in details])


@app.route('/company/<int:company_id>/details/<int:details_id>/JSON')
def articlesJSON(company_id, details_id):
    Article_Details = session.query(Article).filter_by(id=details_id).one()
    return jsonify(Article_Details=Article_Details.serialize)


@app.route('/company/JSON')
def companiesJSON():
    companies = session.query(Company).all()
    return jsonify(companies=[r.serialize for r in companies])
# Show all companies


@app.route('/')
@app.route('/company/')
def showCompanies():
    session1 = DBSession()
    companies = session1.query(Company).all()
    # return "This page will show all my brands"
    session1.close()
    return render_template('companies.html', companies=companies)


# Create a new brand
@app.route('/company/new/', methods=['GET', 'POST'])
def newCompany():
    session2 = DBSession()
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newCompany = Company(name=request.form['name'])
        session2.add(newCompany)
        session2.commit()
        session2.close()
        return redirect(url_for('showCompanies'))
    else:
        session2.close()
        return render_template('newCompany.html')
    # return "This page will be for making a new brand"

# Edit a brand


@app.route('/company/<int:company_id>/edit/', methods=['GET', 'POST'])
def editCompany(company_id):
    session3 = DBSession()
    editCompany = session3.query(Company).filter_by(id=company_id).one()
    if 'username' not in login_session:
        return redirect('/login')
        if editCompany.user_id == login_session['user_id']:
            if company.user_id != login_session['user_id']:
                return "<script>function myFunction() {alert('You \
            are not authorized to edit this Company.\
            Please create your own entry in order \
            to edit/delete.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        if request.form['name']:
            print(editCompany.name)
            editCompany.name = request.form['name']
            session3.add(editCompany)
            session3.commit()
            session3.close()
            return redirect(url_for('showCompanies', company_id=company_id))
    else:
        session3.close()
        return render_template(
            'editCompany.html', company_id=company_id, company=editCompany)

    # return 'This page will be for editing company %s' % company_id

# Delete a company


@app.route('/company/<int:company_id>/delete/', methods=['GET', 'POST'])
def deleteCompany(company_id):
    session4 = DBSession()
    deleteCompany = session4.query(
        Company).filter_by(id=company_id).one()
    if 'username' not in login_session:
        return redirect('/login')
        if deleteCompany.user_id == login_session['user_id']:
            if deleteCompany.user_id != login_session['user_id']:
                return "<script>function myFunction() {alert('You \
                are not authorized to delete this Company.\
                Please create your own entry in order \
                to edit/delete.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        session4.delete(deleteCompany)
        session4.commit()
        session4.close()
        return redirect(
            url_for('showCompanies', company_id=company_id))
    else:
        session4.close()
        return render_template(
            'deleteCompany.html', company_id=company_id, company=deleteCompany)


# Show a brand product
@app.route('/company/<int:company_id>/')
@app.route('/company/<int:company_id>/article/')
def showArticle(company_id):
    session5 = DBSession()
    company = session5.query(Company).filter_by(id=company_id).one()
    details = session5.query(Article).filter_by(company_id=company_id).all()
    session5.close()
    return render_template('article.html', details=details, company=company)
    # return 'This page is the product for brand %s' % brand_id

# Create a new product details


@app.route(
    '/company/<int:company_id>/company/new/', methods=['GET', 'POST'])
def newArticle(company_id):
    session6 = DBSession()
    company = session6.query(Company).filter_by(id=company_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newCompany = Article(
            name=request.form['name'],
            description=request.form['description'],
            price=request.form['price'],
            type=request.form['type'],
            company_id=company_id,
            user_id=company.user_id)

        session6.add(newCompany)
        session6.commit()
        session6.close()

        return redirect(url_for('showArticle', company_id=company_id))
    else:
        return render_template('newArticle.html', company_id=company_id)

    return render_template('newArticle.html')
    # return 'This page is for making a new product details for company %s'

# Edit a article details


@app.route('/company/<int:company_id>/article/<int:article_id>/edit',
           methods=['GET', 'POST'])
def editArticle(company_id, article_id):
    session7 = DBSession()
    if 'username' not in login_session:
        return redirect('/login')
    editArticle = session7.query(Article).filter_by(id=article_id).one()
    company = session7.query(Company).filter_by(id=company_id).one()
    if login_session['user_id'] == company.user_id:
        if company.user_id != login_session['user_id']:
            return "<script>function myFunction() {alert('You \
            are not authorized to edit this Company.\
            Please create your own entry in order \
            to edit/delete.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        if request.form['name']:
            editArticle.name = request.form['name']
        if request.form['description']:
            editArticle.description = request.form['name']
        if request.form['price']:
            editArticle.price = request.form['price']
        if request.form['type']:
            editArticle.type = request.form['type']
        session7.add(editArticle)
        session7.commit()
        session7.close()
        return redirect(url_for('showArticle', company_id=company_id))
    else:
        return render_template('editArticle.html', company_id=company_id,
                               article_id=article_id, details=editArticle)

    # return 'This page is for editing product details %s' % product_id

# Delete a article details


@app.route('/company/<int:company_id>/article/<int:article_id>/delete',
           methods=['GET', 'POST'])
def deleteArticle(company_id, article_id):
    session8 = DBSession()
    if 'username' not in login_session:
        return redirect('/login')
    company = session8.query(Company).filter_by(id=company_id).one()
    deleteArticle = session8.query(Article).filter_by(id=article_id).one()
    if login_session['user_id'] == company.user_id:
        if company.user_id != login_session['user_id']:
            return "<script>function myFunction() {alert('You \
            are not authorized to delete this Company.\
            Please create your own entry in order \
            to edit/delete.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        session8.delete(deleteArticle)
        session8.commit()
        session8.close()
        return redirect(url_for('showArticle', company_id=company_id))
    else:
        return render_template('deleteArticle.html', company_id=company_id,
                               article_id=article_id, details=deleteArticle)
    # return "This page is for deleting article details %s" % article_id


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
