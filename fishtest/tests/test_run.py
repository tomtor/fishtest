import unittest

from fishtest.views import get_master_bench
  
class CreateRunTest(unittest.TestCase):

  def tearDown(self):
    pass

  def test_10_get_bench(self): 
    print(get_master_bench())


if __name__ == "__main__":
  unittest.main()
