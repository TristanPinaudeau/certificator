import sys
import json

from flask import Flask
from flask_simpleldap import LDAP
from flask_jwt import JWT, jwt_required, current_identity
from werkzeug.security import safe_str_cmp

class User(object):
    def __init__(self, username, groups):
        self.username = username
        self.groups = groups

    def __str__(self):
        return "username : {}\ngroups : {}".format(self.username, self.groups)

def authenticate(username, password):
    user = ldap.bind_user(username, password)
    if user and password != '':
        print(json.dumps(ldap.get_object_details(user=username)))
        return user

def identity(payload):
    user_name = payload['identity']
    user_groups = ldap.get_user_groups(user=user_name)
    return User(user_name, user_groups)

app = Flask(__name__)
app.debug = True
app.secret_key = "S3CR3T"
app.config['SECRET_KEY'] = 'S3CR3T'
app.config['LDAP_HOST'] = 'ad-crypto.epsi.intra'
app.config['LDAP_BASE_DN'] = 'cn=Users,dc=epsi,dc=intra'
app.config['LDAP_USERNAME'] = 'cn=Administrator,cn=Users,dc=epsi,dc=intra'
app.config['LDAP_PASSWORD'] = 'P@ssw0rd'
app.config['LDAP_USER_OBJECT_FILTER'] = '(sAMAccountName=%s)'

ldap = LDAP(app)
jwt = JWT(app, authenticate, identity)

@app.route("/")
@jwt_required()
def index():
    return "%s" % current_identity

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(sys.argv[1]), debug=True)
