import datetime
import uuid

from sqlalchemy.dialects.postgresql import UUID

from dbs.db import db, metadata

roles_related = db.Table(
    'roles_related',
    metadata,
    db.Column('profile_id', UUID(as_uuid=True), db.ForeignKey('profiles.id'), primary_key=True),
    db.Column('role_id', UUID(as_uuid=True), db.ForeignKey('roles.id'), primary_key=True)
)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    login = db.Column(db.String(40), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f'<User {self.login}>'


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    role = db.Column(db.String(100), default='user', unique=True, nullable=False)

    def __repr__(self):
        return f'{self.role}'


class Profile(db.Model):
    __tablename__ = 'profiles'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id", ondelete='CASCADE'), nullable=False)
    first_name = db.Column(db.String(128))
    last_name = db.Column(db.String(128))
    role = db.relationship('Role', secondary=roles_related, lazy='subquery',
                           backref=db.backref('profiles', lazy=True))
    bio = db.Column(db.String(10000))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def add_role(self, role):
        self.role.append(role)

    def __repr__(self):
        return f'<Profile user {self.user_id}>'


class JwtRefresh(db.Model):
    __tablename__ = 'jwt'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id", ondelete='CASCADE'), nullable=False)
    refresh_token = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f'<JWT refresh token for user {self.user_id}>'


class Login(db.Model):
    __tablename__ = 'logins'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id", ondelete='CASCADE'), nullable=False)
    info = db.Column(db.String)
    status = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f'<Login user {self.user_id}>'


class SocialAccount(db.Model):
    __tablename__ = 'social_account'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    user = db.relationship(User, backref=db.backref('social_accounts', lazy=True))

    social_id = db.Column(db.Text, nullable=False)
    social_name = db.Column(db.Text, nullable=False)

    __table_args__ = (db.UniqueConstraint('social_id', 'social_name', name='social_pk'),)

    def __repr__(self):
        return f'<SocialAccount {self.social_name}:{self.user_id}>'

