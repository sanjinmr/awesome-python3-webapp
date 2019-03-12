#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'sanjin'

import asyncio, os, inspect, logging, functools

from urllib import parse

from aiohttp import web

from apis import APIError


def get(path):
	'''
	Define decorator @get('/path')
	'''
	def decorator(func):
		@functools.wraps(func)
		def wrapper(*args, **kw):
			return func(*args, **kw)
		wrapper.__method__ = 'GET'
		wrapper.__route__ = path
		return wrapper
	return decorator


def post(path):
	'''
	Define decorator @post('/path')
	'''
	def decorator(func):
		@functools.wraps(func)
		def wrapper(*args, **kw):
			return func(*args, **kw)
		wrapper.__method__ = 'POST'
		wrapper.__route__ = path
		return wrapper
	return decorator

#获取必不可少的参数
#即获取函数的不可变，且没有默认值的关键字参数
def get_required_kw_args(fn):
	args = []
	params = inspect.signature(fn).parameters
	for name, param in params.items():
		#不可变且没有默认值
		if param.kind == inspect.Parameter.KEYWORD_ONLY and param.default == inspect.Parameter.empty:
			args.append(name)
	return tuple(args)

#获取不可变关键字参数（无论是否有默认值）
def get_named_kw_args(fn):
	args = []
	params = inspect.signature(fn).parameters
	for name, param in params.items():
		if param.kind == inspect.Parameter.KEYWORD_ONLY:
			args.append(name)
	return tuple(args)

#判断函数是否含有不可变关键字参数
def has_named_kw_args(fn):
	params = inspect.signature(fn).parameters
	for name, param in params.items():
		if param.kind == inspect.Parameter.KEYWORD_ONLY:
			return True

#判断函数是否含有可变关键字参数
def has_var_kw_args(fn):
	params = inspect.signature(fn).parameters
	for name, param in params.items():
		if param.kind == inspect.Parameter.VAR_KEYWORD:
			return True

#判断函数是否有名为request的参数，如果有，是否为不可变关键字参数，
#如果不是，则提示request参数比如为函数的最后一个参数
def has_request_args(fn):
	sig = inspect.signature(fn)
	params = sig.parameters
	found = False
	for name, param in params.items():
		if name == 'request':
			found = True
			continue
		if found and (
		param.kind != inspect.Parameter.VAR_POSITIONAL and
		param.kind != inspect.Parameter.VAR_KEYWORD):
			raise ValueError('request parameter must be the last named parameter in function: %s%s' % (fn, __name__, str(sig)))
	return found


