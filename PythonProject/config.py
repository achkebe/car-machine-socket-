# 全局Socket配置
HOST = "127.0.0.1"  # 本地回环，模拟车载局域网
SENSOR_PORT = 8001  # 传感器模块端口
ENGINE_PORT = 8002  # 发动机模块端口
DISPLAY_PORT = 8003 # 显示模块端口
MASTER_PORT = 8000  # 总控模块端口
BUFFER_SIZE = 1024  # 数据缓冲区大小
ENCODING = "utf-8"  # 数据编码格式

# 通信指令协议（字典转JSON传输）
# 指令格式：{"type": 指令类型, "data": 数据内容, "from": 发送模块, "to": 接收模块}
CMD_SPEED_REQUEST = "SPEED_REQUEST"  # 发动机请求车速
CMD_SPEED_RESPONSE = "SPEED_RESPONSE"# 传感器返回车速
CMD_MASTER_SPEED = "MASTER_SPEED"    # 总控下发车速到显示
CMD_ENGINE_CTRL = "ENGINE_CTRL"      # 总控控制发动机
CMD_ENGINE_STATUS = "ENGINE_STATUS"  # 发动机返回状态到总控