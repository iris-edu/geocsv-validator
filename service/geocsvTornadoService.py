#!/usr/bin/env python

import os
import sys
# setup to treat this folder as a peer to validator folder
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

import tornado.ioloop
import tornado.web
import tornado.httpclient
import validator.GeocsvValidator
import io
import datetime
import pytz

GeoCSV_param_list = ['verbose', 'octothorp', 'unicode', 'null_fields', \
        'write_report']

class MainHandler(tornado.web.RequestHandler):
  def initialize(self):
    print("***** MainHandler initialize " + \
        datetime.datetime.now(pytz.utc).isoformat())

  def get(self):
    print("** MainHandler get")
    self.set_header('Access-Control-Allow-Origin', '*')
    self.set_header('Content-Type', 'text/plain; charset=UTF-8')
    ##self.write("***** get called on base url")
    self.redirect(GEOCSV_DOCUMENT_URL, permanent=False, status=None)

class GeocsvTornadoHandler(tornado.web.RequestHandler):
  def initialize(self):
    print("***** GeocsvTornadoHandler initialize " + \
        datetime.datetime.now(pytz.utc).isoformat())
    self.GeocsvValidator = validator.GeocsvValidator.GeocsvValidator(self)

  def get(self):
    print("***** current_user: ", self.get_current_user())
    print ("***** request.arguments: " , self.request.arguments)
    pctl = validator.GeocsvValidator.default_program_control()

    for param in self.request.arguments:
      if param in GeoCSV_param_list or param == 'input_url':
        # name matches, ok to continue
        pass
      else:
        msg = "***** Error - unknown parameter: " + param
        sys.stderr.write(msg + "\n")
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Content-Type', 'text/plain; charset=UTF-8')
        self.write(msg + "\n")
        return


    try:
      pctl['input_url'] = self.get_query_argument('input_url')
      print("***** input_url: ", pctl['input_url'])
    except Exception as e:
      sys.stderr.write("***** from stderr URL required ex: " + str(e) + "\n")
      self.set_header('Access-Control-Allow-Origin', '*')
      self.set_header('Content-Type', 'text/plain; charset=UTF-8')
      self.write("***** input_url parameter required" + "\n")
      return

    for param in GeoCSV_param_list:
        try:
          arg_val = self.get_query_argument(param)
          pctl[param] = validator.GeocsvValidator.str2bool(arg_val)
        except Exception as e:
          # ignore, not required
          pass

    self.GeocsvValidator.doReport(pctl)

    self.set_header('Access-Control-Allow-Origin', '*')
    self.set_header('Content-Type', 'text/plain; charset=UTF-8')

class GeocsvTornadoFormsHandler(tornado.web.RequestHandler):
  def initialize(self):
    print("***** GeocsvTornadoFormsHandler initialize " + \
        datetime.datetime.now(pytz.utc).isoformat())
    self.GeocsvValidator = validator.GeocsvValidator.GeocsvValidator(self)

  def get(self):
    print("***** GeocsvTornadoFormsHandler get for forms page",)

    params_part = \
'''
      <tr><td>verbose (true or false)</td><td><input name="geocsv_verbose" type="text" value="false"/></td></tr>
      <tr><td>octothorp (true or false)</td><td><input name="geocsv_octothorp" type="text" value="false"/></td></tr>
      <tr><td>unicode (true or false)</td><td><input name="geocsv_unicode" type="text" value="false"/></td></tr>
      <tr><td>null_fields (true or false)</td><td><input name="geocsv_null_fields" type="text" value="false"/></td></tr>
      <tr><td>write_report (true or false)</td><td><input name="geocsv_write_report" type="text" value="true"/></td></tr>
'''

    page = \
