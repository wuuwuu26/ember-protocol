"""打印 UE 远程执行的原始组播报文，用于确定消息格式。"""

import json
import socket
import struct
import sys
import time

GROUP = "239.0.0.1"
PORT = 6766

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(("", PORT))
mreq = struct.pack("4sl", socket.inet_aton(GROUP), socket.INADDR_ANY)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
sock.settimeout(1.0)

# 发一个 ping 触发回应
ping = json.dumps({"version": 1, "type": "ping", "id": "raw-dump"})
sock.sendto(ping.encode("utf-8"), (GROUP, PORT))
print("已发送 ping，等待回应……")

seen = set()
deadline = time.time() + 4
while time.time() < deadline:
    try:
        data, addr = sock.recvfrom(65536)
    except socket.timeout:
        continue
    except OSError as e:
        print("接收错误: %s" % e)
        break
    key = (addr, data[:80])
    if key in seen:
        continue
    seen.add(key)
    print("-" * 60)
    print("来自: %s:%d  长度=%d" % (addr[0], addr[1], len(data)))
    raw = data.rstrip(b"\x00")
    try:
        txt = raw.decode("utf-8")
        print("原文: %s" % txt[:800])
        try:
            obj = json.loads(txt)
            print("解析后的字段:")
            for k, v in obj.items():
                print("   %s = %r" % (k, v))
        except Exception as e:
            print("JSON 解析失败: %s" % e)
    except Exception as e:
        print("解码失败: %s" % e)
        print("十六进制: %s" % data[:200].hex())

sock.close()
print("-" * 60)
print("结束")
