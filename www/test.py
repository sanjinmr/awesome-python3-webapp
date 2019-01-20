#！、user/bin/env python3
#-*- coding: utf-8 -*-

import asyncio
import orm
from models import User, Blog, Comment

async def test(loop):
    await orm.create_pool(loop=loop, user='root', password='862525', db='firsttest')

    u = User(name='Test', email='test11@example.com', passwd='1234567890', image='about:blank')

    await u.save()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test(loop))
    #loop.run_forever()
    print('Test finished.')
    #loop.close()
#bottom
