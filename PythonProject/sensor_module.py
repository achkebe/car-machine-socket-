import socket
import random
import time
import json
from config import *

class SpeedSensor:
    def __init__(self):
        self.host = HOST
        self.sensor_port = SENSOR_PORT
        self.master_port = MASTER_PORT
        self.running = True
        self.speed = 0  # 实时车速

    def collect_speed(self):
        """模拟采集车速（10-120km/h），持续更新"""
        while self.running:
            self.speed = random.randint(10, 120)
            time.sleep(1)

    def handle_engine_request(self, conn):
        """处理发动机的车速请求，返回实时车速"""
        while self.running:
            try:
                # 接收发动机请求数据
                recv_data = conn.recv(BUFFER_SIZE).decode(ENCODING)
                if not recv_data:
                    break
                data = json.loads(recv_data)
                # 判定为发动机的车速请求
                if data.get("type") == CMD_SPEED_REQUEST and data.get("from") == "engine":
                    # 构造返回数据
                    response = {
                        "type": CMD_SPEED_RESPONSE,
                        "data": self.speed,
                        "from": "sensor",
                        "to": "engine"
                    }
                    conn.send(json.dumps(response).encode(ENCODING))
            except Exception as e:
                print(f"【传感器模块】与发动机通信异常：{e}")
                break
        conn.close()

    def report_to_master(self):
        """持续将实时车速上报给总控模块"""
        while self.running:
            try:
                # 建立与总控的TCP连接
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((self.host, self.master_port))
                # 构造上报数据
                report_data = {
                    "type": CMD_MASTER_SPEED,
                    "data": self.speed,
                    "from": "sensor",
                    "to": "master"
                }
                s.send(json.dumps(report_data).encode(ENCODING))
                s.close()
                time.sleep(1)  # 1秒上报1次
            except Exception as e:
                print(f"【传感器模块】上报总控失败：{e}")
                time.sleep(1)  # 失败后重试

    def start(self):
        """启动传感器模块：采集车速+监听发动机请求+上报总控"""
        # 启动车速采集线程
        import threading
        collect_thread = threading.Thread(target=self.collect_speed, daemon=True)
        collect_thread.start()
        # 启动上报总控线程
        report_thread = threading.Thread(target=self.report_to_master, daemon=True)
        report_thread.start()
        # 启动Socket服务端，监听发动机请求
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.sensor_port))
        server.listen(5)
        print(f"【传感器模块】启动成功，监听端口：{self.sensor_port}")
        try:
            while self.running:
                conn, addr = server.accept()
                print(f"【传感器模块】与发动机建立连接：{addr}")
                # 处理发动机请求的线程
                handle_thread = threading.Thread(target=self.handle_engine_request, args=(conn,), daemon=True)
                handle_thread.start()
        except KeyboardInterrupt:
            self.running = False
        finally:
            server.close()
            print("【传感器模块】停止运行")

if __name__ == "__main__":
    sensor = SpeedSensor()
    sensor.start()