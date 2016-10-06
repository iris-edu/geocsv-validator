

import unittest
import main.geocsvValidate

class Widget():
  def size(self):
    print "--- sz func"
    return (50,50)

class DefaultWidgetSizeTestCase(unittest.TestCase):
  def runTest(self):
    widget = Widget()
    print "****** size: ", widget.size()
    assert widget.size() == (50,50), 'incorrect default size'
    print "after assert"

def run_test_cases():
  testCase1 = DefaultWidgetSizeTestCase()

  runner = unittest.TextTestRunner()
  runner.run(testCase1)

  main.geocsvValidate.runit()

print "*********** the one testsample __name__: ", __name__