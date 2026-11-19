"""
尝试多种消息格式连接 UE Python 远程执行端口
================================================================
UE 的远程执行协议在不同版本间有差异，这里逐个变体试，
找到能通的那一种。
"""

import json
import socket
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 35834
CODE = "print('REMOTE-OK')"


def try_variant(name, payload, wait_for_response=True, timeout=8.0):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect(("127.0.0.1", PORT))
    except Exception as e:
        print("  [%s] 连接失败: %s" % (name, e))
        s.close()
        return False

    try:
        s.sendall(payload)
    except Exception as e:
        print("  [%s] 发送失败: %s" % (name, e))
        s.close()
        return False

    if not wait_for_response:
        print("  [%s] 已发送，未等响应" % name)
        s.close()
        return True

    try:
        buf = b""
        while b"\x00" not in buf and len(buf) < 65536:
            chunk = s.recv(4096)
            if not chunk:
                break
            buf += chunk
        text = buf.split(b"\x00")[0].decode("utf-8", errors="replace")
        if text:
            print("  [%s] ✅ 收到响应: %s" % (name, text[:300]))
            s.close()
            return True
        print("  [%s] 收到空响应" % name)
    except socket.timeout:
        print("  [%s] 超时（无响应）" % name)
    except Exception as e:
        print("  [%s] 接收异常: %s" % (name, e))
    s.close()
    return False


def main():
    base = {
        "version": 1,
        "type": "exec_command",
        "command": CODE,
        "command_mode": "EvaluateStatement",
        "id": "wb1",
    }
    js = json.dumps(base)

    print("=== 尝试各种消息格式（端口 %d）===" % PORT)

    # 变体 1：JSON + \0
    try_variant("JSON+NULL", js.encode("utf-8") + b"\x00")

    # 变体 2：纯 JSON
    try_variant("JSON", js.encode("utf-8"))

    # 变体 3：JSON + \n
    try_variant("JSON+LF", js.encode("utf-8") + b"\n")

    # 变体 4：先发 ping
    ping = json.dumps({"version": 1, "type": "ping", "id": "wb0"})
    try_variant("PING+NULL", ping.encode("utf-8") + b"\x00")

    # 变体 5：4 字节长度前缀 + JSON
    b = js.encode("utf-8")
    try_variant("LEN+JSON", len(b).to_bytes(4, "little") + b)

    # 变体 6：command_mode = ExecuteStatement
    alt = dict(base, command_mode="ExecuteStatement")
    try_variant("ExecStatement+NULL",
                json.dumps(alt).encode("utf-8") + b"\x00")

    print("=== 尝试结束 ===")


main()
