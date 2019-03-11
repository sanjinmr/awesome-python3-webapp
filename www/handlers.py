#!/usr/bin/env python3
#-*- coding:utf-8 -*-

__author__ = 'sanjinmr'

'url handlers'

from coroweb import get

from models import User, Blog

import time

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