#处理request的函数，其实是转换url处理函数的一个函数
#equestHandler目的就是从URL函数中分析其需要接收的参数，
#从request中获取必要的参数，调用URL函数，然后把结果转换为web.Response对象
class RequestHandler(object):

	#构造函数初始化时调用
	#RequestHandler在add_route的时候调用：
	#app.router.add_route(method, path, RequestHandler(func))
	def __init__(self, app, fn):
		self._app = app
		self._func = fn
		self._has_request_arg = has_request_args(fn)
		self._has_var_kw_arg = has_var_kw_args(fn)
		self._has_named_kw_args = has_named_kw_args(fn)
		self._named_kw_args = get_named_kw_args(fn)
		self._required_kw_args = get_required_kw_args(fn)

	async def find_post_kw(self, request, kw):

		if not request.content_type:
			return web.HttpBadReqeust('Missing Content-Type')
		ct = request.content_type.lower()

		if ct.startswith('applicatiion/json'):
			params = await request.json()
			if not isinstance(params, dict):
				return web.HTTPBadRequest('JSON body must be object.')
			kw = params

		elif ct.startswith('application/x-www-form-urlencoded') or ct.startswith('multipart/form-data'):
			params = await request.post()
			kw = dict(**params)

		else:
			return web.HTTPBadRequest('Unsupportd Content-Type: %s')

		return kw

	def find_get_kw(self, request, kw):
		qs = request.query_string
		if qs:
			kw = dict()
			for k, v in parse.parse_qs(qs, True).items():
				kw[k] = v[0]

		return kw
		
	#定义该类的实例可以作为一个函数被调用，调用的函数参数，如__call__描述
	#该函数在factorys的response_factory调用:
	#r = await handler(request)
	async def __call__(self, request):
		kw = None
		#检查POST参数和GET参数
		#如果fn函数有可变/不可变关键字参数或有request参数
		if self._has_var_kw_arg or self._has_named_kw_args or self._required_kw_args:
			#如果是POST方法
			if request.method == 'POST':
				kw = self.find_post_kw(request, kw)
			#如果是GET方法
			if request.method == 'GET':
				kw = self.find_get_kw(request, kw)

		#如果参数为空，参数设为路由路径的参数，即request.match_info
		if kw is None: #如果POST参数和GET参数为空
			kw = dict(**request.match_info)
		else: #如果POST参数和GET参数不为空
			if not self._has_var_kw_arg and self._named_kw_args:
				#remove all unamed kw:
				copy = dict()
				for name in self._named_kw_args:
					if name in kw:
						copy[name] = kw[name]
				kw = copy

			#check named arg:
			for k, v in request.match_info.items():
				if k in kw:
					logging.warning('Duplicate arg name is named arg and kw args: %s' % k)
				kw[k] = v

		#如果有request参数，把request参数放进kw
		if self._has_request_arg:
			kw['request'] = request

		#检查那些必不可少的参数:如果某个参数在kw中没有包含，则返回HttpBadReqeust提示缺少参数
		if self._required_kw_args:
			for name in self._required_kw_args:
				if not name in kw:
					return web.HttpBadRequest('Missing argument: %s' % name)


		#打印日志，提示函数有哪些参数
		logging.info('call with args: %s' % str(kw))


		#调用fn函数，并将**kw参数传给fn函数处理，且得到返回的response
		try:
			r = await self._func(**kw)
			return r
		except APIError as e:
			return dict(error=e.error, data=e.data, message=e.message)


def add_static(app):
	path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
	app.router.add_static('/static/', path)
	logging.info('add static %s ==> %s' % ('/static/', path))


#编写一个add_route函数，用来注册一个URL处理函数
#从url函数中获取方法和路径信息，并检查协程，然后：
#设置路由：app.router.add_route(method, path, handlerFunc)
def add_route(app, fn):
	#获取get/post函数中的method和route参数
	method = getattr(fn, '__method__', None)
	path = getattr(fn, '__route__', None)

	#如果路径或者方法名称为空，返回错误提示
	if path is None or method is None:
		raise ValueError('@get or @post not defined in %s：' % str(fn))

	#如果不是协程函数，且不是装饰函数，将其加入协程
	if not asyncio.iscoroutinefunction(fn) and not inspect.isgeneratorfunction(fn):
		fn = asyncio.coroutine(fn)

	logging.info('add route %s %s => %s(%s)' % (method, path, fn.__name__, ' , '.join(inspect.signature(fn).parameters.keys())))

	#将url处理函数通过RequestHandler处理后，返回RequestHandler的实例handler
	#即以handler作为函数对象传递给add_route()的第三个参数
	app.router.add_route(method, path, RequestHandler(app, fn))


#把很多次add_route()注册的调用：
#add_route(app, handles.index)
#add_route(app, handles.blog)
#add_route(app, handles.create_comment)
#变为自动扫描：add_routes(app, 'handlers')
#即自动把handler模块的所有符合条件的函数注册了
def add_routes(app, module_name):
	n = module_name.rfind('.')
	if n == (-1):
		mod = __import__(module_name, globals(), locals())
	else:
		name =  module_name[n+1:]
		mod = getattr(__import__(module_name[:n], globals(), locals(), [name]), name)

	for attr in dir(mod):
		if attr.startswith('_'):
			continue
		fn = getattr(mod, attr)
		if callable(fn):
			method = getattr(fn, '__method__', None)
			path = getattr(fn, '__route__', None)
			if method and path:
				add_route(app, fn)
