#!/usr/bin/env python3
#-*-coding:utf-8-*-

__author__ = 'sanjinmr'

import logging; logging.basicConfig(level=logging.INFO)

import asyncio,os,json,time

from datetime import datetime

from aiohttp import web

from aiohttp import web_runner


def index(request):
	return web.Response(body=b'<h1>Awesome<h1>', content_type='text/html')

@asyncio.coroutine
def init(loop):
	app = web.Application(loop=loop)
	#app = web_runner.AppRunner(app=app).app()
	app.router.add_route('GET', '/', index)
	srv = yield from loop.create_server(app.make_handler(), '127.0.0.1', 9000)
	logging.info('server started at http://127.0.0.1:90000...')
	return srv

loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()