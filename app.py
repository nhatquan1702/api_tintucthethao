from ast import Str
import json
import pyrebase
import psycopg2
import base64
from flask import Flask, request, jsonify, render_template,redirect
from datetime import datetime
from datetime import timedelta
from datetime import timezone
import time
import datetime
from datetime import timedelta
import requests
from flask_jwt_extended import JWTManager,create_access_token,create_refresh_token,set_access_cookies,jwt_required,set_refresh_cookies,get_jwt_identity,unset_jwt_cookies,get_jwt,get_jwt,verify_jwt_in_request
import socket

# Các mã lỗi
# 200: Success OK
# 400: Bad Request
# 401: Unauthorized
# 404: Not found
# 405: Method not allowed
# 422: Unprocessable Entity
# ===============================
# ===============================
# ===============================

#===== Connect to PostgreSQL in Heroku add on===========
con = psycopg2.connect(database="d3pbrmjh5hgsb9", user="cuefzkwkvdoncc", password="3b5a03ed19cb22bbb695c2b1763d6a7035e2beb9e97221330a9e209500e1c3b8", host="ec2-52-71-231-37.compute-1.amazonaws.com", port="5432")
app = Flask(__name__)

#==== config for cookie========
app.config['JWT_SECRET_KEY']='APISIMPLEAPP'
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=30)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=1)
jwt= JWTManager(app)

# =========Fire base config=================
config = {
    "apiKey": "AIzaSyBYF170a8oXKkqgQrrfoPnZpa45a5AlGTI",
    "authDomain": "imgapi-144fe.firebaseapp.com",
    "databaseURL": "https://imgapi-144fe.firebaseio.com",
    "projectId": "imgapi-144fe",
    "storageBucket": "imgapi-144fe.appspot.com",
    "messagingSenderId": "888978133916",
    "appId": "1:888978133916:web:89c5a046ba04f30ad76e59",
    "measurementId": "G-6KX9HTXCGK"
}
firebase= pyrebase.initialize_app(config)
storage= firebase.storage()

