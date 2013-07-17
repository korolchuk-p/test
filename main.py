from flask import Flask, request, render_template, session, jsonify, make_response
from flask import send_from_directory, url_for, redirect ,Response
import json
from functools import wraps
from libs import libs
from libs import exceptions
from libs import constants
import os
import requests
import shutil


app = Flask(__name__)
app.config.from_pyfile('settings.py')


# ------------------------- DECORATORS ------------------

def template_exception(f):
    @wraps(f)
    def decorator():
        try:
            return f()
        except exceptions.NotAuthException, e:
            clear_auth()
            return redirect(url_for('login'))

    return decorator


def login_required(login=True):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if login == ('token' in session):
                return f(*args, **kwargs)
            if login:
                return redirect(url_for('login'))
            return redirect(url_for('plitka'))
           
        return decorated_function
    return decorator


# ------------------------- VIEWS ------------------

@app.route("/login", methods=["GET", "POST"])
@login_required(login=False)
@template_exception
def login():
    def post():
        response=libs.make_request(server_url='https://goods.itvik.com/api/login/', method="post", params=libs.select_keys(request.form, ['email', 'password']))
        if 'data' in response:
            session['token'] = response['data']['token']
            session['user'] = request.form['email']

            return redirect(url_for('plitka'))

        return template_page(page='login.html', error_message=response['error'] + "; Try again")
    
    return post() if request.method == 'POST' else template_page(page='login.html')


@app.route("/regist", methods=["GET", "POST"])
@login_required(login=False)
@template_exception
def regist():
    def post():
        context = libs.select_keys(request.form, ['email', 'f_name', 'l_name'])
        if request.form['password'] != request.form['password2']:
            context['error_message'] = 'fields password and password2 must be equal'
        else:
            context['password']=request.form['password']
            res = libs.make_request(server_url='https://goods.itvik.com/api/register/', method="post", params=context)
            if not 'error' in res:
                return template_page(page='message.html', message="You are registred")

            context['error_message'] = res['error']
          
        return template_page(page='regist.html', **context)

    return post() if request.method == 'POST' else template_page(page='regist.html')


@app.route("/col", methods=["GET"])
def col():
    try:
        res = libs.make_request(server_url='https://goods.itvik.com/api/collection/', method="get", params={'token':session.get('token')})
        if not 'error' in res:
            response={'total': str(len(res['data']['collections']))}
            response['rows'] = res['data']['collections']
        else:
            response=''

    except exceptions.NotAuthException, e:
        session.pop('token')
        response={'rows':[{'id':'error', 'name':'not authenticated'}]}

    return json.dumps(response)


@app.route("/logout", methods=["GET", "POST"])
@login_required()
@template_exception
def logout():
    if 'token' in session:
        libs.logout_by_token(session['token'])
        clear_auth()

    return  redirect(url_for('index'))


@app.route('/plitka', methods=["GET"])
@login_required()
@template_exception
def plitka():
    col_with_images=[]

    collection_res = libs.make_request(server_url='https://goods.itvik.com/api/collection/', method="get", params={'token':session.get('token')})
    if 'error' in collection_res:
        return col_with_images

    static_collection_image = url_for('static', filename='css/images/no_images.jpg')
    for x in collection_res.get('data', {}).get('collections', []):
        collection_id, collection_name = x.get('id'), x.get('name')

        image_res = libs.make_request(server_url='https://goods.itvik.com/api/image/', method="get", 
                                      params={'token':session.get('token'), 'object_id':collection_id, 'object_name': 'collection', 'is_default': True})

        images = image_res.get('data', {}).get('images', [])
        collection_image = images[0].get('path') if images else None
        collection_image = app.config['STATIC_IMAGE_LOCATION'] + collection_image if collection_image else static_collection_image

        col_with_images.append({'id': collection_id, 'image_url':collection_image, 'collection_name':collection_name})

    return template_page(page='plitka.html', items=col_with_images)


@app.route('/grid', methods=["GET"])
@login_required()
@template_exception
def grid():
    return template_page(page='grid.html')


@app.route('/')
@login_required()
@template_exception
def index():
    return redirect(url_for('plitka'))


@app.route('/favicon.ico')
def favicon():
    return app.send_static_file("favicon.ico")



# ------------------------- FUNCTIONS ------------------

def clear_auth():
    if 'token' in session:
        session.pop('token')

    if 'user' in session:
        session.pop('user')


def template_page(page="", **kwargs):
    return render_template(page, user=session.get('user'), **kwargs)


@app.route("/save_grid_changes", methods=["GET", "POST"])
def save_grid_changes():
    oper = request.form.get('oper')
    if oper not in ('add','edit','del'):
        return "1"

    params = {'token': session.get('token')}
    if oper in ('add','edit'):
        params['name'] = request.form.get('name')
    if oper in ('del','edit'):
        params['id'] = request.form.get('id')

    server_url = 'https://goods.itvik.com/api%s/collection/' % ('/delete' if oper == 'del' else '')
    d = {'server_url': server_url,
         'method': 'post', 
         'params': params}
    try:
        res = libs.make_request(**d)
    except exceptions.NotAuthException, e:
        clear_auth()
        return "1"

    return "0"


