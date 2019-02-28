#!/usr/bin/env python3
#-*- coding:utf-8 -*-

__author__ = 'sanjinmr'

'url handlers'

from coroweb import get

from models import User

@get('/')
async def index(request):
	users = await User.findAll()
	return {
		'__template__': 'test.html',
		'users': users
	}
