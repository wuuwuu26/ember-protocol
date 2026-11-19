"""
连接到运行中的 UE 编辑器的 Python 远程执行端口，执行代码
================================================================
UE 的 PythonScriptPlugin 会监听一个 TCP 端口（随机），并通过 UDP 6666 广播。
这里直接连已知的端口发 JSON 指令。

协议（来自 PythonScriptRemoteExecution.cpp）：
    发送：JSON 字符串 + \0 结尾
    接收：JSON 结果 + \0 结尾

用法:
    python ue_remote.py "<端口>" "<要执行的 Python 代码>"
"""

import json
import socket
import sys


def send_command(port, code, mode="EvaluateStatement", timeout=60.0):
    """连接并执行一段 Python 代码，返回结果文本。"""
    msg = {
        "version": 1,
        "type": "exec_command",
        "command": code,
        "command_mode": mode,
        "id": "wb-diag",
    }
    payload = json.dumps(msg).encode("utf-8") + b"\x00"

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect(("127.0.0.1", port))
        s.sendall(payload)

        # 收响应，直到遇到 \0
        buf = b""
        while b"\x00" not in buf:
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
        text = buf.split(b"\x00")[0].decode("utf-8", errors="replace")
        return text
    except Exception as e:
        return "连接失败: %s" % e
    finally:
        s.close()


def main():
    if len(sys.argv) < 3:
        print("用法: python ue_remote.py <端口> <代码>")
        return 1

    port = int(sys.argv[1])
    code = sys.argv[2]

    result = send_command(port, code)

    # 结果也是 JSON，解析出输出
    try:
        data = json.loads(result)
        print("类型:", data.get("type"))
        if data.get("success"):
            out = data.get("output", [])
            for line in out:
                print(line)
        else:
            print("失败:", data.get("error", data))
    except Exception:
        print("原始响应:", result[:2000])

    return 0


if __name__ == "__main__":
    sys.exit(main())
