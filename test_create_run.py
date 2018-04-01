import unittest
import time
import os
import os.path

from fishtest.fishtest.rundb import RunDb

class CreateRunTest(unittest.TestCase):

  def tearDown(self):
    return
   
  def test_create_run(self):
    rundb= RunDb()
    id = rundb.new_run('master', 'master', 100000, '10+0.01', 'book', 10, 1, '', '')
    print(id)
    run = rundb.get_run(id)
    print(run['tasks'][0])
    run['tasks'][0][u'active'] = True
    print(run['tasks'][0])
    r= rundb.update_task(id, 0, {'wins': 1, 'losses': 1, 'draws': 997}, 1000000, '')
    print(r)
    r= rundb.update_task(id, 0, {'wins': 1, 'losses': 1, 'draws': 998}, 1000000, '')
    print(r)
    rundb.conn.close()
    return


if __name__ == "__main__":
  unittest.main()