'''
<html><body>
    <table border="1">
      <form id="GeocsvFormsMultiPart" method="post" action="/geows/geocsv/1/vforms" enctype="multipart/form-data">
''' + params_part + '''
      <tr><td>GeoCSV file</td><td><input name="geocsv_file" type="file" /></td></tr>
      <tr><td colspan="2" align="right"><input value="submit" type="submit" /></td></tr>
      </form>
   </table>
   <table border="1">
      <form id="GeocsvFormsPost" method="post" action="/geows/geocsv/1/vforms">
''' + params_part + '''
      <tr><td>GeoCSV text</td><td><textarea name="geocsv_texttext" rows="10" cols="100"></textarea></td></tr>
      <tr><td colspan="2" align="right"><input value="submit" type="submit" /></td></tr>
      </form>
   </table>
</body></html>
    '''

    self.set_header('Access-Control-Allow-Origin', '*')
    self.write(page)

  def post(self):
    # starting examples from 
    # https://github.com/tornadoweb/tornado/blob/master/demos/file_upload/file_receiver.py

    DEBUG = False

    if DEBUG:
      print("***** Geocsv post method: ", self.request.method, \
          "  remote_ip: ", self.request.remote_ip, \
          "  host: ", self.request.host)
      print("***** Geocsv post Content-Type: ", self.request.headers['Content-Type'])
      print("***** Geocsv post request: ", self.request)
      print("***** Geocsv post arguments: ", self.request.arguments)
      print("***** Geocsv post query_arguments: ", self.request.query_arguments)
      print("***** Geocsv post connection: ", self.request.connection)

    pctl = validator.GeocsvValidator.default_program_control()
    for item in self.request.arguments:
      for parm in GeoCSV_param_list:
        if item == 'geocsv_' + parm:
          value = self.request.arguments[item][0].decode("utf-8")
          pctl[parm] = validator.GeocsvValidator.str2bool(value)

    if self.request.headers['Content-Type'] == 'application/x-www-form-urlencoded':
      pctl['input_bytes'] = self.request.arguments['geocsv_texttext'][0]

    elif 'multipart/form-data' in self.request.headers['Content-Type']:
      for field_name, files in self.request.files.items():
        for info in files:
          filename, content_type = info['filename'], info['content_type']
          body = info['body']
          # for current html form, not expecting multiple files, only one
          pctl['input_bytes'] = body

          if DEBUG:
            print("***** Geocsv mp HTML field_name: ", field_name)
            print("***** Geocsv mp content_type:",content_type)
            print("***** Geocsv mp type body:", type(body))
            tstream = string_stream(str(body.decode('utf-8')))
            for line in tstream:
              print("---***** GeoCSV mp line:", line)

    else:
      msg = "***** ERROR - GeocsvTornadoFormsHandler UNHANDLED Content-Type: " + \
          str(self.request.headers['Content-Type'])
      print(msg)
      self.write(msg + "\n")
      self.set_header('Access-Control-Allow-Origin', '*')
      self.set_header('Content-Type', 'text/plain; charset=UTF-8')
      # NOTE: notice return from here on error
      return

    self.GeocsvValidator.doReport(pctl)

    self.set_header('Access-Control-Allow-Origin', '*')
    self.set_header('Content-Type', 'text/plain; charset=UTF-8')

class GeocsvTornadoVersionHandler(tornado.web.RequestHandler):
  def initialize(self):
    print("***** GeocsvTornadoVersionHandler initialize " + \
        datetime.datetime.now(pytz.utc).isoformat())

  def get(self):
    print("***** default current_user: ", self.get_current_user())

    print("***** doing GeocsvTornadoVersionHandler version handler",)
    self.set_header('Access-Control-Allow-Origin', '*')
    self.set_header('Content-Type', 'text/plain; charset=UTF-8')
    self.write("%%%%%% GeocsvValidator version: beta 0.9")
    self.write("\n%%%%%% geocsvTornadoService version: alpha prototype 0.3")

class DefaultGeocsvTornadoHandler(tornado.web.RequestHandler):
  def initialize(self):
    print("***** DefaultGeocsvTornadoHandler initialize " + \
        datetime.datetime.now(pytz.utc).isoformat())

  def get(self):
    print("***** default current_user: ", self.get_current_user())

    print("***** doing default action, redirect  for unrecognized URLs *****",)

    self.set_header('Access-Control-Allow-Origin', '*')
    self.set_header('Content-Type', 'text/plain; charset=UTF-8')
    # TBD - replace write with redirect?
    ##self.write("%%%%%% default action for unrecognized URLs")

    self.redirect(GEOCSV_DOCUMENT_URL, permanent=False, status=None)

# from https://stackoverflow.com/questions/21843693/creating-stream-to-iterate-over-from-string-in-python
def string_stream(s, separators="\n"):
    start = 0
    for end in range(len(s)):
        if s[end] in separators:
            yield s[start:end]
            start = end + 1
    if start < end:
        yield s[start:end+1]

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/geows/geocsv/1/validate.*", GeocsvTornadoHandler),
        (r"/geows/geocsv/1/version.*", GeocsvTornadoVersionHandler),
        (r"/geows/geocsv/1/vforms.*", GeocsvTornadoFormsHandler),
        (r".*", DefaultGeocsvTornadoHandler)
        # note alternative for / (r'/(.*)', tornado.web.StaticFileHandler, {'path': static_path}),
        # static_path should be the path to your apache-served website root directory
        # see https://stackoverflow.com/questions/27878813/running-tornado-hosting-app-on-different-port
    ])

if __name__ == "__main__":

  GEOCSV_LISTENING_PORT = os.environ.get('GEOCSV_LISTENING_PORT', '8989')
  print("***** listening on " + GEOCSV_LISTENING_PORT)

  # the document URL could be a static page, swagger-ui, etc.
  GEOCSV_DOCUMENT_URL = os.environ.get('GEOCSV_DOCUMENT_URL', 'http://localhost:8988')
  print("***** GEOCSV_DOCUMENT_URL: ", GEOCSV_DOCUMENT_URL)

  app = make_app()
  app.listen(GEOCSV_LISTENING_PORT)

  try:
    tornado.ioloop.IOLoop.current().start()
  except KeyboardInterrupt:
    print("***** KeyboardInterrupt handled")
