import socket
import json
import time
import threading
from config import *

class MasterControl:
    def __init__(self):
        self.host = HOST
        self.master_port = MASTER_PORT
        self.engine_port = ENGINE_PORT
        self.display_port = DISPLAY_PORT
        self.running = True
        self.engine_conn = None  # 与发动机的连接
        self.display_conn = None # 与显示模块的连接

    def connect_module(self, port):
        """建立与发动机/显示模块的TCP连接，返回连接对象"""
        while self.running:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((self.host, port))
                print(f"【总控模块】成功连接端口：{port}")
                return s
            except Exception as e:
                print(f"【总控模块】连接端口{port}失败，重试中：{e}")
                time.sleep(1)

    def handle_sensor_data(self, conn):
        """接收传感器上报的车速，转发到显示模块"""
        while self.running:
            try:
                recv_data = conn.recv(BUFFER_SIZE).decode(ENCODING)
                if not recv_data:
                    break
                data = json.loads(recv_data)
                # 转发车速到显示模块
                if data.get("type") == CMD_MASTER_SPEED:
                    self.display_conn.send(json.dumps(data).encode(ENCODING))
            except Exception as e:
                print(f"【总控模块】接收传感器数据异常：{e}")
                break
        conn.close()

    def handle_engine_status(self, conn):
        """接收发动机返回的状态，转发到显示模块"""
        while self.running:
            try:
                recv_data = conn.recv(BUFFER_SIZE).decode(ENCODING)
                if not recv_data:
                    break
                data = json.loads(recv_data)
                # 转发发动机状态到显示模块
                if data.get("type") == CMD_ENGINE_STATUS:
                    self.display_conn.send(json.dumps(data).encode(ENCODING))
            except Exception as e:
                print(f"【总控模块】接收发动机状态异常：{e}")
                break
        conn.close()

    def send_engine_cmd(self, cmd, param):
        """向发动机模块下发控制指令"""
        try:
            cmd_data = {
                "type": CMD_ENGINE_CTRL,
                "data": {"cmd": cmd, "param": param},
                "from": "master",
                "to": "engine"
            }
            self.engine_conn.send(json.dumps(cmd_data).encode(ENCODING))
            print(f"【总控模块】下发发动机指令：{cmd} -> {param}")
        except Exception as e:
            print(f"【总控模块】下发指令失败：{e}")

    def simulate_control(self):
        """模拟总控的发动机控制流程：启动->调转速->熄火"""
        time.sleep(3)
        self.send_engine_cmd("启停", "启动")  # 3秒后启动发动机
        time.sleep(5)
        self.send_engine_cmd("调转速", 2500)  # 再5秒调转速到2500
        time.sleep(4)
        self.send_engine_cmd("启停", "熄火")  # 再4秒熄火
        time.sleep(2)
        self.running = False
        print("=== 车机系统停止工作 ===")

    def start(self):
        """启动总控模块：建立模块连接+监听上报+模拟控制"""
        # 1. 先建立与发动机、显示模块的主动连接
        self.engine_conn = self.connect_module(self.engine_port)
        self.display_conn = self.connect_module(self.display_port)
        # 2. 启动Socket服务端，监听传感器/发动机的上报
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.master_port))
        server.listen(5)
        print("=== 车机系统启动成功，开始工作 ===")
        # 3. 启动模拟控制线程
        control_thread = threading.Thread(target=self.simulate_control, daemon=True)
        control_thread.start()
        # 4. 监听并处理传感器/发动机的连接
        try:
            while self.running:
                conn, addr = server.accept()
                # 区分传感器和发动机的连接（通过上报数据的from字段，也可通过端口区分）
                def check_module():
                    recv_data = conn.recv(BUFFER_SIZE).decode(ENCODING)
                    if not recv_data:
                        return
                    data = json.loads(recv_data)
                    if data.get("from") == "sensor":
                        # 处理传感器数据
                        self.handle_sensor_data(conn)
                    elif data.get("from") == "engine":
                        # 处理发动机状态
                        self.handle_engine_status(conn)
                threading.Thread(target=check_module, daemon=True).start()
        except KeyboardInterrupt:
            self.running = False
        finally:
            # 关闭所有连接
            self.engine_conn.close()
            self.display_conn.close()
            server.close()

if __name__ == "__main__":
    master = MasterControl()
    master.start()