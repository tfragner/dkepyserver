from datetime import datetime
from flask import render_template, flash, redirect, url_for, request,  \
    make_response, jsonify
from werkzeug.urls import url_parse
from flask_login import login_user, current_user, logout_user, login_required
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, \
    SparqlForm, AddParameterForm
from app.models import User, Sparql, Parameter
from SPARQLWrapper import SPARQLWrapper, JSON
from config import Config


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = SparqlForm()
    if form.validate_on_submit():
        query = Sparql(description=form.description.data, sparql_url=form.sparql_url.data, sparqlquery=form.sparqlquery.data, pythonscript=form.pythonscript.data, author=current_user)
        db.session.add(query)
        db.session.commit()
        flash('Your Query is now live!')
        return redirect(url_for('index'))
    page = request.args.get('page', 1, type=int)
    queries = current_user.followed_queries().paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('index', page=queries.next_num) \
        if queries.has_next else None
    prev_url = url_for('index', page=queries.prev_num)\
        if queries.has_prev else None
    return render_template('index.html', title='Home', form=form, queries=queries.items, next_url=next_url, prev_url=prev_url)


@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    queries = Sparql.query.order_by(Sparql.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('explore', page=queries.next_num) \
        if queries.has_next else None
    prev_url = url_for('explore', page=queries.prev_num)\
        if queries.has_prev else None
    return render_template('index.html', title='Explore', queries=queries.items, next_url=next_url, prev_url=prev_url)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template("login.html", title="Sign In", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title="Register", form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    queries = user.queries.order_by(Sparql.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('user', username=user.username, page=queries.next_num) \
        if queries.has_next else None
    prev_url = url_for('user', username=user.username, page=queries.prev_num)\
        if queries.has_prev else None
    return render_template('user.html', user=user, queries=queries.items, next_url=next_url, prev_url=prev_url)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('You changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile', form=form)


@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} nit found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot follow yourself!')
        return redirect(url_for('user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('You are now following {}'.format(username))
    return redirect(url_for('user', username=username))


@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot unfollow yourself!')
        return redirect(url_for('user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('You are not following {}'.format(username))
    return redirect(url_for('user', username=username))


@app.route('/deletequery/<id>')
@login_required
def deletequery(id):
    query = Sparql.query.filter_by(id=id).first()
    if query is None:
        flash('Query {} not found.'.format(id))
        return redirect(url_for('index'))
    db.session.delete(query)
    db.session.commit()
    flash('You deleted Query {}'.format(id))
    return redirect(url_for('index'))


@app.route('/addparameter/<id>', methods=['GET', 'POST'])
@login_required
def addparameter(id):
    form = AddParameterForm()
    if form.validate_on_submit():
        query = Sparql.query.get(id)
        param = Parameter(name=form.name.data, description=form.description.data, pythonscript=form.pythonscript.data, belongsTo=query)
        db.session.add(param)
        db.session.commit()
        flash('Your Parameter is now live!')
        return redirect(url_for('index'))
    return render_template('addparameter.html', title='Add Parameter', form=form)


@app.route('/webhook/', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)
    try:
        action = req.get('queryResult').get('action')
    except AttributeError:
        return 'json error'

    query = Sparql.query.filter_by(description=action).first()

    if query is None:
        log.error('Unexpected action.')

    # sparql = SPARQLWrapper(Config.SPARQLSERVER)
    sparql = SPARQLWrapper(query.sparql_url)

    querystring = query.sparqlquery
    params = query.parameters

    for p in params:
        f = make_fun(p.pythonscript)
        querystring = f(querystring, p.name, req['queryResult']['parameters'])

    print(querystring)

    sparql.setQuery(querystring)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    print(results)

    f = make_fun(query.pythonscript)

    lst = f(results)
    print(jsonify({'fulfillmentText': 'test',
                                  "fulfillmentMessages": [{'payload': {'dkepr': lst}}]}))

    return make_response(jsonify({'fulfillmentText': 'test',
                                  "fulfillmentMessages": [{'payload': {'dkepr': lst}}]}))


def make_fun(scripttext):
    exec(scripttext)
    return locals()['f']