# ============ Another function==============
# ===============================
# ===============================
# ===============================
def myconverter(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()

def checkuser(email):
    cur = con.cursor()
    cur.execute("SELECT id_account from account where email='"+str(email)+"'")
    rows = cur.fetchall()
    if len(rows) !=0:
        return True
    else:
        return False

def checkpass(email,password):
    cur = con.cursor()
    cur.execute("SELECT id_account from account where password='"+str(password)+"' and email='"+str(email)+"'")
    rows = cur.fetchall()
    if len(rows) !=0:
        return True
    else:
        return False

def getuserid(email):
    cur = con.cursor()
    cur.execute("SELECT id_account from account where email='"+str(email)+"'")
    rows = cur.fetchall()
    if len(rows) !=0:
        return rows[0][0]
    else:
        return ""

def getusername(email):
    cur = con.cursor()
    cur.execute("SELECT username from account where email='"+str(email)+"'")
    rows = cur.fetchall()
    if len(rows) !=0:
        return rows[0][0]
    else:
        return ""

def getuserrole(email):
    cur = con.cursor()
    cur.execute("SELECT role from account where email='"+str(email)+"'")
    rows = cur.fetchall()
    return rows[0][0]

def get_identity_if_logedin():
    verify_jwt_in_request(optional=True)
    return get_jwt_identity()

def check_post_exist(id_post):
    cur = con.cursor()
    cur.execute("SELECT rating from post where id_post='"+str(id_post)+"'")
    rows = cur.fetchall()
    if len(rows) != 0:
        return True
    else:
        return False

def check_category_exist(id_category):
    cur = con.cursor()
    cur.execute("SELECT id_category from category where id_category='"+str(id_category)+"'")
    rows = cur.fetchall()
    if len(rows) != 0:
        return True
    else:
        return False

def check_account_exist(id_account):
    cur = con.cursor()
    cur.execute("SELECT id_account from account where id_account="+str(id_account))
    rows = cur.fetchall()
    if len(rows) != 0:
        return True
    else:
        return False

def check_category_exist(id_category):
    cur = con.cursor()
    cur.execute("SELECT id_category from category where id_category="+str(id_category))
    rows = cur.fetchall()
    if len(rows) != 0:
        return True
    else:
        return False

def get_category_level(id_category):
    cur = con.cursor()
    cur.execute("SELECT level from category where id_category='"+str(id_category)+"'")
    rows = cur.fetchall()
    if len(rows) !=0:
        return rows[0][0]
    else:
        return ""

# ========== Main function ============
# ===============================
# ===============================
# ===============================

#======= LOGIN +GET + HEADER(email,password)
#======= return status
#======= 1: unvalid- username + 401
#======= 2: unvalid- password + 401
#======= 0: success- + 200 + access_token + refresh_token + user + role
#======= 3: logedin
@app.route('/login', methods=['GET'])
def login():
    user_indentify = get_identity_if_logedin()
    if user_indentify == None:
         # Get email & password from header + get request for mobile and web
        email= request.headers.get('email')
        password= request.headers.get('password')
        if checkuser(email)== False:
            return jsonify({'status':1}),401
        else:
            if checkpass(email,password)== False:
                return jsonify({'status':2}),401
            else:
                username= getusername(email)
                idaccount= getuserid(email)
                role= getuserrole(email)
                # add role vào jwt để giữ luôn cả role trong access cookie
                additional_claims = {"role":role}
                access_token = create_access_token(email, additional_claims=additional_claims)
                refresh_token = create_refresh_token(identity=email)
                resp=jsonify(idaccount=idaccount,status=0,access_token=access_token,refresh_token=refresh_token,email=email,role=role,username=username)
                set_access_cookies(resp,access_token)
                return resp,200
    else:
        claims = get_jwt()
        username= getusername(claims['sub'])
        idaccount= getuserid(claims['sub'])
        return jsonify({'status':3,'role':claims['role'],'email':claims['sub'],'username':username,'idaccount':idaccount}),200


#======= LOGOUT + GET
#======= return status
#======= 1: success + 200
#======= ở đây chỉ xóa cookie chứ chưa vô hiệu hóa cookie (xử lí bằng cách đưa cookie vào blacklist và check nó)
@app.route("/logout", methods=["GET"])
@jwt_required(refresh=True)
def logout():
    response = jsonify({"status":1})
    unset_jwt_cookies(response)
    return response,200

#===== access_token Expired --> Use RefreshToken to post --> receive new accesstoken
#======= refresh + GET
#======= return status
#======= 1: success + 200
@app.route("/refresh", methods=["GET"])
@jwt_required(refresh=True)
def refresh():
    email = get_jwt_identity()
    role=getuserrole(email)
    additional_claims = {"role":role}
    access_token = create_access_token(email, additional_claims=additional_claims)
    return jsonify(access_token=access_token,status=1),200

# ========= View =====
# ========= Add view when user read post
# ========= return status 
@app.route('/post/view/<int:id_post>',methods=['POST'])
def add_view_to_post(id_post):
    if not check_post_exist:
        return jsonify({"status":0}),200
    cur = con.cursor()
    cur.execute("update post set rating= rating + "+str(1)+" where id_post='"+str(id_post)+"'")
    con.commit()
    return jsonify({"status":1}),200

# ========== Duyệt bài======
# ========== Return status
# 0- Not Allow
# 1- Allow
# 2- Not Exist Post
@app.route('/post/approve/<int:id_post>',methods=['POST'])
@jwt_required()
def post_approve(id_post):
    if not check_post_exist(id_post):
        return jsonify({"status":2}),200
    myjwt=get_jwt()
    role=myjwt['role']
    # Có quyền chỉnh sửa
    if role == 1:
        cur = con.cursor()
        cur.execute("update post set status=1 where id_post='"+str(id_post)+"'")
        con.commit()
        return jsonify({"status":1}),200
    # Không có quyền chỉnh sửa
    elif role == 0:
        return jsonify({"status":0}),200

# ========== Xóa bài viết =======
# ========== Return status
# 0: not allow
# 1: allow --> success
@app.route('/post/del/<int:id_post>',methods=['POST'])
@jwt_required()
def post_del(id_post):
    if not check_post_exist(id_post):
        return jsonify({"status":2}),200
    myjwt=get_jwt()
    role=myjwt['role']
    if role == 0:
        return jsonify({"status":0}),200
    elif role == 1:
        cur = con.cursor()
        cur.execute("DELETE FROM post WHERE id_post=%s;",(id_post,))
        con.commit()
        return jsonify({"status":1}),200

# ========== Thêm bài viết=======
# ========== Return status
# 0: not allow
# 1: allow - not contains title
# 2: allow - not contains content
# 3: allow - not contains category
# 4: allow - not exists categroy
# 5: allow - not contains img
# 6: success
@app.route('/post/add',methods=['POST'])
@jwt_required()
def post_add():
    myjwt=get_jwt()
    role=myjwt['role']
    if role == -1:
        return jsonify({"status":0}),200

    # {"title":"abc","content":"content","category":1,"img":"imgstr"}
    myjson = request.get_json()
    myjson = json.loads(myjson) 

    title= myjson['title']
    title=title.strip()
    if not title:
        return jsonify({"status":1}),200

    content= myjson['content']
    content= content.strip()
    if not content:
        return jsonify({"status":2}),200

    if not myjson['category']:
        return jsonify({"status":3}),200
    if not check_category_exist(int(myjson['category'])):
        return jsonify({"status":4}),200
        
    id_category= int(myjson['category'])
    
    # Get last post id
    cur = con.cursor()
    cur.execute("SELECT id_post from post order by id_post desc limit 1")
    rows = cur.fetchall()
    lastid= rows[0][0]

    if not myjson['img']:
        return jsonify({"status":5}),200
    img_base64_str= myjson['img']
    img_decode_base64 = base64.b64decode(img_base64_str)
    storage.child("/img/"+str(lastid)).put(img_decode_base64)
    img_url= storage.child("/img/"+str(lastid)).get_url(None)

    id_post= lastid+1
    status= 0
    rating= 0
    create_time= datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")
    email= get_jwt_identity()
    cur = con.cursor()
    cur.execute("insert into post values (%s,%s,%s,%s,%s,%s,%s,%s,%s)",(id_post,title,content,status,img_url,create_time,getuserid(email),id_category,rating))
    con.commit()
    
    return jsonify({'status':6}),200

#=========== Sủa bài viết =======
# ========== Return status
# 0: not allow
# 1: allow - not exits post
# 2: allow - not contains title
# 3: allow - not contains content
# 4: allow - not contains category
# 5: allow - not exists categroy
# 6: allow - not contains img
# 7: success
@app.route('/post/edit/<int:id_post>',methods=['POST'])
@jwt_required()
def post_edit(id_post):
    myjwt=get_jwt()
    role=myjwt['role']
    if role == -1:
        return jsonify({'status':0}),200

    myjson = request.get_json()
    myjson= json.loads(myjson)

    if not check_post_exist(id_post):
        return jsonify({'status':1}),200

    title= myjson['title']
    title=title.strip()
    if not title:
        return jsonify({'status':2}),200

    content= myjson['content']
    content= content.strip()
    if not content: 
        return jsonify({'status':3}),200

    if not myjson['category']:
        return jsonify({"status":4}),200
    if not check_category_exist(int(myjson['category'])):
        return jsonify({"status":5}),200
    id_category= int(myjson['category'])
    
    img_base64_str= myjson['img']
    if not img_base64_str:
        return jsonify({'status':6}),200
    if img_base64_str != "":
        img_decode_base64 = base64.b64decode(img_base64_str)
        storage.child("/img/"+str(id_post)).put(img_decode_base64)    
    img_url= storage.child("/img/"+str(id_post)).get_url(None)

    status= 0
    email= get_jwt_identity()

    cur = con.cursor()
    cur.execute("update post set title=%s,content=%s,status=%s,img=%s,id_category=%s where id_post= %s",(title,content,status,img_url,id_category,id_post))
    con.commit()
    return jsonify({"status":7}),200

# ============ Get post with id ============
# ============ Return status 
# 0: not exists post
@app.route('/post/<int:id_post>')
def get_post(id_post):
    if not check_post_exist(id_post):
        return jsonify({'status':0}),200

    cur = con.cursor()
    cur.execute("SELECT id_post,post.title,post.content,post.img,post.create_time,post.rating,account.username from post inner join account on post.create_by= account.id_account where id_post= "+str(id_post))
    rows = cur.fetchall()
    colname=[]
    for i in range(0,7):
        colname.append(cur.description[i][0])

    rtlist=[]
    for row in rows:
        dic={}
        for i in range(0,7):
           dic[colname[i]]=row[i]
        rtlist.append(dic)
    
    cur = con.cursor()
    cur.execute("update post set rating= rating + "+str(1)+" where id_post='"+str(id_post)+"'")
    con.commit()

    js=json.dumps(rtlist,default = myconverter,ensure_ascii=False).encode('utf8')
    return js,200

# =========== Get post with filter sort and select========
# Get api with agrument 
# state --> like where 
# fields --> like select 
# sort --> like order by
# limit --> like limit
# http://127.0.0.1:5000/post?state=status=1&fields=id_post,title,create_time&sort=create_time desc&limit=2
@app.route('/post')
def get_post_filter():
    state=request.args.get('state')
    fields= request.args.get('fields')
    sort= request.args.get('sort')
    limit=request.args.get('limit')

    if limit != None:
        limit=" limit "+str(limit)
    else:
        limit=""

    if sort != None:
        sort=sort.replace(","," ")
        sort=" order by "+sort
    else:
        sort=""

    if state != None:       
        state=state.replace(","," and ")
        state= " where "+state
    else:
        state=""

    if fields != None:
        num_of_fields=len(fields.split(","))
    else:
        num_of_fields=9
        fields=" * "
    
    # sqltest="SELECT "+str(fields)+" from post "+str(state) +str(sort)+str(limit)
    # print(sqltest)
    try:
        cur = con.cursor()
        cur.execute("SELECT "+str(fields)+" from post "+str(state) +str(sort)+str(limit))
        rows = cur.fetchall()
        colname=[]
        for i in range(0,num_of_fields):
            colname.append(cur.description[i][0])

        rtlist=[]
        for row in rows:
            dic={}
            for i in range(0,num_of_fields):
                dic[colname[i]]=row[i]
            rtlist.append(dic)
        js=json.dumps(rtlist,default = myconverter,ensure_ascii=False).encode('utf8')
    except:
        return jsonify({'status':0}),200
    return js,200

# ========= Đăng kí user
# ========= return status+ status code
# 0: success
# 1: invalid username
# 2: invalid email
# 3: invalid password
# 4: email exist
@app.route('/account/reg',methods=['POST'])
def account_reg():
    username= request.headers.get('username')
    email= request.headers.get('email')
    password= request.headers.get('password')
    if not username:
        return jsonify({"status":1}),200
    if not email:
        return jsonify({"status":2}),200
    if not password:
        return jsonify({"status":3}),200
    if checkuser(email):
        return jsonify({"status":4}),200

    # default role
    role= 0
  
    # Get last post id
    cur = con.cursor()
    cur.execute("SELECT id_account from account order by id_account desc limit 1")
    rows = cur.fetchall()
    lastid= rows[0][0]
    id_account= lastid+1
    # Add account to post
    cur = con.cursor()
    cur.execute("insert into account values (%s,%s,%s,%s,%s)",(id_account,username,password,email,role))
    con.commit()
    return jsonify({"status":0}),200

# ========== Thêm tài khoản=======
# ========== Return status
# 0: not allow
# 1: invalid username
# 2: invalid email
# 3: invalid pasword
# 4: email exist
# 5: invalid role
# 6: sql error
# 7: success
@app.route('/account/add',methods=['POST'])
@jwt_required()
def account_add():
    myjwt=get_jwt()
    role=myjwt['role']
    if role == -1:
        return jsonify({'status':0}),200

    myjson = request.get_json()
    myjson = json.loads(myjson) 

    email= myjson['email']
    email= email.strip()
    if not email:
        return jsonify({'status':2}),200
    if checkuser(email):
        return jsonify({'status':4}),200

    username = myjson['username']
    username= username.strip()
    if not username:
        return jsonify({'status':1}),200

    password= myjson['password']
    password= password.strip()
    if not password:
        return jsonify({'status':3}),200
    
    if not myjson['role']:
        return jsonify({'status':5}),200
    role= int(myjson['role'])
    
    # Get last post id
    cur = con.cursor()
    cur.execute("SELECT id_account from account order by id_account desc limit 1")
    rows = cur.fetchall()
    lastid= rows[0][0]
    id_account= lastid+1

    try:
        cur = con.cursor()
        cur.execute("insert into account values (%s,%s,%s,%s,%s)",(id_account,username,password,email,role))
        con.commit()
    except:
        return jsonify({'status':6}),200
    return jsonify({'status':7}),200

# ========== Xóa tài khoản =======
# ========== Return status
# 0: not allow
# 1: not exist account
# 2: SQL error
# 3: Success
@app.route('/account/del/<int:id_account>',methods=['POST'])
@jwt_required()
def account_del(id_account):
    myjwt=get_jwt()
    role=myjwt['role']
    if role == -1:
        return jsonify({'status':0}),200
    if not check_account_exist(id_account):
        return jsonify({'status':1}),200
    
    try:
        cur = con.cursor()
        cur.execute("update account set role=-1 WHERE id_account=%s;",(id_account,))
        con.commit()
    except:
        return jsonify({'status':2}),200
    return jsonify({'status':3}),200

#=========== Sửa tài khoản =======
#=========== Return status
# 0: not allow
# 1: invalid emaiil
# 2: email exist
# 3: invalid username
# 4: invalid password
# 5: not exist account
# 6: invalid role
# 7: sql error
# 8: success
@app.route('/account/edit/<int:id_account>',methods=['POST'])
@jwt_required()
def account_edit(id_account):
    myjwt=get_jwt()
    role=myjwt['role']
    if role == 0:
        return jsonify({'status':0}),200

    myjson = request.get_json()
    myjson= json.loads(myjson)

    if not check_account_exist(id_account):
        return jsonify({'status':5}),200

    email= myjson['email']
    email= email.strip()
    if not email: 
        return jsonify({'status':1}),200

    username= myjson['username']
    username=username.strip()
    if not username:
        return jsonify({'status':3}),200

    password= myjson['password']
    password= password.strip()
    if not password: 
        return jsonify({'status':4}),200

    if not myjson['role']:
        return jsonify({'status':6}),200
    role= int(myjson['role'])
    
    try:
        cur = con.cursor()
        cur.execute("update account set username=%s,password=%s,email=%s,role=%s where id_account= %s",(username,password,email,role,id_account))
        con.commit()
    except:
        return jsonify({'status':7}),200
    return jsonify({'status':8}),200

# =========== Return all category ==========
@app.route('/category')
def rt_categories():
    cur = con.cursor()
    cur.execute("SELECT * from category where level>0")
    rows = cur.fetchall()
    colname=[]
    for i in range(0,4):
        colname.append(cur.description[i][0])
    rtlist=[]
    for row in rows:
        dic={}
        for i in range(0,4):
            dic[colname[i]]=row[i]
        rtlist.append(dic)
    js=json.dumps(rtlist,ensure_ascii=False).encode('utf8')
    return js,200

# ========== Thêm danh mục=======
# 0: not allow ===========
# 1: invalid categrory_name
# 2: invalid level
# 3: invalid id_parent
# 4: not exist id_parent
# 5: SQL error
# 6: Success
@app.route('/category/add',methods=['POST'])
@jwt_required()
def category_add():
    myjwt=get_jwt()
    role=myjwt['role']
    if role == -1:
        return jsonify({'status':0}),200

    myjson = request.get_json()
    myjson = json.loads(myjson) 

    category_name = myjson['category_name']
    category_name= category_name.strip()
    if not category_name:
        return jsonify({'status':1}),200

    # if not myjson['level']:
    #     return jsonify({'status':2}),200

    if not myjson['id_parent']:
        return jsonify({'status':3}),200
    if not myjson['id_parent'] == 'null':
        id_parent= int(myjson['id_parent'])
        if not check_category_exist(id_parent):
            return jsonify({'status':4}),200
        level= int(get_category_level(id_parent))+1
    else: 
        id_parent= 'null'
        level= 1

    # Get last post id
    cur = con.cursor()
    cur.execute("SELECT id_category from category order by id_category desc limit 1")
    rows = cur.fetchall()
    lastid= rows[0][0]

    if not lastid:
        id_category=0
    else:
        id_category= lastid+1

    try:
        cur = con.cursor()
        if id_parent == 'null':
            cur.execute("insert into category values (%s,%s,null,%s)",(id_category,category_name,level))
        else:
            cur.execute("insert into category values (%s,%s,%s,%s)",(id_category,category_name,id_parent,level))
        con.commit()
    except:
        
        return jsonify({'status':5}),200
    return jsonify({'status':6}),200

# ========== Xóa danh mục =======
# 0: not allow
# 1: not exist category
# 2: SQL error
# 3: success
@app.route('/category/del/<int:id_category>',methods=['POST'])
@jwt_required()
def category_del(id_category):
    myjwt=get_jwt()
    role=myjwt['role']
    if role == 0:
        return jsonify({'status':0}),200

    if not check_category_exist(id_category):
        return jsonify({'status':1}),200
    try:
        cur = con.cursor()
        cur.execute("update category set level=-1 WHERE id_category=%s;",(id_category,))
        con.commit()
    except:
        return jsonify({'status':2}),200
    return jsonify({'status':3}),200


#=========== Sủa danh mục =======
# 0: not allow
# 1: invalid category_name
# 2: exist id_category
# 3: invalid id_parent
# 4: not exist id_parent
# 5: invalid level
# 6: SQL error
# 7: Success
@app.route('/category/edit/<int:id_category>',methods=['POST'])
@jwt_required()
def category_edit(id_category):
    myjwt=get_jwt()
    role=myjwt['role']
    if role == -1:
        return jsonify({'status':0}),200

    try:
        myjson = request.get_json()
        myjson= json.loads(myjson)
    except:
        return jsonify({'status':"lỗi load json"}),200

    name= myjson['category_name']
    name=name.strip()
    if not name:
        return jsonify({'status':1}),200

    # if check_category_exist(id_category):
    #     return jsonify({'status':2}),200
    # id_category= int(myjson['id_category'])

    if not myjson['id_parent']:
        return jsonify({'status':3}),200
    if myjson['id_parent'] != 'null':
        if not check_category_exist(myjson['id_parent']):
            return jsonify({'status':4}),200
        id_parent= int(myjson['id_parent']) 
        level= get_category_level(id_parent) + 1
    else:
        id_parent='null'
        level=0
    
    # if not myjson['level']:
    #     return jsonify({'status':5}),200
    # level= int(myjson['level'])
    
    try:
        cur = con.cursor()
        if id_parent == 'null':
            cur.execute("update category set name=%s,id_parent=null,level=%s where id_category= %s",(name,level,id_category))
        else:
            cur.execute("update category set name=%s,id_parent=%s,level=%s where id_category= %s",(name,id_parent,level,id_category))
        con.commit()
    except:
        return jsonify({'status':6}),200
    return jsonify({'status':7}),200


#========= get category theo id
# 0: id not exist
# 1: SQL Error
@app.route('/category/<int:id_category>',methods=['GET'])
def get_category_id(id_category):
    if not check_category_exist(id_category):
        return jsonify({'status':0}),200

    try:
        cur = con.cursor()
        cur.execute("SELECT * from category where id_category= "+str(id_category))
        rows = cur.fetchall()
    except:
        return jsonify({'status':1}),200
    colname=[]
    for i in range(0,3):
        colname.append(cur.description[i][0])

    rtlist=[]
    for row in rows:
        dic={}
        for i in range(0,3):
           dic[colname[i]]=row[i]
        rtlist.append(dic)

    js=json.dumps(rtlist,default = myconverter,ensure_ascii=False).encode('utf8')
    return js,200



# ========= Get All Account for admin ============
# 0: not allow
# 1: SQL Error
@app.route('/account',methods=['GET'])
@jwt_required()
def get_acc_all():
    myjwt=get_jwt()
    role=myjwt['role']
    if role == -1:
        return jsonify({'status':0}),200

    try:
        cur = con.cursor()
        cur.execute("SELECT * from account where role>=0")
        rows = cur.fetchall()
    except:
        return jsonify({'status':1}),200
        
    colname=[]
    for i in range(0,4):
        colname.append(cur.description[i][0])

    rtlist=[]
    for row in rows:
        dic={}
        for i in range(0,4):
           dic[colname[i]]=row[i]
        rtlist.append(dic)

    js=json.dumps(rtlist,default = myconverter,ensure_ascii=False).encode('utf8')
    return js,200

# ========= Get All Account by id============
# 0: not allow
# 1: SQL Error
@app.route('/account/<int:id_account>',methods=['GET'])
@jwt_required()
def get_acc_by_id(id_account):
    myjwt=get_jwt()
    role=myjwt['role']
    if role == -1:
        return jsonify({'status':0}),200

    try:
        cur = con.cursor()
        cur.execute("SELECT * from account where id_account="+str(id_account))
        rows = cur.fetchall()
    except:
        return jsonify({'status':1}),200
        
    colname=[]
    for i in range(0,4):
        colname.append(cur.description[i][0])

    rtlist=[]
    for row in rows:
        dic={}
        for i in range(0,4):
           dic[colname[i]]=row[i]
        rtlist.append(dic)

    js=json.dumps(rtlist,default = myconverter,ensure_ascii=False).encode('utf8')
    return js,200


@app.route('/test',methods=['GET'])
@jwt_required()
def test():
    email= get_jwt_identity()
    claims = get_jwt()
    return jsonify(claims['role'])

@app.route('/index')
def index1():
    user = get_identity_if_logedin()
    print(user)
    if user==None:
        return render_template('index.html')
    else:
        return jsonify({'Logged':True})

@app.route('/testlogin')
def test_login():
    user = get_identity_if_logedin()
    print(user)
    if user==None:
        return jsonify("No User")
    else:
        return jsonify({'User':user})

@app.route('/2')
def index2():
    cur = con.cursor()
    cur.execute("SELECT * from customer")
    rows = cur.fetchall()
    rtlist=[]
    for row in rows:
        rtlist.append(str(row[0])+" "+row[1])
    return "<h1>Welcome "+rtlist[1]+"!!</h1>"

def test():
    pass
#test
# @app.route('/test2',methods=['GET'])
# def test2():
#     response=requests.get('http://127.0.0.1:5000/test',headers={'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTYxNzAwOTczOCwianRpIjoiMzMxY2U5MjktYmIzZi00ZmE4LWE0ZTItODlmMTQ4NWM4YTdjIiwibmJmIjoxNjE3MDA5NzM4LCJ0eXBlIjoiYWNjZXNzIiwic3ViIjoiYmN2IiwiZXhwIjoxNjE3MDEwNjM4fQ.jUM0ZKGwF7B0rssEdyg0uPWMTWXvUlcrdEeKL_jQLtM'})
#     return response.json()

# app.config['uploadimg']=['/uploadimg/']
# @app.route('/img', methods=["POST"])
# def index3():
#     if request.method == 'POST':
#         if request.files:
#             img= request.files["image"]       
#             # img.save('uploadimg/'+img.filename)
#             storage.child("/img/"+img.filename).put(img)
#             return redirect('/2')

# with open("BANH CAM VINH.PNG", "rb") as img_file:
#     my_string = base64.b64encode(img_file.read())

# imgdata = base64.b64decode(my_string)
# print(type(imgdata))
# filename = 'new_image_2'  # I assume you have a way of picking unique filenames
# # with open(filename, 'wb') as f:
# #     f.write(imgdata)

# storage.child("/img/"+filename).put(imgdata)

# with open("BANH CAM VINH.PNG", "rb") as img_file:
#     my_string = base64.b64encode(img_file.read())

# imgdata = base64.b64decode(my_string)




# ----------------------------
# ----------------------------
# ----------------------------
# ----------------------------
# ----------------------------
# ----------------------------
# ----------------------------
# ----------------------------
@app.route('/khoa/tiso',methods=['GET'])
def khoa_ti_so():
    try:
        cur = con.cursor()
        cur.execute("SELECT  match_id ,clb_home_name,clb_guess_name,SUBSTRING(match_result,1,1)  as H ,SUBSTRING(match_result,3,1) as G FROM Match limit 1000")
        rows = cur.fetchall()
    except:
        return jsonify({'status':0}),200
    colname=[]
    for i in range(0,5):
        colname.append(cur.description[i][0])

    rtlist=[]
    for row in rows:
        dic={}
        for i in range(0,5):
            dic[colname[i]]=row[i]
        rtlist.append(dic)
    js=json.dumps(rtlist,default = myconverter,ensure_ascii=False).encode('utf8')
    return js,200

@app.route('/khoa/get_ketqua_nam/<int:nam>',methods=['GET'])
def khoa_get_ketqua_nam(nam):
    try:
        cur = con.cursor()
        cur.execute("""
        SELECT match_id,clb_home_name,clb_guess_name,SUBSTRING(match_result,1,1) as H,SUBSTRING(match_result,3,1) as G,
        EXTRACT(YEAR FROM match_happen_time) as Y 
        FROM Match WHERE EXTRACT(YEAR FROM match_happen_time) =%s
        """,(nam,))
        rows = cur.fetchall()
    except:
        return jsonify({'status':0}),200
    colname=[]
    for i in range(0,6):
        colname.append(cur.description[i][0])

    rtlist=[]
    for row in rows:
        dic={}
        for i in range(0,6):
           dic[colname[i]]=row[i]
        rtlist.append(dic)
    js=json.dumps(rtlist,default = myconverter,ensure_ascii=False).encode('utf8')
    return js,200

@app.route('/khoa/get_bxh_year/<int:nam>',methods=['GET'])
def khoa_Get_bxh_year(nam):
    try:
        cur = con.cursor()
        cur.execute("""
            SELECT club_name, year,match,win,draw,lose,banthang,banthua,(banthang-banthua) as hieuso, (win*3 + draw) as diem FROM RANKING
            WHERE year = '%s'
            ORDER BY diem DESC, hieuso DESC
        """,(nam,))
        rows = cur.fetchall()
    except Exception as e:
        print(e)
        return jsonify({'status':0}),200
    colname=[]
    for i in range(0,10):
        colname.append(cur.description[i][0])

    rtlist=[]
    for row in rows:
        dic={}
        for i in range(0,10):
           dic[colname[i]]=row[i]
        rtlist.append(dic)
    js=json.dumps(rtlist,default = myconverter,ensure_ascii=False).encode('utf8')
    return js,200

@app.route('/khoa/get_all_bxh_doi/<clb_name>',methods=['GET'])
def khoa_get_all_bxh_doi(clb_name):
    try:
        cur = con.cursor()
        cur.execute("""
            SELECT club_name, year,match,win,draw,lose,banthang,banthua,
	        (banthang-banthua) as hieuso, (win*3 + draw) as diem
            FROM RANKING
            WHERE club_name= %s
            order by year asc
        """,(clb_name,))
        rows = cur.fetchall()
    except Exception as e:
        print(e)
        return jsonify({'status':0}),200
    colname=[]
    for i in range(0,10):
        colname.append(cur.description[i][0])

    rtlist=[]
    for row in rows:
        dic={}
        for i in range(0,10):
           dic[colname[i]]=row[i]
        rtlist.append(dic)
    js=json.dumps(rtlist,default = myconverter,ensure_ascii=False).encode('utf8')
    return js,200

@app.route('/khoa/get_bxh_clb_nameYear/<clb_name>/<int:year>',methods=['GET'])
def khoa_get_bxh_clb_nameYeari(clb_name,year):
    try:
        cur = con.cursor()
        cur.execute("""
            SELECT club_name, year,match,win,draw,lose,banthang,banthua,
            (banthang-banthua) as hieuso, (win*3 + draw) as diem
            FROM RANKING
            WHERE club_name= %s and year = %s
        """,(clb_name,str(year),))
        rows = cur.fetchall()
    except Exception as e:
        print(e)
        return jsonify({'status':0}),200
    colname=[]
    for i in range(0,10):
        colname.append(cur.description[i][0])

    rtlist=[]
    for row in rows:
        dic={}
        for i in range(0,10):
           dic[colname[i]]=row[i]
        rtlist.append(dic)
    js=json.dumps(rtlist,default = myconverter,ensure_ascii=False).encode('utf8')
    return js,200


@app.route('/quan/del/comment', methods=['POST'])
def quan_del_comment():
    account_email= request.headers.get('account_email') 
    post_id= request.headers.get('post_id')
    time= request.headers.get('comment_time')
    try:
        cur = con.cursor()
        cur.execute("""
        DELETE FROM comment WHERE post_id =%s and comment_by=%s and comment_time=%s;
        """,(post_id,account_email,time,))
        con.commit()
    except Exception as e:
        con.rollback()
        print(e)
        return jsonify({'status':0}),200
    return jsonify({'status':1}),200


@app.route('/quan/comment', methods=['POST'])
def quan_comment():
    account_email= request.headers.get('account_email') 
    post_id= request.headers.get('post_id')
    comment_content= request.headers.get('comment_content')
    now = datetime.datetime.now()
    timestr=now.strftime("%Y-%m-%d %H:%M:%S")
    try:
        cur = con.cursor()
        cur.execute("""
        insert into Comment values (%s,%s,%s,%s)
        """,(post_id,account_email,timestr,comment_content,))
        con.commit()
    except Exception as e:
        con.rollback()
        print(e)
        return jsonify({'status':0}),200
    return jsonify({'status':1}),200

@app.route('/quan/list_comment/<post_id>',methods=['GET'])
def quan_list_comment(post_id):
    try:
        cur = con.cursor()
        cur.execute("""select *
            from Comment
            where post_id= %s
            order by comment_time asc""",(post_id,))
        rows = cur.fetchall()
    except:
        return jsonify({'status':0}),200
    colname=[]
    for i in range(0,4):
        colname.append(cur.description[i][0])

    rtlist=[]
    for row in rows:
        dic={}
        for i in range(0,4):
           dic[colname[i]]=row[i]
        rtlist.append(dic)
    js=json.dumps(rtlist,default = myconverter,ensure_ascii=False).encode('utf8')
    return js,200


@app.route('/quan/list_baiviethot',methods=['GET'])
def quan_list_baiviethot():
    try:
        cur = con.cursor()
        cur.execute("""
            select post.post_id, post.post_title, post.post_img, post.post_create_time, post.post_view 
            from( select post_id from post_tag where post_tag_name = 'hot') 
            as hot_post 
            inner join 
            (select *
            from post 
            where post_status != -1) as post
            on post.post_id= hot_post.post_id order by post.post_create_time desc,post.post_view desc
        """)
        rows = cur.fetchall()
    except:
        return jsonify({'status':0}),200
    colname=[]
    for i in range(0,5):
        colname.append(cur.description[i][0])

    rtlist=[]
    for row in rows:
        dic={}
        for i in range(0,5):
           dic[colname[i]]=row[i]
        rtlist.append(dic)
    js=json.dumps(rtlist,default = myconverter,ensure_ascii=False).encode('utf8')
    return js,200

@app.route('/quan/list_tinmoi',methods=['GET'])
def quan_list_tinmoi():
    try:
        cur = con.cursor()
        cur.execute("""
            select post.post_id, post.post_title, post.post_img, post.post_create_time, post.post_view 
            from post 
            where post_status != -1
            order by post.post_create_time desc
        """)
        rows = cur.fetchall()
    except:
        return jsonify({'status':0}),200
    colname=[]
    for i in range(0,5):
        colname.append(cur.description[i][0])

    rtlist=[]
    for row in rows:
        dic={}
        for i in range(0,5):
           dic[colname[i]]=row[i]
        rtlist.append(dic)
    js=json.dumps(rtlist,default = myconverter,ensure_ascii=False).encode('utf8')
    return js,200

@app.route('/quan/list_tinphobien',methods=['GET'])
def quan_list_tinphobien():
    try:
        cur = con.cursor()
        cur.execute("""
            select post.post_id, post.post_title, post.post_img, post.post_create_time, post.post_view 
            from post 
            where post_status != -1
            order by post.post_create_time desc, post.post_view desc
        """)
        rows = cur.fetchall()
    except:
        return jsonify({'status':0}),200
    colname=[]
    for i in range(0,5):
        colname.append(cur.description[i][0])

    rtlist=[]
    for row in rows:
        dic={}
        for i in range(0,5):
           dic[colname[i]]=row[i]
        rtlist.append(dic)
    js=json.dumps(rtlist,default = myconverter,ensure_ascii=False).encode('utf8')
    return js,200
@app.route('/quan/list_tinchuyennhuong',methods=['GET'])
def quan_list_tinchuyennhuong():
    try:
        cur = con.cursor()
        cur.execute("""
            select post.post_id, post.post_title, post.post_img, post.post_create_time, post.post_view 
            from( select post_id from post_tag where post_tag_name = 'cn' ) as hot_post
            inner join 
            (select * 
            from post
            where post_status != -1)as post
            on post.post_id= hot_post.post_id order by post.post_create_time desc,post.post_view desc
        """)
        rows = cur.fetchall()
    except:
        return jsonify({'status':0}),200
    colname=[]
    for i in range(0,5):
        colname.append(cur.description[i][0])

    rtlist=[]
    for row in rows:
        dic={}
        for i in range(0,5):
           dic[colname[i]]=row[i]
        rtlist.append(dic)
    js=json.dumps(rtlist,default = myconverter,ensure_ascii=False).encode('utf8')
    return js,200
@app.route('/quan/chitietbaiviet/<int:post_id>',methods=['GET'])
def quan_chitietbaiviet(post_id):
    try:
        cur = con.cursor()
        cur.execute("select * from post where post.post_id=%s",(post_id,))
        rows = cur.fetchall()
    except:
        return jsonify({'status':0}),200
    colname=[]
    for i in range(0,8):
        colname.append(cur.description[i][0])

    rtlist=[]
    for row in rows:
        dic={}
        for i in range(0,8):
           dic[colname[i]]=row[i]
        rtlist.append(dic)

    cur= con.cursor()
    cur.execute("UPDATE post SET post_view=post_view+1 WHERE post_id=%s",(post_id,))
    con.commit()
    js=json.dumps(rtlist,default = myconverter,ensure_ascii=False).encode('utf8')
    return js,200
@app.route('/quan/list_clb',methods=['GET'])
def quan_list_clb():
    try:
        cur = con.cursor()
        cur.execute("select * from clb where clb_name != 'OTHER'")
        rows = cur.fetchall()
    except:
        return jsonify({'status':0}),200
    colname=[]
    for i in range(0,2):
        colname.append(cur.description[i][0])

    rtlist=[]
    for row in rows:
        dic={}
        for i in range(0,2):
           dic[colname[i]]=row[i]
        rtlist.append(dic)
    js=json.dumps(rtlist,default = myconverter,ensure_ascii=False).encode('utf8')
    return js,200
@app.route('/quan/chitietclb/<clb_id>',methods=['GET'])
def quan_chitietclb(clb_id):
    try:
        cur = con.cursor()
        cur.execute("select * from clb where clb_name=%s",(clb_id,))
        rows = cur.fetchall()
    except:
        return jsonify({'status':0}),200
    colname=[]
    for i in range(0,2):
        colname.append(cur.description[i][0])

    rtlist=[]
    for row in rows:
        dic={}
        for i in range(0,2):
           dic[colname[i]]=row[i]
        rtlist.append(dic)
    js=json.dumps(rtlist,default = myconverter,ensure_ascii=False).encode('utf8')
    return js,200
@app.route('/quan/tatcacauthu_clb/<clb_id>',methods=['GET'])
def quan_tatcacauthu_clb(clb_id):
    try:
        cur = con.cursor()
        cur.execute("""
    select player.*,rs_player_properties.value,rs_player_properties.performance,rs_player_properties.number,rs_player_properties.position
    from(
        select player_id
        from player_clubs
        where clb_name=%s and end_time is null
    )as player_club
    inner join player on player.player_id= player_club.player_id
    inner join(
        select player_id,
            max(case when (property_name='value') then property_value else NULL end) as value,
            max(case when (property_name='position') then property_value else NULL end) as position,
            max(case when (property_name='performance') then property_value else NULL end) as performance,
            max(case when (property_name='number') then property_value else NULL end) as number
        from(
            select *
            from(
                select Player_Properties.player_id,Player_Properties.property_name,Player_Properties.property_value
                from Player_Properties
                inner join(
                    select player_id,property_name, max(start_time) as start_time
                    from Player_Properties
                    group by player_id, property_name
                )as max_date
                on max_date.player_id=Player_Properties.player_id and max_date.start_time=Player_Properties.start_time
                and max_date.property_name= Player_Properties.property_name
            ) as max_date_player_properties
        )as temp
        group by temp.player_id
        order by temp.player_id
    )as rs_player_properties
    on rs_player_properties.player_id= player.player_id 
        """,(clb_id,))
        rows = cur.fetchall()
    except:
        return jsonify({'status':0}),200
    colname=[]
    for i in range(0,12):
        colname.append(cur.description[i][0])

    rtlist=[]
    for row in rows:
        dic={}
        for i in range(0,12):
           dic[colname[i]]=row[i]
        rtlist.append(dic)
    js=json.dumps(rtlist,default = myconverter,ensure_ascii=False).encode('utf8')
    return js,200

@app.route('/quan/trandau_chuada',methods=['GET'])
def quan_trandau_chuada():
    try:
        cur = con.cursor()
        cur.execute("""
            select match.*,home_clb.clb_img_url as clb_home_img_url, guess_clb.clb_img_url as clb_guess_img_url
            from(
                select *
                from match
                where match_result = '-:-') as match
            inner join clb as home_clb
            on home_clb.clb_name= match.clb_home_name
            inner join clb as guess_clb
            on guess_clb.clb_name= match.clb_guess_name
        """)
        rows = cur.fetchall()
    except:
        return jsonify({'status':0}),200
    colname=[]
    for i in range(0,9):
        colname.append(cur.description[i][0])

    rtlist=[]
    for row in rows:
        dic={}
        for i in range(0,9):
           dic[colname[i]]=row[i]
        rtlist.append(dic)
    js=json.dumps(rtlist,default = myconverter,ensure_ascii=False).encode('utf8')
    return js,200

@app.route('/quan/trandau/<match_id>',methods=['GET'])
def quan_trandau(match_id):
    try:
        cur = con.cursor()
        cur.execute("select clb_home_name,clb_guess_name,match_result,match_happen_time from match where match_id = %s",(match_id,))
        rows = cur.fetchall()
    except:
        return jsonify({'status':0}),200
    colname=[]
    for i in range(0,4):
        colname.append(cur.description[i][0])

    rtlist=[]
    for row in rows:
        dic={}
        for i in range(0,4):
           dic[colname[i]]=row[i]
        rtlist.append(dic)
    js=json.dumps(rtlist,default = myconverter,ensure_ascii=False).encode('utf8')
    return js,200

@app.route('/quan/trandau_home_main/<match_id>',methods=['GET'])
def quan_trandau_home_main(match_id):
    try:
        cur = con.cursor()
        cur.execute("""
        select player_clubs.*,player.player_international_name,rs_player_properties.number,rs_player_properties.performance, rs_player_properties.position
        from(
            select player_id,match_id
            from player_match_event
            where event_name='main' -- nếu là đội hình dữ bị thì thay bằng 'sub'
            and match_id = %s
        )as match_player
        inner join (
            select player_id,clb_name
            from player_clubs
            where clb_name = (
                select clb_home_name -- nếu muốn lấy đội khách thì đổi thành clb_guess_name
                from match 
                where match_id= %s
                limit 1
            )
        )as player_clubs 
        on player_clubs.player_id= match_player.player_id
        inner join player on player.player_id= player_clubs.player_id
        inner join(
            select player_id,
                max(case when (property_name='value') then property_value else NULL end) as value,
                max(case when (property_name='position') then property_value else NULL end) as position,
                max(case when (property_name='performance') then property_value else NULL end) as performance,
                max(case when (property_name='number') then property_value else NULL end) as number
            from(
                select *
                from(
                    select Player_Properties.player_id,Player_Properties.property_name,Player_Properties.property_value
                    from Player_Properties
                    inner join(
                        select player_id,property_name, max(start_time) as start_time
                        from Player_Properties
                        group by player_id, property_name
                    )as max_date
                    on max_date.player_id=Player_Properties.player_id and max_date.start_time=Player_Properties.start_time
                    and max_date.property_name= Player_Properties.property_name
                ) as max_date_player_properties
            )as temp
            group by temp.player_id
            order by temp.player_id
        )as rs_player_properties
        on rs_player_properties.player_id= player.player_id
         """,(match_id,match_id,))
        rows = cur.fetchall()
    except Exception as e:
        print(e)
        return jsonify({'status':0}),200
    colname=[]
    for i in range(0,6):
        colname.append(cur.description[i][0])

    rtlist=[]
    for row in rows:
        dic={}
        for i in range(0,6):
           dic[colname[i]]=row[i]
        rtlist.append(dic)
    js=json.dumps(rtlist,default = myconverter,ensure_ascii=False).encode('utf8')
    return js,200
@app.route('/quan/trandau_home_sub/<match_id>',methods=['GET'])
def quan_trandau_home_sub(match_id):
    try:
        cur = con.cursor()
        cur.execute("""
        select player_clubs.*,player.player_international_name,rs_player_properties.number,rs_player_properties.performance, rs_player_properties.position
        from(
            select player_id,match_id
            from player_match_event
            where event_name='sub' -- nếu là đội hình dữ bị thì thay bằng 'sub'
            and match_id = %s
        )as match_player
        inner join (
            select player_id,clb_name
            from player_clubs
            where clb_name = (
                select clb_home_name -- nếu muốn lấy đội khách thì đổi thành clb_guess_name
                from match 
                where match_id= %s
                limit 1
            )
        )as player_clubs 
        on player_clubs.player_id= match_player.player_id
        inner join player on player.player_id= player_clubs.player_id
        inner join(
            select player_id,
                max(case when (property_name='value') then property_value else NULL end) as value,
                max(case when (property_name='position') then property_value else NULL end) as position,
                max(case when (property_name='performance') then property_value else NULL end) as performance,
                max(case when (property_name='number') then property_value else NULL end) as number
            from(
                select *
                from(
                    select Player_Properties.player_id,Player_Properties.property_name,Player_Properties.property_value
                    from Player_Properties
                    inner join(
                        select player_id,property_name, max(start_time) as start_time
                        from Player_Properties
                        group by player_id, property_name
                    )as max_date
                    on max_date.player_id=Player_Properties.player_id and max_date.start_time=Player_Properties.start_time
                    and max_date.property_name= Player_Properties.property_name
                ) as max_date_player_properties
            )as temp
            group by temp.player_id
            order by temp.player_id
        )as rs_player_properties
        on rs_player_properties.player_id= player.player_id
         """,(match_id,match_id,))
        rows = cur.fetchall()
    except Exception as e:
        print(e)
        return jsonify({'status':0}),200
    colname=[]
    for i in range(0,6):
        colname.append(cur.description[i][0])

    rtlist=[]
    for row in rows:
        dic={}
        for i in range(0,6):
           dic[colname[i]]=row[i]
        rtlist.append(dic)
    js=json.dumps(rtlist,default = myconverter,ensure_ascii=False).encode('utf8')
    return js,200
@app.route('/quan/trandau_guess_main/<match_id>',methods=['GET'])
def quan_trandau_guess_main(match_id):
    try:
        cur = con.cursor()
        cur.execute("""
        select player_clubs.*,player.player_international_name,rs_player_properties.number,rs_player_properties.performance, rs_player_properties.position
        from(
            select player_id,match_id
            from player_match_event
            where event_name='main' -- nếu là đội hình dữ bị thì thay bằng 'sub'
            and match_id = %s
        )as match_player
        inner join (
            select player_id,clb_name
            from player_clubs
            where clb_name = (
                select clb_guess_name -- nếu muốn lấy đội khách thì đổi thành clb_guess_name
                from match 
                where match_id= %s
                limit 1
            )
        )as player_clubs 
        on player_clubs.player_id= match_player.player_id
        inner join player on player.player_id= player_clubs.player_id
        inner join(
            select player_id,
                max(case when (property_name='value') then property_value else NULL end) as value,
                max(case when (property_name='position') then property_value else NULL end) as position,
                max(case when (property_name='performance') then property_value else NULL end) as performance,
                max(case when (property_name='number') then property_value else NULL end) as number
            from(
                select *
                from(
                    select Player_Properties.player_id,Player_Properties.property_name,Player_Properties.property_value
                    from Player_Properties
                    inner join(
                        select player_id,property_name, max(start_time) as start_time
                        from Player_Properties
                        group by player_id, property_name
                    )as max_date
                    on max_date.player_id=Player_Properties.player_id and max_date.start_time=Player_Properties.start_time
                    and max_date.property_name= Player_Properties.property_name
                ) as max_date_player_properties
            )as temp
            group by temp.player_id
            order by temp.player_id
        )as rs_player_properties
        on rs_player_properties.player_id= player.player_id
         """,(match_id,match_id,))
        rows = cur.fetchall()
    except Exception as e:
        print(e)
        return jsonify({'status':0}),200
    colname=[]
    for i in range(0,6):
        colname.append(cur.description[i][0])

    rtlist=[]
    for row in rows:
        dic={}
        for i in range(0,6):
           dic[colname[i]]=row[i]
        rtlist.append(dic)
    js=json.dumps(rtlist,default = myconverter,ensure_ascii=False).encode('utf8')
    return js,200
@app.route('/quan/trandau_guess_sub/<match_id>',methods=['GET'])
def quan_trandau_guess_sub(match_id):
    try:
        cur = con.cursor()
        cur.execute("""
        select player_clubs.*,player.player_international_name,rs_player_properties.number,rs_player_properties.performance, rs_player_properties.position
        from(
            select player_id,match_id
            from player_match_event
            where event_name='sub' -- nếu là đội hình dữ bị thì thay bằng 'sub'
            and match_id = %s
        )as match_player
        inner join (
            select player_id,clb_name
            from player_clubs
            where clb_name = (
                select clb_guess_name -- nếu muốn lấy đội khách thì đổi thành clb_guess_name
                from match 
                where match_id= %s
                limit 1
            )
        )as player_clubs 
        on player_clubs.player_id= match_player.player_id
        inner join player on player.player_id= player_clubs.player_id
        inner join(
            select player_id,
                max(case when (property_name='value') then property_value else NULL end) as value,
                max(case when (property_name='position') then property_value else NULL end) as position,
                max(case when (property_name='performance') then property_value else NULL end) as performance,
                max(case when (property_name='number') then property_value else NULL end) as number
            from(
                select *
                from(
                    select Player_Properties.player_id,Player_Properties.property_name,Player_Properties.property_value
                    from Player_Properties
                    inner join(
                        select player_id,property_name, max(start_time) as start_time
                        from Player_Properties
                        group by player_id, property_name
                    )as max_date
                    on max_date.player_id=Player_Properties.player_id and max_date.start_time=Player_Properties.start_time
                    and max_date.property_name= Player_Properties.property_name
                ) as max_date_player_properties
            )as temp
            group by temp.player_id
            order by temp.player_id
        )as rs_player_properties
        on rs_player_properties.player_id= player.player_id
         """,(match_id,match_id,))
        rows = cur.fetchall()
    except Exception as e:
        print(e)
        return jsonify({'status':0}),200
    colname=[]
    for i in range(0,6):
        colname.append(cur.description[i][0])

    rtlist=[]
    for row in rows:
        dic={}
        for i in range(0,6):
           dic[colname[i]]=row[i]
        rtlist.append(dic)
    js=json.dumps(rtlist,default = myconverter,ensure_ascii=False).encode('utf8')
    return js,200
@app.route('/quan/trandau_dienbien/<match_id>',methods=['GET'])
def quan_trandau_dienbien(match_id):
    try:
        cur = con.cursor()
        cur.execute("""
        select player_clubs.*,player.player_international_name,rs_player_properties.number,
        rs_player_properties.position,match_player.event_name,match_player.start_time
        from(
            select player_id,match_id,event_name,start_time
            from player_match_event
            where event_name in ('goal','assist','in','out','yellow','red') -- nếu là đội hình dữ bị thì thay bằng 'sub'
            and match_id = %s
        )as match_player
        inner join (
            select player_id,clb_name
            from player_clubs
            where clb_name = (
                select clb_home_name -- nếu muốn lấy đội khách thì đổi thành clb_guess_name
                from match 
                where match_id= %s
                limit 1
            ) or clb_name = (
                select clb_guess_name -- nếu muốn lấy đội khách thì đổi thành clb_guess_name
                from match 
                where match_id=%s
                limit 1
            )
        )as player_clubs 
        on player_clubs.player_id= match_player.player_id
        inner join player on player.player_id= player_clubs.player_id
        inner join(
            select player_id,
                max(case when (property_name='value') then property_value else NULL end) as value,
                max(case when (property_name='position') then property_value else NULL end) as position,
                max(case when (property_name='performance') then property_value else NULL end) as performance,
                max(case when (property_name='number') then property_value else NULL end) as number
            from(
                select *
                from(
                    select Player_Properties.player_id,Player_Properties.property_name,Player_Properties.property_value
                    from Player_Properties
                    inner join(
                        select player_id,property_name, max(start_time) as start_time
                        from Player_Properties
                        group by player_id, property_name
                    )as max_date
                    on max_date.player_id=Player_Properties.player_id and max_date.start_time=Player_Properties.start_time
                    and max_date.property_name= Player_Properties.property_name
                ) as max_date_player_properties
            )as temp
            group by temp.player_id
            order by temp.player_id
        )as rs_player_properties
        on rs_player_properties.player_id= player.player_id
        order by match_player.start_time asc
         """,(match_id,match_id,match_id,))
        rows = cur.fetchall()
    except Exception as e:
        print(e)
        return jsonify({'status':0}),200
    colname=[]
    for i in range(0,7):
        colname.append(cur.description[i][0])

    rtlist=[]
    for row in rows:
        dic={}
        for i in range(0,7):
           dic[colname[i]]=row[i]
        rtlist.append(dic)
    js=json.dumps(rtlist,default = myconverter,ensure_ascii=False).encode('utf8')
    return js,200

@app.route('/quan/doihinhrasan/<match_id>',methods=['GET'])
def quan_dohinhrasan(match_id):
    try:
        cur = con.cursor()
        cur.execute("""
            select player_clubs.*,player.player_international_name,rs_player_properties.number,rs_player_properties.performance, rs_player_properties.position
            from(
                select player_id,match_id
                from player_match_event
                where event_name='main' -- nếu là đội hình dữ bị thì thay bằng 'sub'
                and match_id = %s
            )as match_player
            inner join (
                select player_id,clb_name
                from player_clubs
                where clb_name = (
                    select clb_home_name -- nếu muốn lấy đội khách thì đổi thành clb_guess_name
                    from match 
                    where match_id= %s
                    limit 1
                )
            )as player_clubs 
            on player_clubs.player_id= match_player.player_id
            inner join player on player.player_id= player_clubs.player_id
            inner join(
                select player_id,
                    max(case when (property_name='value') then property_value else NULL end) as value,
                    max(case when (property_name='position') then property_value else NULL end) as position,
                    max(case when (property_name='performance') then property_value else NULL end) as performance,
                    max(case when (property_name='number') then property_value else NULL end) as number
                from(
                    select *
                    from(
                        select Player_Properties.player_id,Player_Properties.property_name,Player_Properties.property_value
                        from Player_Properties
                        inner join(
                            select player_id,property_name, max(start_time) as start_time
                            from Player_Properties
                            group by player_id, property_name
                        )as max_date
                        on max_date.player_id=Player_Properties.player_id and max_date.start_time=Player_Properties.start_time
                        and max_date.property_name= Player_Properties.property_name
                    ) as max_date_player_properties
                )as temp
                group by temp.player_id
                order by temp.player_id
            )as rs_player_properties
            on rs_player_properties.player_id= player.player_id
         """,(match_id,match_id,))
    except Exception as e:
        print(e)
        return jsonify({'status':0}),200
    home_main_rows = cur.fetchall()
    colname=[]
    for i in range(0,6):
        colname.append(cur.description[i][0])
    home_main_rtlist=[]
    for row in home_main_rows:
        dic={}
        for i in range(0,6):
           dic[colname[i]]=row[i]
        home_main_rtlist.append(dic)

    
    try:
        cur = con.cursor()
        cur.execute("""
            select player_clubs.*,player.player_international_name,rs_player_properties.number,rs_player_properties.performance, rs_player_properties.position
            from(
                select player_id,match_id
                from player_match_event
                where event_name='sub' -- nếu là đội hình dữ bị thì thay bằng 'sub'
                and match_id = %s
            )as match_player
            inner join (
                select player_id,clb_name
                from player_clubs
                where clb_name = (
                    select clb_home_name -- nếu muốn lấy đội khách thì đổi thành clb_guess_name
                    from match 
                    where match_id= %s
                    limit 1
                )
            )as player_clubs 
            on player_clubs.player_id= match_player.player_id
            inner join player on player.player_id= player_clubs.player_id
            inner join(
                select player_id,
                    max(case when (property_name='value') then property_value else NULL end) as value,
                    max(case when (property_name='position') then property_value else NULL end) as position,
                    max(case when (property_name='performance') then property_value else NULL end) as performance,
                    max(case when (property_name='number') then property_value else NULL end) as number
                from(
                    select *
                    from(
                        select Player_Properties.player_id,Player_Properties.property_name,Player_Properties.property_value
                        from Player_Properties
                        inner join(
                            select player_id,property_name, max(start_time) as start_time
                            from Player_Properties
                            group by player_id, property_name
                        )as max_date
                        on max_date.player_id=Player_Properties.player_id and max_date.start_time=Player_Properties.start_time
                        and max_date.property_name= Player_Properties.property_name
                    ) as max_date_player_properties
                )as temp
                group by temp.player_id
                order by temp.player_id
            )as rs_player_properties
            on rs_player_properties.player_id= player.player_id
         """,(match_id,match_id,))
    except Exception as e:
        print(e)
        return jsonify({'status':0}),200
    home_sub_rows = cur.fetchall()
    colname=[]
    for i in range(0,6):
        colname.append(cur.description[i][0])
    home_sub_rtlist=[]
    for row in home_sub_rows:
        dic={}
        for i in range(0,6):
           dic[colname[i]]=row[i]
        home_sub_rtlist.append(dic)


    try:
        cur = con.cursor()
        cur.execute("""
            select player_clubs.*,player.player_international_name,rs_player_properties.number,rs_player_properties.performance, rs_player_properties.position
            from(
                select player_id,match_id
                from player_match_event
                where event_name='main' -- nếu là đội hình dữ bị thì thay bằng 'sub'
                and match_id = %s
            )as match_player
            inner join (
                select player_id,clb_name
                from player_clubs
                where clb_name = (
                    select clb_guess_name -- nếu muốn lấy đội khách thì đổi thành clb_guess_name
                    from match 
                    where match_id= %s
                    limit 1
                )
            )as player_clubs 
            on player_clubs.player_id= match_player.player_id
            inner join player on player.player_id= player_clubs.player_id
            inner join(
                select player_id,
                    max(case when (property_name='value') then property_value else NULL end) as value,
                    max(case when (property_name='position') then property_value else NULL end) as position,
                    max(case when (property_name='performance') then property_value else NULL end) as performance,
                    max(case when (property_name='number') then property_value else NULL end) as number
                from(
                    select *
                    from(
                        select Player_Properties.player_id,Player_Properties.property_name,Player_Properties.property_value
                        from Player_Properties
                        inner join(
                            select player_id,property_name, max(start_time) as start_time
                            from Player_Properties
                            group by player_id, property_name
                        )as max_date
                        on max_date.player_id=Player_Properties.player_id and max_date.start_time=Player_Properties.start_time
                        and max_date.property_name= Player_Properties.property_name
                    ) as max_date_player_properties
                )as temp
                group by temp.player_id
                order by temp.player_id
            )as rs_player_properties
            on rs_player_properties.player_id= player.player_id
         """,(match_id,match_id,))
    except Exception as e:
        print(e)
        return jsonify({'status':0}),200
    guess_main_rows = cur.fetchall()
    colname=[]
    for i in range(0,6):
        colname.append(cur.description[i][0])
    guess_main_rtlist=[]
    for row in guess_main_rows:
        dic={}
        for i in range(0,6):
           dic[colname[i]]=row[i]
        guess_main_rtlist.append(dic)


    try:
        cur = con.cursor()
        cur.execute("""
            select player_clubs.*,player.player_international_name,rs_player_properties.number,rs_player_properties.performance, rs_player_properties.position
            from(
                select player_id,match_id
                from player_match_event
                where event_name='sub' -- nếu là đội hình dữ bị thì thay bằng 'sub'
                and match_id = %s
            )as match_player
            inner join (
                select player_id,clb_name
                from player_clubs
                where clb_name = (
                    select clb_guess_name -- nếu muốn lấy đội khách thì đổi thành clb_guess_name
                    from match 
                    where match_id= %s
                    limit 1
                )
            )as player_clubs 
            on player_clubs.player_id= match_player.player_id
            inner join player on player.player_id= player_clubs.player_id
            inner join(
                select player_id,
                    max(case when (property_name='value') then property_value else NULL end) as value,
                    max(case when (property_name='position') then property_value else NULL end) as position,
                    max(case when (property_name='performance') then property_value else NULL end) as performance,
                    max(case when (property_name='number') then property_value else NULL end) as number
                from(
                    select *
                    from(
                        select Player_Properties.player_id,Player_Properties.property_name,Player_Properties.property_value
                        from Player_Properties
                        inner join(
                            select player_id,property_name, max(start_time) as start_time
                            from Player_Properties
                            group by player_id, property_name
                        )as max_date
                        on max_date.player_id=Player_Properties.player_id and max_date.start_time=Player_Properties.start_time
                        and max_date.property_name= Player_Properties.property_name
                    ) as max_date_player_properties
                )as temp
                group by temp.player_id
                order by temp.player_id
            )as rs_player_properties
            on rs_player_properties.player_id= player.player_id
         """,(match_id,match_id,))
    except Exception as e:
        print(e)
        return jsonify({'status':0}),200
    guess_sub_rows = cur.fetchall()
    colname=[]
    for i in range(0,6):
        colname.append(cur.description[i][0])
    guess_sub_rtlist=[]
    for row in guess_sub_rows:
        dic={}
        for i in range(0,6):
           dic[colname[i]]=row[i]
        guess_sub_rtlist.append(dic)


    rtlist=[]
    dic={}
    dic["home_main"]=home_main_rtlist
    rtlist.append(dic)
    dic={}
    dic["home_sub"]=home_sub_rtlist
    rtlist.append(dic)
    dic={}
    dic["guess_main"]=guess_main_rtlist
    rtlist.append(dic)
    dic={}
    dic["guess_sub"]=guess_sub_rtlist
    rtlist.append(dic)

    js=json.dumps(rtlist,default = myconverter,ensure_ascii=False).encode('utf8')
    return js,200

@app.route('/quan/search/<tukhoa>',methods=['GET'])
def quan_serchbaiviet(tukhoa):
    try:
        cur = con.cursor()
        cur.execute("select post_id,post_title,post_img,post_create_time,post_view from post where post_title ilike '%"+tukhoa+"%'" )
        rows = cur.fetchall()
    except:
        return jsonify({'status':0}),200
    colname=[]
    for i in range(0,5):
        colname.append(cur.description[i][0])

    rtlist=[]
    for row in rows:
        dic={}
        for i in range(0,5):
           dic[colname[i]]=row[i]
        rtlist.append(dic)
    js=json.dumps(rtlist,default = myconverter,ensure_ascii=False).encode('utf8')
    return js,200

@app.route('/quan/create_match', methods=['POST'])
def quan_create_match():
    clb_home_name= request.headers.get('clb_home_name') 
    clb_guess_name= request.headers.get('clb_guess_name')
    match_happen_time= request.headers.get('match_happen_time')
    match_id= str(match_happen_time).split('-')[0]+"_"+str(clb_home_name)+"_"+str(clb_guess_name)
    # now = datetime.datetime.now()
    # timestr=now.strftime("%Y-%m-%d %H:%M:%S")
    try:
        cur = con.cursor()
        cur.execute("""
        insert into Match values (%s,%s,%s,%s,%s,%s,%s)
        """,(match_id,match_happen_time,None,clb_home_name,clb_guess_name,None,"-:-",))
        con.commit()
    except Exception as e:
        con.rollback()
        print(e)
        return jsonify({'status':0}),200
    return jsonify({'status':1}),200

@app.route('/quan/create_match_event/<match_id>', methods=['POST'])
def quan_create_event(match_id):
    player_id= request.headers.get('player_id') 
    event_name= request.headers.get('event_name')
    start_time= request.headers.get('start_time')
    # now = datetime.datetime.now()
    # timestr=now.strftime("%Y-%m-%d %H:%M:%S")
    try:
        cur = con.cursor()
        cur.execute("""
        insert into player_match_event values (%s,%s,%s,%s)
        """,(player_id, match_id,event_name,start_time, ))
        con.commit()
    except Exception as e:
        con.rollback()
        print(e)
        return jsonify({'status':0}),200
    return jsonify({'status':1}),200

@app.route('/quan/match_result/<match_id>', methods=['POST'])
def quan_match_result(match_id):
    match_result= request.headers.get('match_result') 
    # now = datetime.datetime.now()
    # timestr=now.strftime("%Y-%m-%d %H:%M:%S")
    try:
        cur = con.cursor()
        cur.execute("""
        update match set match_result=%s where match_id=%s
        """,(match_result,match_id,))
        con.commit()
    except Exception as e:
        con.rollback()
        print(e)
        return jsonify({'status':0}),200
    
    match_cur = con.cursor()
    match_cur.execute("select match_id,match_happen_time,match_result from Match where match_id=%s",(match_id,))
    match_resultset= match_cur.fetchall()
    for match in match_resultset:
        # Kiểm tra trận đấu diên ra chưa
        match_result= match[2]
        if match_result =='-:-':
            continue
        # Xử lí 
        match_happen_time= match[1]
        match_id= match[0]
        player_event_cur= con.cursor()
        player_event_cur.execute("select player_id from Player_Match_Event where match_id = %s and event_name in ('yellow','red','goal','assist')",(match_id,))
        player_event_resultset= player_event_cur.fetchall()
        player_list=[]
        print("Trận đấu: "+match_id)
        for player_event_result in player_event_resultset:
            player_id= player_event_result[0]
            if not player_id in player_list:
                player_list.append(player_id)

        for player_id in player_list:
            player_cusor= con.cursor()
            player_cusor.execute("select event_name from Player_Match_Event where match_id = %s and player_id = %s and event_name in ('yellow','red','goal','assist')",(match_id,player_id,))
            player_result_set= player_cusor.fetchall()
            print("Cầu thủ: "+player_id)
            player_performance=0
            for player_result in player_result_set:
                event_name= player_result[0]
                print(event_name)
                if event_name == "goal":
                    player_performance+=2
                elif event_name == "assist":
                    player_performance+=1
                elif event_name == "yellow":
                    player_performance-=1
                elif event_name == "red":
                    player_performance-=2
            
            per_cur= con.cursor()
            per_cur.execute("select property_value from player_properties where property_name = 'performance' and player_id= %s order by start_time desc limit 1",(player_id,))
            last_per= per_cur.fetchall()[0][0]
            if last_per == None:
                last_per="3"
            print("Phong độ cũ: "+last_per)
            
            new_per= int(last_per)+ player_performance
            if new_per > 5:
                new_per=5
            if new_per < 0:
                new_per=0
            print("Phong độ mới: "+str(new_per))
            print("Time: "+str(match_happen_time))

            try:
                cur = con.cursor()
                cur.execute("insert into player_properties values (%s,%s,%s,%s)",(player_id,match_happen_time,'performance',new_per,))
                con.commit()
            except Exception as e:
                print("ERROR")
                print(e)
    return jsonify({'status':1}),200



@app.route('/nhan/match_result/<clb_name>',methods=['GET'])
def nhan_match_result(clb_name):
    try:
        cur = con.cursor()
        cur.execute("""
        SELECT match_id,clb_home_name, clb_guess_name, match_result FROM Match
        WHERE (clb_home_name=%s OR clb_guess_name=%s) AND NOT match_result='-:-'
         """,(clb_name,clb_name,))
        rows = cur.fetchall()
    except Exception as e:
        print(e)
        return jsonify({'status':0}),200
    colname=[]
    for i in range(0,4):
        colname.append(cur.description[i][0])

    rtlist=[]
    for row in rows:
        dic={}
        for i in range(0,4):
           dic[colname[i]]=row[i]
        rtlist.append(dic)
    js=json.dumps(rtlist,default = myconverter,ensure_ascii=False).encode('utf8')
    return js,200

@app.route('/nhan/upcomming/<clb_name>',methods=['GET'])
def nhan_upcommintt(clb_name):
    try:
        cur = con.cursor()
        cur.execute("""
        SELECT * FROM Match
	    WHERE (clb_home_name= %s OR clb_guess_name= %s) AND match_result='-:-'
         """,(clb_name,clb_name,))
        rows = cur.fetchall()
    except Exception as e:
        print(e)
        return jsonify({'status':0}),200
    colname=[]
    for i in range(0,7):
        colname.append(cur.description[i][0])

    rtlist=[]
    for row in rows:
        dic={}
        for i in range(0,7):
           dic[colname[i]]=row[i]
        rtlist.append(dic)
    js=json.dumps(rtlist,default = myconverter,ensure_ascii=False).encode('utf8')
    return js,200

@app.route('/nhan/lastest_match/<clb_name>',methods=['GET'])
def nhan_lastest_match(clb_name):
    try:
        cur = con.cursor()
        cur.execute("""
        SELECT  * FROM Match
        WHERE (clb_home_name=%s OR clb_guess_name=%s) AND NOT match_result='-:-'
        ORDER BY match_happen_time DESC
        limit 5
         """,(clb_name,clb_name,))
        rows = cur.fetchall()
    except Exception as e:
        print(e)
        return jsonify({'status':0}),200
    colname=[]
    for i in range(0,7):
        colname.append(cur.description[i][0])

    rtlist=[]
    for row in rows:
        dic={}
        for i in range(0,7):
           dic[colname[i]]=row[i]
        rtlist.append(dic)
    js=json.dumps(rtlist,default = myconverter,ensure_ascii=False).encode('utf8')
    return js,200

@app.route('/nhan/user/<email>/<password>',methods=['GET'])
def nhan_user(email,password):
    try:
        cur = con.cursor()
        cur.execute("""
            SELECT * FROM Account 
	        WHERE account_email=%s AND account_password= %s and role != %s
         """,(email,password,'-1',))
        rows = cur.fetchall()
    except Exception as e:
        print(e)
        return jsonify({'status':0}),200
    colname=[]
    for i in range(0,3):
        colname.append(cur.description[i][0])

    rtlist=[]
    for row in rows:
        dic={}
        for i in range(0,3):
           dic[colname[i]]=row[i]
        rtlist.append(dic)
    js=json.dumps(rtlist,default = myconverter,ensure_ascii=False).encode('utf8')
    return js,200

@app.route('/nhan/user/<email>/<password>',methods=['POST'])
def nhan_create_user(email,password):
    try:
        cur = con.cursor()
        cur.execute("""
            SELECT * FROM Account 
	        WHERE account_email=%s
         """,(email,))
        rows = cur.fetchall()
        if len(rows) != 0:
            return jsonify({'status':1}),200
        else:
            cur=con.cursor()
            cur.execute("Insert into Account values (%s,%s,'0')",(email,password,))
            con.commit()
    except Exception as e:
        print(e)
        con.rollback()
        return jsonify({'status':0}),200
    return jsonify({'status':2}),200

@app.route('/nhan/user/',methods=['POST'])
def nhan_user_posts():
    request_data = request.get_json()
    account_email = request_data['account_email']
    account_password = request_data['account_password']
    role= request_data['role']
    try:
        cur = con.cursor()
        cur.execute("""
            SELECT * FROM Account 
	        WHERE account_email=%s and role != %s
         """,(account_email,'-1',))
        rows = cur.fetchall()
        if len(rows) != 0:
            return jsonify({'status':1}),200
        else:
            cur=con.cursor()
            cur.execute("Insert into Account values (%s,%s,%s)",(account_email,account_password,role,))
            con.commit()
    except Exception as e:
        print(e)
        con.rollback()
        return jsonify({'status':0}),200
    return jsonify({'status':2}),200

@app.route('/nhan/user/del/<account_email>',methods=['GET'])
def nhan_user_del(account_email):
    try:
        cur = con.cursor()
        cur.execute("""
            SELECT * FROM Account 
	        WHERE account_email=%s
         """,(account_email,))
        rows = cur.fetchall()
        if len(rows) == 0:
            return jsonify({'status':1}),200
        else:
            cur=con.cursor()
            cur.execute("Update account set role=%s where account_email=%s",('-1',account_email))
            con.commit()
    except Exception as e:
        print(e)
        con.rollback()
        return jsonify({'status':0}),200
    return jsonify({'status':2}),200
     
@app.route('/nhan/user/',methods=['PUT'])
def nhan_update_user():
    request_data = request.get_json()
    account_email = request_data['account_email']
    account_password = request_data['account_password']
    role= request_data['role']
    try:
        cur = con.cursor()
        cur.execute("""
            SELECT * FROM Account 
	        WHERE account_email=%s and role != %s
         """,(account_email,'-1',))
        rows = cur.fetchall()
        if len(rows) == 0:
            return jsonify({'status':1}),200
        else:
            cur=con.cursor()
            cur.execute("update account set account_password=%s, role=%s where account_email=%s",(account_password,role,account_email,))
            con.commit()
    except Exception as e:
        print(e)
        con.rollback()
        return jsonify({'status':0}),200
    return jsonify({'status':2}),200
      
@app.route('/nhan/users',methods=['GET'])
def nhan_get_all_user():
    try:
        cur = con.cursor()
        cur.execute("""
            select *
            from Account
            where role != %s
            order by account_email asc
         """,('-1',))
        rows = cur.fetchall()
    except Exception as e:
        print(e)
        return jsonify({'status':0}),200
    colname=[]
    for i in range(0,3):
        colname.append(cur.description[i][0])

    rtlist=[]
    for row in rows:
        dic={}
        for i in range(0,3):
           dic[colname[i]]=row[i]
        rtlist.append(dic)
    js=json.dumps(rtlist,default = myconverter,ensure_ascii=False).encode('utf8')
    return js,200

@app.route('/nhan/analysis',methods=['GET'])
def nhan_analysis():
    try:
        cur = con.cursor()
        cur.execute("""
            select * from
            (select count(account_email)as count_account from account)as account,
            (select count(post_id)as count_post from post) as post,
            (select count(match_id)as count_match from match)as match
         """,)
        rows = cur.fetchall()
    except Exception as e:
        print(e)
        return jsonify({'count_account':0,'count_post':0,'count_match':0}),200
    colname=[]
    for i in range(0,3):
        colname.append(cur.description[i][0])

    rtlist=[]
    for row in rows:
        dic={}
        for i in range(0,3):
           dic[colname[i]]=row[i]
        rtlist.append(dic)
    js=json.dumps(rtlist,default = myconverter,ensure_ascii=False).encode('utf8')
    return js,200


@app.route('/khai/getNgayDaDau/<date>',methods=['GET'])
def khai_ngay_da_dau(date):
    try:
        cur = con.cursor()
        cur.execute("""
            SELECT d.date_match
            FROM(SELECT DISTINCT DATE(match_happen_time) as date_match FROM Match
                WHERE match_happen_time <= %s) d
            ORDER BY d.date_match DESC
            limit 10
         """,(date,))
        rows = cur.fetchall()
    except Exception as e:
        print(e)
        return jsonify({'status':0}),200

    colname=[]
    for i in range(0,1):
        colname.append(cur.description[i][0])

    rtlist=[]
    for row in rows:
        dic={}
        for i in range(0,1):
            dic[colname[i]]=str(row[i])
        rtlist.append(dic)
    js=json.dumps(rtlist)
    return js,200

@app.route('/khai/getNgaySapDau/<date>',methods=['GET'])
def khai_getngaysapdau(date):
    try:
        cur = con.cursor()
        cur.execute("""
            SELECT d.date_match
            FROM(SELECT DISTINCT DATE(match_happen_time) as date_match FROM Match
                WHERE match_happen_time >= %s) d
            ORDER BY d.date_match ASC
            limit 10
         """,(date,))
        rows = cur.fetchall()
    except Exception as e:
        print(e)
        return jsonify({'status':0}),200

    colname=[]
    for i in range(0,1):
        colname.append(cur.description[i][0])

    rtlist=[]
    for row in rows:
        dic={}
        for i in range(0,1):
            dic[colname[i]]=str(row[i])
        rtlist.append(dic)
    js=json.dumps(rtlist)
    return js,200

@app.route('/khai/getTranDau/<date>',methods=['GET'])
def khai_gettrandau(date):
    try:
        cur = con.cursor()
        cur.execute("""
            SELECT * 
            From Match 
            WhERE DATE(match_happen_time) = %s
            ORDER BY match_happen_time ASC
         """,(date,))
        rows = cur.fetchall()
    except Exception as e:
        print(e)
        return jsonify({'status':0}),200

    colname=[]
    for i in range(0,7):
        colname.append(cur.description[i][0])

    rtlist=[]
    for row in rows:
        dic={}
        for i in range(0,7):
            dic[colname[i]]=str(row[i])
        rtlist.append(dic)
    js=json.dumps(rtlist,default = myconverter,ensure_ascii=False).encode('utf8')
    return js,200

@app.route('/khai/getbaiviet/<email>/<date>',methods=['GET'])
def khai_getbaiviet_date_email(email,date):
    try:
        cur = con.cursor()
        cur.execute("""
            SELECT * 
            From post
            WhERE DATE(post_create_time) = %s and post_create_by =%s
            ORDER BY post_view desc
         """,(date,email,))
        rows = cur.fetchall()
    except Exception as e:
        print(e)
        return jsonify({'status':0}),200

    colname=[]
    for i in range(0,8):
        colname.append(cur.description[i][0])

    rtlist=[]
    for row in rows:
        dic={}
        for i in range(0,8):
            dic[colname[i]]=str(row[i])
        rtlist.append(dic)
    js=json.dumps(rtlist,default = myconverter,ensure_ascii=False).encode('utf8')
    return js,200



@app.route('/khai/add/post',methods=['POST'])
def khai_add_post():
    request_data = request.get_json()
    post_title = request_data['post_title']
    post_content = request_data['post_content']
    post_img= request_data['post_img']
    
    
    if post_img != None:
        cur=con.cursor()
        cur.execute("select post_id from post order by post_id desc limit 1")
        rows = cur.fetchall()
        img_base64_str= post_img
        img_name= int(rows[0][0])+ 1
        img_decode_base64 = base64.b64decode(img_base64_str)
        storage.child("/img/"+str(img_name)).put(img_decode_base64)
        img_url= storage.child("/img/mobile"+str(img_name)).get_url(None)
    else:
        img_url=""

    now = datetime.datetime.now()
    post_create_time=now.strftime("%Y-%m-%d %H:%M:%S")
    post_create_by= request_data['post_create_by']
    try:
        cur=con.cursor()
        cur.execute("""
            insert into post (post_title,post_content,post_img,post_create_time,post_create_by,
                    post_status,post_view)
            values (%s,%s,%s,%s,%s,%s,%s)
        """,(post_title,post_content,img_url,post_create_time,post_create_by,1,0))
        con.commit()
    except Exception as e:
        print(e)
        con.rollback()
        return jsonify({'status':str(e)}),200
    return jsonify({'status':2}),200

@app.route('/khai/edit/post/<post_id>',methods=['POST'])
def khai_edit_post(post_id):
    request_data = request.get_json()
    post_title = request_data['post_title']
    post_content = request_data['post_content']
    post_img= request_data['post_img']
    img_base64_str= post_img

    img_name= post_id
    img_decode_base64 = base64.b64decode(img_base64_str)
    storage.child("/img/"+str(img_name)).put(img_decode_base64)
    img_url= storage.child("/img/mobile"+str(img_name)).get_url(None)

    now = datetime.datetime.now()
    post_create_time=now.strftime("%Y-%m-%d %H:%M:%S")
    post_create_by= request_data['post_create_by']
    try:
        cur=con.cursor()
        cur.execute("update post set post_title= %s, post_content=%s, post_img=%s where post_id =%s",(post_title,post_content,img_url,post_id,))
        con.commit()
    except Exception as e:
        print(e)
        con.rollback()
        return jsonify({'status':0}),200
    return jsonify({'status':2}),200

@app.route('/khai/del/post/<post_id>',methods=['POST'])
def khai_del_post(post_id):
    try:
        cur=con.cursor()
        cur.execute("update post set post_status= %s where post_id =%s",('-1',post_id,))
        con.commit()
    except Exception as e:
        print(e)
        con.rollback()
        return jsonify({'status':0}),200
    return jsonify({'status':2}),200

@app.route('/khai/getbaiviet/<account_email>',methods=['GET'])
def khai_getbaiviet(account_email):
    try:
        cur = con.cursor()
        cur.execute("""
            select *
            from post
            where post_create_by=%s
         """,(account_email,))
        rows = cur.fetchall()
    except Exception as e:
        print(e)
        return jsonify({'status':0}),200

    colname=[]
    for i in range(0,8):
        colname.append(cur.description[i][0])

    rtlist=[]
    for row in rows:
        dic={}
        for i in range(0,8):
            dic[colname[i]]=str(row[i])
        rtlist.append(dic)
    js=json.dumps(rtlist,default = myconverter,ensure_ascii=False).encode('utf8')
    return js,200

@app.route('/manem/thongtincauthu/<player_id>',methods=['GET'])
def manem_thongtincauthu(player_id):
    try:
        cur = con.cursor()
        cur.execute("""
            select player.*, clb_name, start_time, end_time, transfer_money,
                main, sub, p_out, p_in, assist, yellow, red, p_value, p_position, performance, p_number,goal
            from player
            left join player_clubs on player.player_id= player_clubs.player_id
            left join (
                select player_id, 
                        sum(case when (event_name='main') then 1 else 0 end) as main,
                        sum(case when (event_name='sub') then 1 else 0 end) as sub,
                        sum(case when (event_name='out') then 1 else 0 end) as p_out,
                        sum(case when (event_name='in') then 1 else 0 end) as p_in,
                        sum(case when (event_name='assist') then 1 else 0 end) as assist,	
                        sum(case when (event_name='goal') then 1 else 0 end) as goal,
                        sum(case when (event_name='yellow') then 1 else 0 end) as yellow,
                        sum(case when (event_name='red') then 1 else 0 end) as red
                from player_match_event
                group by player_id) as events
            on player.player_id = events.player_id
            inner join (
                select player_id,
                    max(case when (property_name='value') then property_value else NULL end) as p_value,
                    max(case when (property_name='position') then property_value else NULL end) as p_position,
                    max(case when (property_name='performance') then property_value else NULL end) as performance,
                    max(case when (property_name='number') then property_value else NULL end) as p_number
                from(
                    select *
                    from(
                        select Player_Properties.player_id,Player_Properties.property_name,Player_Properties.property_value
                        from Player_Properties
                        inner join(
                            select player_id,property_name, max(start_time) as start_time
                            from Player_Properties
                            group by player_id, property_name
                        )as max_date
                        on max_date.player_id=Player_Properties.player_id and max_date.start_time=Player_Properties.start_time
                        and max_date.property_name= Player_Properties.property_name
                    ) as max_date_player_properties
                )as temp
                group by temp.player_id
                order by temp.player_id
            ) as player_property
            on player_property.player_id = player.player_id
            where player.player_id = %s
        """,(player_id,))
        rows = cur.fetchall()
    except:
        return jsonify({'status':0}),200
    colname=[]
    for i in range(0,24):
        colname.append(cur.description[i][0])

    rtlist=[]
    for row in rows:
        dic={}
        for i in range(0,24):
            if colname[i] == 'player_birthday':
                dic[colname[i]]=str(row[i])
            else:
                dic[colname[i]]=row[i]
        rtlist.append(dic)
    js=json.dumps(rtlist,default = myconverter,ensure_ascii=False).encode('utf8')
    # js=json.dumps(rtlist)
    return js,200


@app.route('/manem/allperformance/<player_id>',methods=['GET'])
def manem_allperformance(player_id):
    try:
        cur = con.cursor()
        cur.execute("""
            select *
            from player_properties
            where property_name = 'performance'
            and player_id = %s
            order by start_time asc
        """,(player_id,))
        rows = cur.fetchall()
    except:
        return jsonify({'status':0}),200
    colname=[]
    for i in range(0,4):
        colname.append(cur.description[i][0])

    rtlist=[]
    for row in rows:
        dic={}
        for i in range(0,4):
           dic[colname[i]]=row[i]
        rtlist.append(dic)
    js=json.dumps(rtlist,default = myconverter,ensure_ascii=False).encode('utf8')
    return js,200

@app.route('/manem/listcauthu/',methods=['GET'])
def manem_listcauthu():
    try:
        cur = con.cursor()
        cur.execute("""
            select player.player_id, player.player_international_name, player.player_img_url, rs_player_properties.number
            from player
            inner join(
                select player_id,
                    max(case when (property_name='number') then property_value else NULL end) as number
                from(
                    select *
                    from(
                        select Player_Properties.player_id,Player_Properties.property_name,Player_Properties.property_value
                        from Player_Properties
                        inner join(
                            select player_id,property_name, max(start_time) as start_time
                            from Player_Properties
                            group by player_id, property_name
                        )as max_date
                        on max_date.player_id=Player_Properties.player_id and max_date.start_time=Player_Properties.start_time
                        and max_date.property_name= Player_Properties.property_name
                    ) as max_date_player_properties
                )as temp
                group by temp.player_id
                order by temp.player_id
            )as rs_player_properties
            on rs_player_properties.player_id= player.player_id
        """)
        rows = cur.fetchall()
    except:
        return jsonify({'status':0}),200
    colname=[]
    for i in range(0,4):
        colname.append(cur.description[i][0])

    rtlist=[]
    for row in rows:
        dic={}
        for i in range(0,4):
           dic[colname[i]]=row[i]
        rtlist.append(dic)
    js=json.dumps(rtlist,default = myconverter,ensure_ascii=False).encode('utf8')
    return js,200


#test
if __name__ == '__main__':
    app.run()