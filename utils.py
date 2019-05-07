import os
import OpenSSL.crypto

from flask import Flask
from flask_simpleldap import LDAP
from flask_jwt import JWT
from user import User, CertState
from OpenSSL.crypto import FILETYPE_PEM


def absolute_path(relative_path):
    current_dir = os.path.dirname(__file__)
    return os.path.join(current_dir, relative_path)

def create_file_tree():
    dirs = [
        'certificates',
        'certificates/pending',
        'certificates/revoked',
        'certificates/issued'
    ]
    for relative_path in dirs:
        directory = absolute_path(relative_path)
        if not os.path.exists(directory):
            os.makedirs(directory)

def init_flask():
    app = Flask(__name__)
    app.debug = True
    app.secret_key = "S3CR3T"
    create_file_tree()
    return app

def init_ldap(app):
    app.config['LDAP_HOST'] = 'ad-crypto.epsi.intra'
    app.config['LDAP_BASE_DN'] = 'cn=Users,dc=epsi,dc=intra'
    app.config['LDAP_USERNAME'] = 'cn=Administrator,cn=Users,dc=epsi,dc=intra'
    app.config['LDAP_PASSWORD'] = 'P@ssw0rd'
    app.config['LDAP_USER_OBJECT_FILTER'] = '(sAMAccountName=%s)'
    return LDAP(app)

def init_jwt(app, ldap):

    def authenticate(username, password):
        binded = ldap.bind_user(username, password)
        if binded and password != '':
            user_groups = ldap.get_user_groups(user=username)
            user = User(username, user_groups)
            return user

    def identity(payload):
        user_name = payload['identity']
        user_groups = ldap.get_user_groups(user=user_name)
        return User(user_name, user_groups)

    return JWT(app, authenticate, identity)


def listfiles(path):
    cert_dir = absolute_path(path)
    with os.scandir(cert_dir) as directory:
        files = [entry.name for entry in directory if entry.is_file()]
        return files if files is not None else []


def list_certificates(state=None):
    if CertState.PENDING.value == state:
        return listfiles('certificates/pending')
    elif CertState.ISSUED.value == state:
        return listfiles('certificates/issued')
    elif CertState.REVOKED.value == state:
        return listfiles('certificates/revoked')
    else:
        return listfiles('certificates/pending') \
             + listfiles('certificates/issued') \
             + listfiles('certificates/revoked')

def detail_certificate(cert_id):
    csr_file = open("certificates/pending/{}.csr".format(cert_id), "r")
    file_content = f.read()
    req = OpenSSL.crypto.load_certificate_request(FILETYPE_PEM, csrContent)
    key = req.get_pubkey()
    subject = req.get_subject()
    algorithm = 'RSA' if key.type() == OpenSSL.crypto.TYPE_RSA else 'DSA'
    size = key.bits()

    for key, val in dict(subject.get_components()).items():
        key, val = key.decode(), val.decode()
        common_name       = val if key == "CN"   else None
        organization      = val if key == "O"    else None
        organization_unit = val if key == "OU"   else None
        city              = val if key == "L"    else None
        state             = val if key == "S"    else None
        country           = val if key == "C"    else None
        mail              = val if key == "MAIL" else None

    return {
        "algorithm": algorithm,
        "size": size,
        "details": {
            "CN": common_name,
            "O": organization,
            "OU": organization_unit,
            "L": city,
            "S": state,
            "C": country,
            "MAIL": mail,
        }
    }

