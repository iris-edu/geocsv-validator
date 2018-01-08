#!/usr/bin/env python

import tornado.ioloop
import tornado.web
import tornado.httpclient
import GeocsvHandler
import sys
import io

GeoCSV_param_list = ['verbose', 'octothorp', 'unicode', 'null_fields', \
        'write_report']

class MainHandler(tornado.web.RequestHandler):
  def initialize(self):
    print("***** MainHandler initialize")

  def get(self):
    print("** MainHandler get")
    self.set_header('Access-Control-Allow-Origin', '*')
    self.set_header('Content-Type', 'text/plain; charset=UTF-8')
    self.write("***** get called on base url")

class GeocsvTornadoHandler(tornado.web.RequestHandler):
  def initialize(self):
    print("***** GeocsvTornadoHandler initialize")
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

    for param in GeoCSV_param_list:
        try:
          arg_val = self.get_query_argument(param)
          pctl[param] = GeocsvHandler.str2bool(arg_val)
        except Exception as e:
          # ignore, not required
          pass

    self.GeocsvHandler.doReport(pctl)

    self.set_header('Access-Control-Allow-Origin', '*')
    self.set_header('Content-Type', 'text/plain; charset=UTF-8')

class GeocsvTornadoFormsHandler(tornado.web.RequestHandler):
  def initialize(self):
    print("***** GeocsvTornadoFormsHandler initialize")
    self.GeocsvHandler = GeocsvHandler.GeocsvHandler(self)

  def get(self):
    print("***** GeocsvTornadoFormsHandler get HTML page *****",)

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

    pctl = GeocsvHandler.default_program_control()
    for item in self.request.arguments:
      for parm in GeoCSV_param_list:
        if item == 'geocsv_' + parm:
          value = self.request.arguments[item][0].decode("utf-8")
          pctl[parm] = GeocsvHandler.str2bool(value)

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

    self.GeocsvHandler.doReport(pctl)

    self.set_header('Access-Control-Allow-Origin', '*')
    self.set_header('Content-Type', 'text/plain; charset=UTF-8')

class DefaultGeocsvTornadoHandler(tornado.web.RequestHandler):
  def initialize(self):
    print("***** DefaultGeocsvTornadoHandler initialize")

  def get(self):
    print("***** default current_user: ", self.get_current_user())

    print("***** doing default action  for unrecognized URLs *****",)
    self.set_header('Access-Control-Allow-Origin', '*')
    self.set_header('Content-Type', 'text/plain; charset=UTF-8')
    self.write("%%%%%% default action for unrecognized URLs")

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
        (r"/geows/geocsv/1/vforms.*", GeocsvTornadoFormsHandler),
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
