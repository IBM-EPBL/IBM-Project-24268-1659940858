from flask import Flask, redirect, url_for, request, render_template, session
import ibm_db
from flask_session import Session
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from time import gmtime, strftime
import hmac, base64, struct, hashlib, time

conn = None
secret = "IUCXICYJFABTTOE3WOXUTC2HZ5MDWWSR"
text = None
limtext = None
inctxt = None

app=Flask(__name__,static_folder="static")
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

def get_hotp_token(secret, intervals_no):
    key = base64.b32decode(secret, True)
    #decoding our key
    msg = struct.pack(">Q", intervals_no)
    #conversions between Python values and C structs represente
    h = hmac.new(key, msg, hashlib.sha1).digest()
    o = o = h[19] & 15
    #Generate a hash using both of these. Hashing algorithm is HMAC
    h = (struct.unpack(">I", h[o:o+4])[0] & 0x7fffffff) % 1000000
    #unpacking
    return h

def get_totp_token(secret):
    #ensuring to give the same otp for 30 seconds
    x =str(get_hotp_token(secret,intervals_no=int(time.time())//30))
    #adding 0 in the beginning till OTP has 6 digits
    while len(x)!=6:
        x+='0'
    return x

def mail(msg,value):
    message = Mail(
    from_email='1912019@nec.edu.in',
    to_emails=session["email"],
    subject=msg,
    html_content='<strong>'+value+'</strong>')
    sg = SendGridAPIClient(os.environ.get('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'))
    response = sg.send(message)
    print(response.status_code)
    print(response.body)
    print(response.headers)

def connect():
    global conn 
    conn = ibm_db.connect("DATABASE=bludb;HOSTNAME=fbd88901-ebdb-4a4f-a32e-9822b9fb237b.c1ogj3sd0tgtu0lqde00.databases.appdomain.cloud;PORT=32731;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=dxy32089;PWD=75PDKFFPQjkfYtNz",'','')

@app.route('/2fa', methods = ['GET', 'POST'])
def auth():
    otp = int(request.form.get("otp"))


@app.route('/')
def base():
    session["email"] = None
    session["username"] = None
    return render_template('login.html',msg='None')

@app.route('/signup', methods = ['GET', 'POST'])
def signup():
    if request.method == 'POST':
        if(conn == None):
            connect()
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        phno = request.form.get('phno')
        name = request.form.get('name')
        stmt = ibm_db.exec_immediate(conn, "insert into login(username,password,name,phonenumber,email) values ('"+username+"', '"+password+"', '"+name+"', "+phno+", '"+email+"');")
        if(ibm_db.num_rows(stmt)>0):
            session["msg"] = "signup"
            mail("App signup","Thankyou for signing up in our app")
            return render_template("index.html",msg='success')
        else:
            session["msg"] = "signup"
            return render_template("signup.html",msg='error')
    else:
        return render_template("signup.html", msg='None')


def limitcheck(expence,limit):
    global limtext
    percent = int(limit) * (int(expence)/100)
    if(percent < 90):
        session["limitcolor"] = "green"
        limtext = "success"
    elif(percent >= 90 and percent >= 100):
        mail("App Expence limit","Expence nearing limit")
        session["limitcolor"] = "orange"
        limtext = "warning"
    else:
        mail("App Expence limit","Your expence exceeded your limit")
        session["limitcolor"] = "red"
        limtext = "danger"
    return percent

def recordupdate():
    stmt = ibm_db.exec_immediate(conn, "Select * from records a inner join category b on a.category=b.categoryid where a.email = '"+session["email"]+"';")
    result = ibm_db.fetch_assoc(stmt)
    recordsExpence = []
    recordsTransfer = []
    recordsIncome = []
    excnt = 1
    incnt = 1
    trcnt = 1
    while result!=False:
    #     record.append([result["AMOUNT"],result["EMAIL"],result["TYPE"]])
        if(result["TYPE"] == "Expence"):
            recordsExpence.append([excnt,result["TO_ACC"],result["AMOUNT"],result["NAME"],result["UPDATION_DATE"]])
            excnt+=1
        elif(result["TYPE"] == "Transfer"):
            recordsTransfer.append([trcnt,result["TO_ACC"],result["AMOUNT"],result["NAME"],result["UPDATION_DATE"]])
            trcnt+=1
        else:
            recordsIncome.append([incnt,result["TO_ACC"],result["AMOUNT"],result["NAME"],result["UPDATION_DATE"]])
            incnt+=1

            
        result = ibm_db.fetch_assoc(stmt)
    session["recordsExpence"] = recordsExpence
    session["recordsTransfer"] = recordsTransfer
    session["recordsIncome"] = recordsIncome

def categoryUpdate():
    stmt = ibm_db.exec_immediate(conn, "Select * from category where a.email = '"+session["email"]+"';")
    result = ibm_db.fetch_assoc(stmt)
    category = []
    cnt = 1
    while result!=False:
        category.append([cnt,result["NAME"]])
        result = ibm_db.fetch_assoc(stmt)
    session["category"] = category


@app.route('/redirect')
def redirect():
    session["username"]     =   None
    session["password"]     =   None
    session["email"]        =   None
    session["phonenumber"]  =   None
    session["balance"]      =   None
    session["limit"]        =   None
    session["expence"]      =   None
    session["transfer"]     =   None
    session["income"]       =   None
    return render_template('login.html')

@app.route('/login', methods = ['POST', 'GET'])
def login():
    if request.method == 'POST':
        global text
        global limtext
        global inctxt
        username = request.form.get('email')
        password = request.form.get('password')
        if(conn == None):
            connect()
        stmt = ibm_db.exec_immediate(conn, "Select * from login where email = '"+username+"' and password = '"+password+"' ")
        result = ibm_db.fetch_assoc(stmt)
        if(result):
            session["username"] = result["USERNAME"]
            session["password"] = result["PASSWORD"]
            session["email"] = result["EMAIL"]
            session["phonenumber"] = result["PHONENUMBER"]
            session["balance"] = result["BALANCE"]
            session["limit"] = result["LIMIT"]
            session["expence"] = result["EXPENCE"]
            session["transfer"] = result["TRANSFER"]
            session["income"] = result["INCOME"]
            session["msg"] = "Login"
            sesbal(int(session["balance"]))
            percent = limitcheck(result["EXPENCE"],result["LIMIT"])
            session["percent"] = percent
            if(percent > 90):
                limtext = "danger"
            elif(percent >= 90 and percent >= 100):
                limtext = "warning"
            else:
                limtext = "danger"
            recordupdate()
            sesinc(int(result["INCOME"]))
            return render_template('index.html',msg='success',text=text,limtext=limtext,inctxt=inctxt)
        else:
            session["msg"] = "Login"
            return render_template('login.html',msg='error')
    else:
        return render_template('login.html')

def sesinc(income):
    global inctxt
    if(income == 0):
                inctxt = "danger"
    else:
        inctxt = "success"

def sesbal(balance):
    global text
    global limtext
    session["balance"] = balance
    if(int(balance)<490):
        text = "danger"
    elif(int(balance)>=490 and int(balance)<= 500):
        text = "warning"
    else:
        text = "success"


@app.route("/changebalance", methods = ['POST','GET'])
def changebal():
    global text
    global limtext
    global inctxt
    if request.method == 'POST':
        balance = request.form.get("balance")
        if(balance == ""):
            session["msg"] = "0 not acceptable"
            return render_template("index.html",msg='error',active='home')
        print(balance)
        stmt = ibm_db.exec_immediate(conn, "update login set balance='"+balance+"' where email = '"+session["email"]+"' and username = '"+session["username"]+"';")
        if(ibm_db.num_rows(stmt)>0):
            session["msg"] = "change balance"
            sesbal(balance)
            return render_template("index.html",msg='success',text=text,limtext=limtext,inctxt=inctxt)
        else:
            session["msg"] = "change balance"
            return render_template("index.html",msg='error',text=text,limtext=limtext,inctxt=inctxt)

@app.route("/addrecord",method=['POST','GET'])
def addrecord():
    if request.method == 'POST':
        global text
        global limtext
        sendto = request.form.get("to_acc")
        amount = request.form.get("amount")
        catetgory = request.form.get("category")
        type = request.form.get("type")
        stmt = ibm_db.exec_immediate(conn, "insert into record(email,to_acc,amount,category,type) values ('"+session["email"]+"', '"+sendto+"', "+amount+", "+catetgory+", '"+type+"');")
        if(ibm_db.num_rows(stmt)>0):
            t = ""
            if(type == "Transfer"):
                t = "transfer"
            elif(type=="Expence"):
                t = "expence"
            else:
                t = "income"
            stmt = ibm_db.exec_immediate(conn, "update login set balance = balance - "+amount+" , "+t+" = "+t+" + "+amount+" where email = '"+session["email"]+"' and username = '"+session["username"]+"';")
            session["msg"] = "adding records"
            return render_template("index.html",msg='success',text=text,limtext=limtext,inctxt=inctxt)
        else:
            session["msg"] = "adding records"
            return render_template("index.html",msg='error',text=text,limtext=limtext,inctxt=inctxt)


@app.route("/changelimit", methods = ['POST','GET'])
def changelim():
    if request.method == 'POST':
        global text
        global limtext
        limit = request.form.get("limit")
        if(limit == ""):
            session["msg"] = "0 not acceptable"
            return render_template("index.html",msg='error',text='danger',active='home')
        print(limit)
        stmt = ibm_db.exec_immediate(conn, "update login set limit='"+limit+"' where email = '"+session["email"]+"' and username = '"+session["username"]+"';")
        if(ibm_db.num_rows(stmt)>0):
            session["msg"] = "Limit Set"
            session["limit"] = limit
            percent = limitcheck(session["expence"], session["limit"])
            if(percent > 100):
                limtext = "danger"
            elif(percent >= 90 and percent <= 100):
                limtext = "warning"
            else:
                limtext = "success"
            return render_template("index.html",msg='success',text=text,limtext=limtext,inctxt=inctxt,active='home')
        else:
            session["msg"] = "change balance"
            return render_template("index.html",msg='error',text=text,limtext=limtext,inctxt=inctxt,active='home')

if __name__=='__main__':
    app.run(host='0.0.0.0',port=5000)