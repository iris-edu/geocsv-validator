#!/usr/bin/env python

import tornado.ioloop
import tornado.web
import tornado.httpclient
import GeocsvHandler

class MainHandler(tornado.web.RequestHandler):
  def initialize(self):
    print("***** MainHandler initialize")

  def get(self):
    print("** MainHandler get")
    self.write("***** get called on base url")

class GeocsvTornadoHandler(tornado.web.RequestHandler):
  def initialize(self):
    print("***** GeocsvTornadoHandler initialize")
    self.default_url_string = 'http://geows.ds.iris.edu/geows-uf/wovodat/1/'\
        + 'query?format=text&showNumberFormatExceptions=true'

    self.GeocsvHandler = GeocsvHandler.GeocsvHandler()

  def get(self):
    response = self.doValidate(self.default_url_string)
    self.set_header('Access-Control-Allow-Origin', '*')
    self.set_header('Content-Type', 'text/plain; charset=UTF-8')
    self.set_header('Content-Disposition', 'inline; filename=geows-geocsv.txt')
    self.write("*&*&*&*&*&*\n" + response)

  def doValidate(self, target_url):
    pctl = GeocsvHandler.default_program_control()
    pctl['input_url'] = target_url
    pctl['verbose'] = False
    pctl['octothorp'] = False  # explicitly list any line with # and respective metrics
    pctl['unicode'] = False  # show lines where unicode is detected and respective metrics
    pctl['null_fields'] = False  # show lines if any field is null and respective metrics
    pctl['test_mode'] = False  # turns off report when true (i.e. keeps unit test report small)

    report_obj = self.GeocsvHandler.validate(pctl)
    rstr = self.GeocsvHandler.createReportStr(report_obj)
    return rstr

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/geows/geocsv/1/validate/", GeocsvTornadoHandler)
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8989)
    print("***** listening on 8989")
    try:
      tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
      print("***** KeyboardInterrupt handled")
