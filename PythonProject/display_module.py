import socket
import json
from config import *

class DisplayModule:
    def __init__(self):
        self.host = HOST
        self.display_port = DISPLAY_PORT
        self.running = True

    def show_info(self, show_type, content):
        """终端模拟车机屏幕显示信息"""
        print(f"\033[32m【车机显示】{show_type}：{content}\033[0m")  # 绿色字体突出显示

    def handle_master_cmd(self, conn):
        """处理总控的显示指令，调用显示方法"""
        while self.running:
            try:
                recv_data = conn.recv(BUFFER_SIZE).decode(ENCODING)
                if not recv_data:
                    break
                data = json.loads(recv_data)
                # 显示车速
                if data.get("type") == CMD_MASTER_SPEED:
                    speed = data.get("data")
                    self.show_info("当前车速", f"{speed} km/h")
                # 显示发动机状态
                elif data.get("type") == CMD_ENGINE_STATUS:
                    engine_data = data.get("data")
                    self.show_info("发动机状态", f"{engine_data['状态']}，转速{engine_data['转速']} r/min，当前车速{engine_data['当前车速']} km/h")
            except Exception as e:
                print(f"【显示模块】与总控通信异常：{e}")
                break
        conn.close()

    def start(self):
        """启动显示模块：监听总控的显示指令"""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.display_port))
        server.listen(5)
        print(f"【显示模块】启动成功，监听端口：{self.display_port}")
        try:
            while self.running:
                conn, addr = server.accept()
                print(f"【显示模块】与总控建立连接：{addr}")
                import threading
                # 处理总控显示指令的线程
                handle_thread = threading.Thread(target=self.handle_master_cmd, args=(conn,), daemon=True)
                handle_thread.start()
        except KeyboardInterrupt:
            self.running = False
        finally:
            server.close()
            print("【显示模块】停止运行")

if __name__ == "__main__":
    display = DisplayModule()
    display.start()