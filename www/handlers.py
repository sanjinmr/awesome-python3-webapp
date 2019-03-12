#!/usr/bin/env python3
#-*- coding:utf-8 -*-

__author__ = 'sanjinmr'

'url handlers'

from coroweb import get

from models import User, Blog

import time

from apis import Page, APIValueError

def get_page_index(page_str):
	p = 1
	try:
		p = int(page_str)
	except ValueError as e:
		pass
	if p < 1:
		p = 1
	return p
	

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