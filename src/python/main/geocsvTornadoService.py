#!/usr/bin/env python

import tornado.ioloop
import tornado.web
import tornado.httpclient
import GeocsvHandler
import sys

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

    self.GeocsvHandler = GeocsvHandler.GeocsvHandler(self)

  def get(self):
    print("----- current_user: ", self.get_current_user())
    pctl = GeocsvHandler.default_program_control()

    try:
      pctl['input_url'] = self.get_query_argument('input_url')
      print("----- input_url: ", pctl['input_url'])
    except Exception as e:
      sys.stderr.write("----- from stderr URL required ex: " + str(e) + "\n")
      self.set_header('Access-Control-Allow-Origin', '*')
      self.set_header('Content-Type', 'text/plain; charset=UTF-8')
      self.write("----- input_url parameter required" + "\n")
      return

    bool_param_list = ['verbose', 'octothorp', 'unicode', 'null_fields', \
        'test_mode']
    for param in bool_param_list:
        try:
          arg_val = self.get_query_argument(param)
          pctl[param] = GeocsvHandler.str2bool(arg_val)
        except Exception as e:
          # ignore, not required
          pass

    print("----- doReport *****, pctl: ", pctl)
    self.write("-----1 *&*&*&*&*&*\n\n")

    self.GeocsvHandler.doReport(pctl)

    self.set_header('Access-Control-Allow-Origin', '*')
    self.set_header('Content-Type', 'text/plain; charset=UTF-8')
    self.write("\n-----2 *&*&*&*&*&*")

class DefaultGeocsvTornadoHandler(tornado.web.RequestHandler):
  def initialize(self):
    print("***** DefaultGeocsvTornadoHandler initialize")

  def get(self):
    print("***** default current_user: ", self.get_current_user())

    print("***** default action *****",)
    self.set_header('Access-Control-Allow-Origin', '*')
    self.set_header('Content-Type', 'text/plain; charset=UTF-8')
    self.write("%%%%%% default")


def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
##        (r"/geows/geocsv/1/validate.*", GeocsvTornadoHandler)
        (r"/geows/geocsv/1/validate.*", GeocsvTornadoHandler),
        (r".*", DefaultGeocsvTornadoHandler)
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8989)
    print("***** listening on 8989")
    try:
      tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
      print("***** KeyboardInterrupt handled")
