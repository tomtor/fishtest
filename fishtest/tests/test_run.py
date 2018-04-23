import unittest
import re

from fishtest.views import get_master_bench, get_user_branch
  
class CreateRunTest(unittest.TestCase):

  def tearDown(self):
    pass

  def test_10_get_bench(self): 
    self.assertTrue(re.match('[0-9]{7}', get_master_bench()))

  """
  def test_20_get_user_branch(self): 
      print(get_user_branch('https://github.com/tomtor/fishtest'))
      #print(get_user_branch('https://github.com/glinscott/fishtest'))
      #self.assertTrue(get_user_branch('https://github.com/glinscott/fishtest'))
  """


if __name__ == "__main__":
  unittest.main()
