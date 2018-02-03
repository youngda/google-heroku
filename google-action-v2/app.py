import websockets
import socket
import asyncio
import json
import time, os
import logging
from time import sleep

class HttpWSSProtocol(websockets.WebSocketServerProtocol):
  rwebsocket = None
  rddata = None
#  async def process_request(self,path,request_headers):
#    print("intercept header")
#    if path != '/ws':
#      print("Intercept header")
#      print(path)
#      print(request_headers)
#      try:
#        return await self.http_handler(path)
#      except Exception as e:
#        print("Handler fails with: ",e)
#    else:
#      process_request=None

  async def handler(self):
    try:
      print("Start class handler")
      path, headers = await websockets.http.read_request(self.reader)
      #websockets.accept()
    except Exception as e:
      #print ("I/O error("+e.errno+") , "+e.strerror)
      print ("I/O error", e)
      #self.writer.close()
      # self.ws_server.unregister(self)
      # raise
    # TODO: Check headers etc. to see if we are to upgrade to WS.
    if path == '/ws':
      # HACK: Put the read data back, to continue with normal WS handling.
      self.reader.feed_data(bytes(request_line))
      self.reader.feed_data(headers.as_bytes().replace(b'\n', b'\r\n'))
      return await super(HttpWSSProtocol, self).handler()
    else:
       try:
         return await self.http_handler(path)
       except Exception as e:
        print("Handler fails with: ",e)
       finally:
         print('Closing connection')
         self.writer.close()
         self.ws_server.unregister(self)



  async def http_handler(self, path):
    global reply
    reply=self

    try:
      #sleep(0.50)
      googleRequest = self.reader._buffer.decode('utf-8')
      print("Google request length: ",len(googleRequest))
      googleRequestJson = json.loads(googleRequest)
      #{"location": "living", "state": "on", "device": "lights"}
      print("From Google: "+googleRequestJson['result']['resolvedQuery'])
      if 'state' in googleRequestJson['result']['resolvedQuery']:
        ESPparameters = googleRequestJson['result']['parameters']
        ESPparameters['query'] = '?'
        order = 'cmd=publish&uid=youngda&device_name=LED001&device_cmd=ON'
        s = socket.socket()  
        host = "iot.doit.am"  
        port =  8810  
        s.connect((host, port))  
        s.send(order.encode())
        s.recv(1024)
      elif 'on or off' in googleRequestJson['result']['resolvedQuery']:
        ESPparameters = googleRequestJson['result']['parameters']
        ESPparameters['query'] = '?'
        order = 'cmd=publish&uid=youngda&device_name=LED001&device_cmd=ON'
        s = socket.socket()  
        host = "iot.doit.am"  
        port =  8810  
        s.connect((host, port))  
        s.send(order.encode())
        s.recv(1024)
      elif 'GOOGLE_ASSISTANT_WELCOME' in googleRequestJson['result']['resolvedQuery']:
        ESPparameters = googleRequestJson['result']['parameters']
        ESPparameters['query'] = 'connect'
        order = 'cmd=publish&uid=youngda&device_name=LED001&device_cmd=ON'
        s = socket.socket()  
        host = "iot.doit.am"  
        port =  8810  
        s.connect((host, port))  
        s.send(order.encode())
        s.recv(1024)
      else:
        ESPparameters = googleRequestJson['result']['parameters']
        ESPparameters['query'] = 'cmd'
        # send command to ESP over websocket
      if self.rwebsocket== None:
        print("Device is not connected!")
      else:
        await self.rwebsocket.send(json.dumps(ESPparameters))
        print("sent to websocket: ", ESPparameters)
        sleep(0.25)
      print("Got it",self.rddata,HttpWSSProtocol.rddata)
      print("waiting for socket response to Google")
      self.rddata = await self.rwebsocket.recv()
      print("Receive response for Google from websocket",self.rddata)
      {"speech": "It is working", "displayText": "It is working"}

    except Exception as e:
      print("HTTP Handler fails with: ",e)

def updateData(data):
  HttpWSSProtocol.rddata = data

async def ws_handler(websocket, path):
  game_name = 'g1'
  #print("handler starts")
  try:
    HttpWSSProtocol.rwebsocket = websocket
    await websocket.send(json.dumps({'heartbeat': 'OK'}))
    data ='{"empty":"empty"}'
    while True:
      response = ''
      respond = False
      data = await websocket.recv()
      updateData(data)
      status = json.loads(data)['status']
      #print("Status = ",status)
      if (status == "Socket Connected"):
        print("Socket Connected")
      elif (status == "keepalive"):
        print("Heartbeat")
        await websocket.send(json.dumps({'heartbeat': 'OK'}))
      elif (status == "GOOGLE CONNECTED"):
        print("Google Connected")
        responseText = '{"speech": "What would you like done?", "displayText": "What would you like done?"}'
        respond = True
      elif (status == "Response"):
        print("Response Received")
        state = json.loads(data)['state']
        responseText = '{"speech": "It is turned '+state+'", "displayText": "It is turned '+state+'"}'
        respond = True
      else:
        print("Unknown status")
      if (respond == True):
        response = '\r\n'.join([
          'HTTP/1.1 200 OK',
          'Content-Type: text/json',
          '',
          ''+responseText+'',
        ])
        print("Writeback to Google",responseText,"Response END")
        reply.writer.write(response.encode())
        #print('Closing connection')
        reply.writer.close()
        reply.ws_server.unregister(reply)
  except Exception as e:
    print ("ws_handler error. Received = ",data,"Error = ",e)
  finally:
    print("")

port = int(os.getenv('PORT', 8020))
logger = logging.getLogger('websockets')
logger.setLevel(logging.ERROR)
logger.addHandler(logging.StreamHandler())
print("Starting server on port",port)
start_server = websockets.serve(ws_handler, None, port, klass=HttpWSSProtocol)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
