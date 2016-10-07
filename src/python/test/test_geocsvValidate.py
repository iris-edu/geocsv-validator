

import unittest
import main.geocsvValidate

class geocsvValidateTest1TestCase(unittest.TestCase):
  def runTest(self):
    target_url = 'http://geows.ds.iris.edu/geows-uf/wovodat/1/query?format=text&showNumberFormatExceptions=true'
    main.geocsvValidate.runvalidate(target_url)

def run_test_cases():
  print "*********** run_test_cases __name__: ", __name__
  runner = unittest.TextTestRunner()

  testCase1 = geocsvValidateTest1TestCase()
  runner.run(testCase1)


