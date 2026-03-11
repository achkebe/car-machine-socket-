import socket
import json
import time
from config import *

class EngineModule:
    def __init__(self):
        self.host = HOST
        self.engine_port = ENGINE_PORT
        self.sensor_port = SENSOR_PORT
        self.master_port = MASTER_PORT
        self.status = "未启动"  # 发动机状态
        self.speed = 0          # 发动机转速
        self.car_speed = 0      # 从传感器获取的车速

    def request_car_speed(self):
        """持续向传感器模块请求车速，更新本地车速"""
        while True:
            try:
                # 建立与传感器的TCP连接
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((self.host, self.sensor_port))
                # 构造车速请求指令
                request = {
                    "type": CMD_SPEED_REQUEST,
                    "data": {},
                    "from": "engine",
                    "to": "sensor"
                }
                s.send(json.dumps(request).encode(ENCODING))
                # 接收传感器返回的车速
                recv_data = s.recv(BUFFER_SIZE).decode(ENCODING)
                data = json.loads(recv_data)
                if data.get("type") == CMD_SPEED_RESPONSE:
                    self.car_speed = data.get("data")
                s.close()
                time.sleep(1)
            except Exception as e:
                print(f"【发动机模块】请求车速失败：{e}")
                self.car_speed = 0
                time.sleep(1)

    def exec_master_cmd(self, conn):
        """执行总控的控制指令，返回发动机状态"""
        while True:
            try:
                recv_data = conn.recv(BUFFER_SIZE).decode(ENCODING)
                if not recv_data:
                    break
                data = json.loads(recv_data)
                # 处理总控的发动机控制指令
                if data.get("type") == CMD_ENGINE_CTRL and data.get("from") == "master":
                    cmd = data.get("data").get("cmd")
                    param = data.get("data").get("param")
                    # 执行启停/调转速指令
                    if cmd == "启停":
                        self.status = "运行中" if param == "启动" else "未启动"
                        self.speed = 2000 if self.status == "运行中" else 0
                    elif cmd == "调转速":
                        self.speed = param
                        self.status = "运行中" if param > 0 else "未启动"
                    # 构造状态返回数据
                    response = {
                        "type": CMD_ENGINE_STATUS,
                        "data": {"状态": self.status, "转速": self.speed, "当前车速": self.car_speed},
                        "from": "engine",
                        "to": "master"
                    }
                    conn.send(json.dumps(response).encode(ENCODING))
            except Exception as e:
                print(f"【发动机模块】与总控通信异常：{e}")
                break
        conn.close()

    def start(self):
        """启动发动机模块：请求车速+监听总控指令"""
        import threading
        # 启动请求车速线程
        speed_thread = threading.Thread(target=self.request_car_speed, daemon=True)
        speed_thread.start()
        # 启动Socket服务端，监听总控指令
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.engine_port))
        server.listen(5)
        print(f"【发动机模块】启动成功，监听端口：{self.engine_port}")
        try:
            while True:
                conn, addr = server.accept()
                print(f"【发动机模块】与总控建立连接：{addr}")
                # 处理总控指令的线程
                handle_thread = threading.Thread(target=self.exec_master_cmd, args=(conn,), daemon=True)
                handle_thread.start()
        except KeyboardInterrupt:
            pass
        finally:
            server.close()
            print("【发动机模块】停止运行")

if __name__ == "__main__":
    engine = EngineModule()
    engine.start()