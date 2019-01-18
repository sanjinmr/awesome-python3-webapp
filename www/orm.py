#!/usr/bin/env python3
#-*-coding:utf-8-*-

__author__ = 'sanjinmr'

import asyncio, logging
import aiomysql
from orm import 

@sycnico.coroutine
def create_pool(loop, **kw):
	logging.info('create database connection pool...')
	global __pool
	__pool = yield from aiomysql.create_pool(
		host = kw.get('host', 'localhost'),
		port = kw.get('port', 3306),
		user = kw['user'],
		password = kw['password'],
		db = kw['db'],
		charset = kw.get('charset', 'utf8'),
		autocommit = kw.get('autocommit', True),
		maxsize = kw.get('maxsize', 10),
		minsize = kw.get('minsize', 1),
		loop = loop
		)

@asyncio.coroutine
def select(sql, args, size = None):
	log(sql, args)
	global __pool
	with (yield from __pool) as conn:
		cur = yield from conn.cursor(aiomysql.DictCursor)
		yield from cur.execute(sql.replace('?', '%s'), args or ())
		if size:
			rs = yield from cur.fetchmany(size)
		else:
			rs = yield from cur.fetchall()
		yield from cur.close()
		logging.info('from returned: %s' % len(rs))
		return rs
		
@asyncio.coroutine
def execute(sql, args):
	log(sql)
	with (yield from __pool) as conn:
		try:
			cur = yield from conn.cursor()
			yield from cur.execute(sql.replace('?', '%s'), args)
			affected = cur.rowcount
			yield from cur.close()
		except BaseException as e:
			raise
		return affected
		
class Model(dict, metaclass=ModelMetaclass):
	def __init__(self, **kw):
		super(Model, self).__init__(**kw)
		
	def __getattr__(self, key):
		try:
			return self[key]
		except KeyError:
			raise AttributeError(r"'Model' bject has no attribute '%s' % key")
	
	def __setattr__(self, key, value):
		self[key] = value
	
	def getValue(self, key):
		return getattr(self, key, None)
		
	def getValueOrDefault(self, key):
		value = getattr(self, key, None)
		if value is None:
			field = self.__mappings__[key]
			if field.default is not None:
				value = field.default() if calllable(field.default) else field default
				logging.debug('using default value for %s: %s' % (key, str(value)))
				setattr(self, key, value)
		return value

class Field(object):
	def __init__(self, name, column_type, primary_key, default):
		self.name = name
		self.column_type = column_type
		self.primary_key = primary_key
		self.default = default
		
	def __str__(self):
		return '<%s, %s:%s>' % (self.__class__.__name__, self.column_type, self.name)
		
class StringField(Field):
	def __init__(self, name=None, primary_key=false, default=None, ddl = 'varchar(100)'):
		super().__init__(name, ddl, primary_key, default)
		

class ModelMetaclass(type):
	def __new__(cls, name, bases, attrs):
		#排除Model本身
		if name == 'Model':
			return type.__new__(cls, name, bases, atrrs)
		#获取table名称
		tableName = attrs.get('__table__', None) or name
		logging.info('found model: %s (table: %s)' % (name, tableName))
		#获取所有的Field和主键名
		mappings = dict()
		fields = []
		primaryKey = None
		
		
		
		
		
