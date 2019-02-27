#!/usr/bin/env python3
#-*- coding:utf-8 -*-

__author__ = 'sanjinmr'

'url handlers'

from coroweb import get

from models import User

@get('/')
def index(request):
	users = yield from User.findAll()
	return {
		'__template__': 'test.html',
		'users': users
	}