@app.route('/delete_collection', methods=["POST"])
def delete_collection():
    try:
        res = libs.make_request(server_url='https://goods.itvik.com/api/delete/collection/', method="post",
                                params={'token': session.get('token'), 'id': request.form.get('id')})

    except exceptions.NotAuthException, e:
        clear_auth()
        res = {'error':""}
        
    return json.dumps(res)

# ------------------------- OTHER ------------------

 



@app.route("/stest", methods=["GET", "POST"])
@template_exception
def test1():
    print libs.make_request(server_url='https://goods.itvik.com/api/logout/', method="post", params={'token':session.get('token')})
    #raise exceptions.ContAdmException('error')
    return "1" #redirect(url_for('testsave', request=r))


@app.route("/mtest", methods=["GET", "POST"])
@template_exception
def test2():
    #print libs.make_request(server_url='https://goods.itvik.com/api/logout/', method="post", params={'token':session.get('token')})
    #raise exceptions.ContAdmException('error')
    return template_page(page='message.html', message="ololo") #redirect(url_for('testsave', request=r))




@app.route('/add_collection', methods=["GET", "POST"])
@login_required()
@template_exception
def add_collection():
    def post():
        print  request.form.items()
        res = libs.make_request(server_url='https://goods.itvik.com/api/collection/',
                                method='post', 
                                params={'name': request.form.get('collection_name'),
                                        'token': session.get('token')})
        if 'error' in res:
            return template_page(page='add_collection.html', error_message=res['error'])

        return redirect(url_for('plitka'))

    return template_page(page='add_collection.html') if request.method == "GET" else post()


@app.route('/edit_collection', methods=["GET", "POST"])
@login_required()
@template_exception
def edit_collection():
    get_template = lambda id, **kwargs: template_page(page='edit_collection.html', collection_id=id, items=get_collection_images(id), **kwargs)

    def post():
        col_id, col_name = request.form.get('collection_id'), request.form.get('collection_name')
        res = libs.make_request(server_url='https://goods.itvik.com/api/collection/',
                                method='post',
                                params={'id': col_id,
                                        'name': col_name,
                                        'token': session.get('token')})
        if 'error' in res:
            return get_template(col_id, collection_name=col_name, error_message=res.get('error'))

        return redirect(url_for('plitka'))        

    collection_id = request.args.get('collection_id')
    return get_template(collection_id, collection_name=get_collection_name(int(collection_id))) if request.method == "GET" else post()


def get_collection_images(collection_id):
    data=[]
    static_no_image_url = url_for('static', filename='css/images/no_images.jpg')  
    image_res = libs.make_request(server_url='https://goods.itvik.com/api/image/',
                                  method="get", 
                                  params={'token':session.get('token'),
                                          'object_id':collection_id,
                                          'object_name': 'collection'})
    if 'error' in image_res:
        return data

    images = image_res.get('data', {}).get('images', [])
    for x in images:
        image_id, image_name = x.get('id'), x.get('name')
        image_url = x.get('path') if images else None
        image_url = app.config['STATIC_IMAGE_LOCATION'] + image_url if image_url else static_no_image_url
        data.append({'image_id': image_id, 'image_url': image_url, 'image_name': image_name})

    return data

@app.route('/delete_collection_image', methods=["POST"])
def delete_collection_image():
    try:
        res = libs.make_request(server_url='https://goods.itvik.com/api/delete/image/',
                                method="post",
                                params={'token': session.get('token'), 'id': request.form.get('id')})

    except exceptions.NotAuthException, e:
        clear_auth()
        res = {'error': constants.ERRORS.not_auth}
        
    return json.dumps(res)

def get_collection_name(collection_id):

    res = libs.make_request(server_url='https://goods.itvik.com/api/collection/',
                                  method="get", 
                                  params={'token':session.get('token')})
    if 'error' in res:
        return ""
    name = [item for item in res.get('data', {}).get('collections', []) if item.get('id') == collection_id]

    return name[0].get('name') if name else ""


@app.route('/upload_file', methods=["POST"])
@login_required()
@template_exception
def upload_file():
    file1 = request.files.get('photo', None)
    if file1:
        dir_path = os.path.join(app.config['TEMP_DIR'] , os.urandom(20).encode('hex'))
        os.mkdir(dir_path)
        file_path = os.path.join(dir_path , file1.filename)
        file1.save(file_path)
        r = requests.post("https://goods.itvik.com/api/upload/", files={'photo': open(file_path, 'rb')},
                                                                 data={'token': session.get('token'),
                                                                       'object_name': request.form.get('object_name'),
                                                                       'object_id': request.form.get('object_id'),
                                                                       'is_default': request.form.get('is_default', False)},
                                                                 verify=False)
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
        print r.text
    return redirect("%s?collection_id=%s" % (url_for('edit_collection'), request.form.get('object_id')))


@app.route('/send_test', methods=["GET", "POST"])
@login_required()
@template_exception
def send_test():

    print request.args if request.method == "GET" else request.form
    print request.environ.items() if request.method == "POST" else ""

    print "###########"
    return "1"



if __name__ == "__main__":
    app.run()
    
