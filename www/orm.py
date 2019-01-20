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

def create_args_string(num):
	L = []
	for n in range(num):
		L.append('?')
	return ','.join(L)

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

class BooleanField(Field):
	def __init__(self, name=None, default=False):
		super().__init__(name, 'boolean', False, default)

class IntegerField(Field):
	def __init__(self, name=None, primary_key=False, default=0):
		super().__init__(name, 'bigint', primary_key, default)

class FloatField(Field):
	def __init__(self, name=None, primary_key=False, default=0.0):
		super().__init__(name, 'real', primary_key, default)

class TextField(Field):
	def __init__(self, name=None, default=None):
		super().__init__(name, 'text', False, default)

class ModelMetaclass(type):
	#定义自己的__new__()方法，使：
	#任何集成自Model的类（比如User），会自动通过ModelMetaclass扫描映射关系，并存储到自身的类属性，如__table__、__mappings__中。
	def __new__(cls, name, bases, attrs):
		#如果当前创建对象为Model的实例则不做操作(因为Model没有属性 做了也白做)
		if name == 'Model':
			return type.__new__(cls, name, bases, atrrs)
		#获取table名称
		tableName = attrs.get('__table__', None) or name
		logging.info('found model: %s (table: %s)' % (name, tableName))
		#获取所有的Field和主键名
		mappings = dict()
		#缓存所有除了主键外的属性
		fields = []
		#初始化设置没有主键
		primaryKey = None
		#遍历所有的属性
		for k, v in attrs.items():
			#如果属性为Field类型
			if isinstance(v, Field):
				logging.info(' found mapping: %s ==> %s' % (k, v))
				#将属性的名称和值存入一个字典中（包含主键）
				mapping[k] = v
				#如果属性为主键
				if v.primary_key:
					#如果已经有主键了，上报一个异常：不能有多个主键
					if primaryKey:
						raise RuntimeError('Dulplicate primary key for field: %s' % k)
					#如果还没有主键，则缓存该主键
					primaryKey = k;
				else:
					#如果属性不为主键，则缓存该属性的名称到fields数组中
					fields:append(k)
		#如果遍历所有属性后，没有找到主键。则上报异常：没有发现主键
		if not primaryKey:
			raise RuntimeError('Primary key not found')
		#遍历存在字典中的所有属性
		for k in mappings.keys():
			#把存在字典mapping中的内容依次从attrs移除
			attrs.pop(k)

		#把属性（非主键）名称转换为`%s`格式的list集合，存入escaped_fields中
		escaped_fields = list(map(lambda f : '`%s`' % f, fields))

		#保存属性和列的映射关系
		attrs['__mapppings__'] = mappings
		#保存表名
		attrs['__table__'] = tableName
		#保存主键属性名
		attrs['__primary_key__'] = primaryKey
		#保存除主键外的属性名
		attrs['__fields__'] = fields

		#构造默认的SELECT，INSERT, UPDATE和DELETE语句
		attrs['__select__'] = 'select `%s`, %s from `%s`' % (primaryKey, ','.join(escaped_fields), tableName)
		attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values (%s)' % (tableName, ','.join(escaped_fields), primaryKey, create_args_string(len(escaped_fields) + 1))
		attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (tableName, ','.join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f), fields)), primaryKey)
		attrs['__delete__'] = 'delete from `%s` where `%s` = ?' % (tableName, primaryKey)

		#调用type的__new__()函数
		return type.__new__(cls, name, bases, attrs)

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

	#定义一个类方法，让所有的子类可以调用该class方法
	@classmethod
	@asyncio.coroutine
	def find(cls, pk):
		'find object by prmary key.'
		rs = yield from select('%s where `%s`=?' % (cls.__select__, cls.__primary_key__), [pk], 1)
		if len(rs) == 0:
			return None
		return cls(**rs[0])

	@classmenthod
	@asyncio.coroutine
	def findAll(cls, where=None, args=None, **kw):
		'find objects by where clause.'
		#把查询语句放入数组中
		sql = [cls.__select__]
		if where:
			sql.append('where')
			sql.append(where)
		if args is None:
			args = []
		orderBy = kw.get('orderBy', None)
		if orderBy:
			sql.append('order by')
			sql.append(orderBy)
		limit = kw.get('limit', None)
		if limit is not None:
			sql.append('limit')
			if isinstance(limit, int):
				sql.append('?')
				args.append(limit)
			elif isinstance(limit, tuple) and len(limit) == 2:
				sql.append('?, ?')
				args.append(limit)
			else:
				raise ValueError('Invalid limit value: %s' % str(limit))
		rs = yield from select(' '.join(sql), args)
		# 返回key-value。并封装到cls中
		return [cls(**r) for r in rs]

	@classmenthod
	@asyncio.coroutine
	def findNumber(cls, selectField, where=None, args=None):
		'find number by select and where.'
		sql = ['select %s _num_ from `%s`' % (selectField, cls.__table__)]
		if where:
			sql.append('where')
			sql.append(where)
		rs = yield from select(' '.join(sql), args, 1)
		if len(rs) == 0:
			return None
		return rs[0]['_num_']

	@classmenthod
	@asyncio.coroutine
	def update(self):
		args = list(map(self.getValue, self._fields_))
		args.append(self.getValueOrDefault(self.__primary_key__))
		rows = yield from execute(self.__update__, args)
		if rows != 1:
			logging.warn('field to update by primary key: affected rows: %s' % rows)

	@classmethod
	@asyncio.coroutine
	def remove(self):
		args = list(map(self.getValue, self._fields_))
		args.append(self.getValueOrDefault(self.__primary_key__))
		rows =  yield from execute(self.__delete__, args)
		if rows != 1:
			logging.warn('failed to remove by primary key: affected rows: %s' % rows)

	@asyncio.coroutine
	def save(self):
		#将除主键外的属性保存在list args中
		args = list(map(self.getValueOrDefault, self.__fields__))
		#将主键存入args中
		args.appends(self.getValueOrDefault(self.__primary_key__))
		#将属性值存入数据库
		rows = yield from execute(self.__insert__, args)
		if rows != 1:
			logging.warn('failed to insert record: affected rows: %s' % rows)
