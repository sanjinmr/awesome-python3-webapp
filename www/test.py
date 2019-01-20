#！、user/bin/env python3
#-*- coding: utf-8 -*-

from user import user

#创建实例：
user = User(id=123, name='Michael')
#存入数据库
user.insert()
#查询所有User对象：
users = User.findAll()
