"""
UE Python 远程执行客户端（含自动发现）
================================================================
UE 的 Python 远程执行：
  1. 编辑器在 UDP 组播 239.0.0.1:6766 上广播自己的 TCP 端口
  2. 客户端连上那个 TCP 端口，发 JSON 指令

本脚本自动完成发现 + 连接 + 执行。

用法:
    python ue_connect.py "<要执行的 Python 代码>"
    python ue_connect.py --file <脚本路径>
    python ue_connect.py --discover        # 只做发现，看有哪些编辑器在线
"""

import json
import os
import socket
import struct
import sys
import time

MULTICAST_GROUP = "239.0.0.1"
MULTICAST_PORT = 6766


def discover(timeout=3.0):
    """通过 UDP 组播发现在线的编辑器，返回 [(ip, port, project), ...]"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                         socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(("", MULTICAST_PORT))
    except OSError as e:
        print("绑定 %d 失败: %s" % (MULTICAST_PORT, e))
        return []
    mreq = struct.pack("4sl", socket.inet_aton(MULTICAST_GROUP),
                       socket.INADDR_ANY)
    try:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    except OSError as e:
        print("加入组播组失败: %s" % e)
        sock.close()
        return []
    sock.settimeout(timeout)

    # 先发一个 ping，促使编辑器回应
    ping = json.dumps({"version": 1, "type": "ping", "id": "wb-disc"})
    try:
        sock.sendto(ping.encode("utf-8"), (MULTICAST_GROUP, MULTICAST_PORT))
    except OSError:
        pass

    found = []
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            data, addr = sock.recvfrom(65536)
        except socket.timeout:
            break
        except OSError:
            break
        try:
            msg = json.loads(data.split(b"\x00")[0].decode("utf-8", "replace"))
        except Exception:
            continue
        if msg.get("type") in ("ping", "pong"):
            found.append((msg.get("ip_address") or addr[0],
                          msg.get("port"),
                          msg.get("project_name", "?")))
    sock.close()
    return found


def exec_remote(ip, port, code, timeout=120.0):
    """连上编辑器执行代码，返回输出行。"""
    msg = {
        "version": 1,
        "type": "exec_command",
        "command": code,
        "command_mode": "EvaluateStatement",
        "id": "wb-exec",
    }
    payload = json.dumps(msg).encode("utf-8") + b"\x00"

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((ip, port))
        s.sendall(payload)
        buf = b""
        while b"\x00" not in buf:
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
        text = buf.split(b"\x00")[0].decode("utf-8", "replace")
        data = json.loads(text)
        if data.get("success"):
            return data.get("output", [])
        return ["失败: %s" % data.get("error", data)]
    except Exception as e:
        return ["连接/执行失败: %s" % e]
    finally:
        s.close()


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1

    # 只发现
    if args[0] == "--discover":
        print("=== 搜索在线的 UE 编辑器（UDP 组播 %s:%d）===" %
              (MULTICAST_GROUP, MULTICAST_PORT))
        found = discover()
        if not found:
            print("  没找到。检查：")
            print("  1. 编辑器是否已重启（配置改动需要重启生效）")
            print("  2. DefaultEngine.ini 里 bRemoteExecution=True 是否生效")
            print("  3. 防火墙是否拦了 UDP 6766")
        for ip, port, proj in found:
            print("  ✅ %s:%s  项目=%s" % (ip, port, proj))
        return 0

    # 从文件读代码
    if args[0] == "--file":
        with open(args[1], "r", encoding="utf-8") as f:
            code = f.read()
    else:
        code = args[0]

    found = discover()
    if not found:
        print("❌ 没发现编辑器，先跑 --discover 排查")
        return 1

    ip, port, proj = found[0]
    print("连接 %s:%s（%s）" % (ip, port, proj))
    for line in exec_remote(ip, port, code):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
