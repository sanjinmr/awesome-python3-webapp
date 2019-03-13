#!/usr/bin/env python3
#-*- coding:utf-8 -*-

__author__ = 'sanjinmr'

'url handlers'

from coroweb import get

from models import User, Blog, next_id

import time

from apis import Page, APIValueError


COOKIE_NAME = 'awesession'
_COOKIE_KEY = configs.session.secret

def get_page_index(page_str):
	p = 1
	try:
		p = int(page_str)
	except ValueError as e:
		pass
	if p < 1:
		p = 1
	return p
	
def user2cookie(uesr, max_age):
	'''
	Generate cookie str by user.
	'''
	#build cookie string by: id-express-sha1
	expires = str(int(time.time() + max_age))
	s = '%s-%s-%s-%s' % (user.id, user.passwd, expires, _COOKIE_KEY)
	L = [user.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
	return '-'.join(L)
	
	
@get('/')
async def index(request):
	users = await User.findAll()
	summary = 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
	blogs = [
		Blog(id='1', name='Test Blog 1', summary=summary, created_at=time.time()-120),
		Blog(id='2', name='Test Blog 2', summary=summary, created_at=time.time()-3600),
		Blog(id='3', name='Test Blog 3', summary=summary, created_at=time.time()-7200)
	]
	return {
		'__template__': 'blogs.html',
		'users': users,
		'blogs': blogs
	}

@get('/api/users')
async def api_get_users(*, page = '1'):
	page_index = get_page_index(page)
	num = await User.findNumber('count(id)')
	p = Page(num, page_index)
	if num == 0:
		return dict(page = p, users = ())
	users = await User.findAll(orderBy = 'created_at desc', limit = (p.offset, p.limit))
	for u in users:
		u.passwd = '******'
	return dict(page = p, users = users)
	
_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')

@POST('/api/users')
def api_register_user(*, email, name, passwd):
	if not name or not name.strip():
		raise APIValueError('name')
	if not email or not _RE_EMAIL.match(email):
		raise APIValueError('email')
	if not passwd or not _RE_SHA1.match(passwd):
		raise APIValueError('passwd')
	users = await User.findAll('email=?', [email])
	if len(users) > 0:
		raise APIError('register:failed', 'email', 'Email is already in use.')
	uid = next_id()
	sha1_passwd = '%s:%s' % (uid, passwd)
	user = User(id=uid, name=name.strip(), email=email)
	await user.save()
	# make session cookie
	r = web.Response()
	r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
	user.passwd = '******'
	r.content_type = 'application/json'
	r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
	return r
	
	
	
