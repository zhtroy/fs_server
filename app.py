import socket
from multiprocessing import Process ,Pipe, Queue
from threading import Thread
import threading
from contextlib import closing
import socketserver
from datetime import datetime
import queue


class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self):
        super(StoppableThread, self).__init__()
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

def phoneThread(s,q):
    try:
        while True:
            data = s.recv(1024)
            print('recv: {}  at:{}'.format(data,datetime.now().time()))
            if not data:    #socket关闭后退出线程
                print('phone socket closed, quit thread')
                break   
            q.put(data)
    except:
        raise
    finally:
        s.close()
   

def Server(port,qrecv, qsend):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #with closing( socket.socket(socket.AF_INET, socket.SOCK_STREAM) ) as s:
        s.bind(('', port))
        s.listen()
        print('phone server listening on: ', port)
        ts = []
       # client_sock = None
        while True:
            conn, addr = s.accept()
            print('port: ' ,port,'Connected by', addr)
            
            if ts:
                for t in ts:
                    t.stop()
                ts.clear()
            '''
            if client_sock:
                client_sock.close()
                '''
            tsend =SendThread(conn,qsend)
            ts.append(tsend)
            ts.append(RecvThread(conn,qrecv,tsend))
            #client_sock = conn
            
            for t in ts:
                t.start()


    except KeyboardInterrupt:
        return
    finally:
        s.close()
           

def boardThread(s,q):
    try:
        while True:
        
            data = q.get()
            s.send(data)
            print('send: ', data)
            
    except ConnectionAbortedError:
        print('board socket closed, quit thread')
    finally:
        s.close()

class SendThread(StoppableThread):
    def __init__(self,socket, q):
        super().__init__()
        self._s = socket
        self._q = q
        self.name = 'Send thread '
    
    def run(self):
        
        while True:
            if self.stopped():
                break
            try:
                data = self._q.get(timeout = 0.1)
            except queue.Empty:
                continue
           
            try:
                self._s.send(data)
            except:
                print('peer socket closed')
                break

            print('send: ', data)

        print('quit send thread')
        self._s.close()
                
class RecvThread(StoppableThread):
    def __init__(self,socket, q,tx_thread):
        super().__init__()
        self._s = socket
        self._q = q
        self._tx = tx_thread
        self.name = 'Recv thread '
        
    
    def run(self):
        while True:
            if self.stopped():
                break

            try:
                data = self._s.recv(1024)
            except :
                print('peer socket closed')
                break

            print('recv: {}'.format(data))

            if not data:    #socket关闭后退出线程
                print('peer socket closed')
                break   
            self._q.put(data)

        print('quit  recv thread')
        self._tx.stop()
        self._s.close()
        








if __name__ == '__main__':
    qin,qout = Queue(),Queue()  #qin是从手机到处理板的队列
    pBoard = Thread(target=Server , args = (3000, qin, qout))
    pPhone = Thread(target=Server , args = (5000, qout, qin ))

    pBoard.start()
    pPhone.start()

    pBoard.join()
    pPhone.join()



    



   




   