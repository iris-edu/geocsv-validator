#!/usr/bin/env python

import tornado.ioloop
import tornado.web
import tornado.httpclient
import GeocsvHandler
import sys
import io

class MainHandler(tornado.web.RequestHandler):
  def initialize(self):
    print("***** MainHandler initialize")

  def get(self):
    print("** MainHandler get")
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

class GeocsvTornadoFormsHandler(tornado.web.RequestHandler):
  def initialize(self):
    print("***** GeocsvTornadoFormsHandler initialize")

  def get(self):
    print("***** GeocsvTornadoFormsHandler action *****",)
    self.set_header('Access-Control-Allow-Origin', '*')
    page = \
    '''
<html><body>
    <table border="1">
      <form id="GeocsvTFormsMultiPart" enctype="multipart/form-data" method="post" action="/geows/geocsv/1/vforms">
      <tr><td>format</td><td><input name="vformfileformat" type="text" /></td></tr>
      <tr><td>file</td><td><input name="vformfilefile" type="file" /></td></tr>
      <tr><td colspan="2" align="right"><input value="submit" type="submit" /></td></tr>
      </form>
   </table>
   <table border="1">
      <form id="GeocsvTFormsPost" method="post" action="/geows/geocsv/1/vforms">
      <tr><td>format</td><td><input name="vformtextformat" type="text" /></td></tr>
      <tr><td>text</td><td><textarea name="vformtexttext" rows="10" cols="100"></textarea></td></tr>
      <tr><td colspan="2" align="right"><input value="submit" type="submit" /></td></tr>
      </form>
   </table>
</body></html>
    '''
    self.write(page)

  def post(self):
    # examples from https://github.com/tornadoweb/tornado/blob/master/demos/file_upload/file_receiver.py

    print("***** dir request: ", dir(self.request))
    print("***** GeocsvTornadoFormsHandler method: ", self.request.method, \
        "  remote_ip: ", self.request.remote_ip, \
        "  host: ", self.request.host)
    print("***** GeocsvTornadoFormsHandler request: ", self.request)
    print("***** GeocsvTornadoFormsHandler headers: ", self.request.headers)
    print("***** GeocsvTornadoFormsHandler Content-Type: ", self.request.headers['Content-Type'])
    try:
      print("***** GeocsvTornadoFormsHandler arguments: ", self.request.arguments)
    except AttributeError:
      print("***** GeocsvTornadoFormsHandler arguments NOT FOUND")
    print("***** GeocsvTornadoFormsHandler query_arguments: ", self.request.query_arguments)
    print("***** GeocsvTornadoFormsHandler body_arguments: ", self.request.body_arguments)
    try:
      print("***** GeocsvTornadoFormsHandler connection: ", self.request.connection)
    except AttributeError:
      print("***** GeocsvTornadoFormsHandler connection NOT FOUND")
    try:
      print("***** GeocsvTornadoFormsHandler files: ", self.request.files)
    except AttributeError:
      print("***** GeocsvTornadoFormsHandler files NOT FOUND")

    if self.request.headers['Content-Type'] == 'application/x-www-form-urlencoded':
      print("***** GeocsvTornadoFormsHandler body type: ", type(self.request.body))

      self.set_header("Content-Type", "text/plain")
      contnt = self.get_body_argument("vformtexttext")
      print("----- posted type: " , type(contnt))
      print("----- posted: " + contnt)
      self.write("----- posted type: " + str(type(contnt)) + "\n")
      self.write("----- posted: " + contnt)
    elif 'multipart/form-data' in self.request.headers['Content-Type']:
      print("***** GeocsvTornadoFormsHandler HANDLED Content-Type: ", self.request.headers['Content-Type'])
      print("***** GeocsvTornadoFormsHandler body_argument vformfileformat: ", self.request.body_arguments['vformfileformat'])
      print("***** GeocsvTornadoFormsHandler body_argument vformfileformat type: ", type(self.request.body_arguments['vformfileformat']))
      print("***** GeocsvTornadoFormsHandler body_argument vformfileformat str: ", self.request.body_arguments['vformfileformat'][0].decode("utf-8"))
      print("***** GeocsvTornadoFormsHandler body_argument vformfileformat type: ", type(str(self.request.body_arguments['vformfileformat'][0].decode("utf-8"))))
      for field_name, files in self.request.files.items():
        for info in files:
          filename, content_type = info['filename'], info['content_type']
          body = info['body']
          print("***** GeocsvTornadoFormsHandler field_name: ", field_name, "  filename:",filename)
          print("***** GeocsvTornadoFormsHandler field_name: ", field_name, "  content_type:",content_type)
          print("***** GeocsvTornadoFormsHandler field_name: ", field_name, "  body:",body)
          tstream = string_stream(str(body.decode('utf-8')))
          for st in tstream:
            print("---***** GeocsvTornadoFormsHandler field_name: ", field_name, "  st:",st)

          MY_LINE_BREAK_CHARS = '\n\r'
          bo = io.BytesIO(body)
          myiter = bo.readlines().__iter__()
          while True:
            try:
              rowStr = next(myiter).decode('utf-8').rstrip(MY_LINE_BREAK_CHARS)
              print("--- ---***** GeocsvTornadoFormsHandler field_name: ", field_name, "  st:",st)
            except StopIteration:
              print("--- ---***** STOPPING")
      self.set_header("Content-Type", "text/plain")
      self.write("multipart processing" + "\n")

    else:
      print("***** GeocsvTornadoFormsHandler UNHANDLED Content-Type: ", self.request.headers['Content-Type'])
      msg = "----- posted, UNHANDLED Content-Type: " + str(self.request.headers['Content-Type'])
      self.set_header("Content-Type", "text/plain")
      print(msg)
      self.write(msg + "\n")

class GeocsvTPostHandler(tornado.web.RequestHandler):
  def initialize(self):
    print("***** GeocsvTPostHandler initialize")

  def get(self):
    print("***** GeocsvTPostHandler method: ", self.request.method, \
        "  remote_ip: ", self.request.remote_ip, \
        "  host: ", self.request.host)

    self.set_header('Access-Control-Allow-Origin', '*')
##    self.set_header('Content-Type', 'text/plain; charset=UTF-8')
    self.write('<html><body><form action="/geows/geocsv/1/vpost" method="POST">'
               '<input type="text" name="message">'
               '<input type="submit" value="Submit">'
               '</form></body></html>')

  def post(self):
    print("***** GeocsvTPostHandler method: ", self.request.method, \
        "  remote_ip: ", self.request.remote_ip, \
        "  host: ", self.request.host)
    print("***** GeocsvTPostHandler body type: ", type(self.request.body))

    self.set_header("Content-Type", "text/plain")
    contnt = self.get_body_argument("message")
    print("----- posted type: " , type(contnt))
    print("----- posted: " + contnt)
    self.write("----- posted type: " + str(type(contnt)) + "\n")
    self.write("----- posted: " + contnt)

class DefaultGeocsvTornadoHandler(tornado.web.RequestHandler):
  def initialize(self):
    print("***** DefaultGeocsvTornadoHandler initialize")

  def get(self):
    print("***** default current_user: ", self.get_current_user())

    print("***** default action *****",)
    self.set_header('Access-Control-Allow-Origin', '*')
    self.set_header('Content-Type', 'text/plain; charset=UTF-8')
    self.write("%%%%%% default")

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
        (r"/geows/geocsv/1/vforms", GeocsvTornadoFormsHandler),
        (r"/geows/geocsv/1/vpost", GeocsvTPostHandler),
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
