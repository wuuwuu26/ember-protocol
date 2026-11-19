# -*- coding: utf-8 -*-
"""
程序化音效生成 —— 不依赖任何外部音频素材。
================================================================

用户要求"游戏机制、体验进一步优化"。声音是**反馈闭环里缺失的一环**：
现在开火、命中、部位摧毁、冲刺、拾取全部是哑的，打击感少一半。

为什么程序化生成而不是找素材：
  ① 项目里没有任何音频资产，也没有素材来源；
  ② 这类"机器人/能量武器"的音效恰好是合成音频最擅长的领域
     （振荡器 + 噪声 + 包络就能做出很到位的机械感）；
  ③ 参数化生成 = 可迭代：不满意就改一行参数重跑，5 秒出新版本。

每个音效都由"基本波形（正弦/方波/噪声）+ 频率包络 + 幅度包络"合成，
写成 44.1kHz / 16-bit / 单声道 WAV。

用法: python tools/make_sfx.py [输出目录]
默认输出到 <项目>/assets/audio/
"""
import os
import sys
import wave

import numpy as np

SR = 44100
OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else \
    r"C:\Users\25227\Documents\robot_game\assets\audio"


# ─────────────────────────────────────────────
# 基础工具
# ─────────────────────────────────────────────

def t_axis(dur):
    return np.arange(int(SR * dur), dtype=np.float64) / SR


def env_exp(t, decay, attack=0.002):
    """指数衰减包络（带极短 attack，避免爆音 "pop"）。"""
    e = np.exp(-t * decay)
    a = np.clip(t / max(attack, 1e-5), 0.0, 1.0)
    return e * a


def chirp(t, f0, f1, curve=2.0):
    """频率从 f0 滑到 f1 的相位连续扫频（curve=2 为指数型，听起来更自然）。"""
    u = t / max(t[-1], 1e-6)
    k = (np.exp(curve * u) - 1.0) / (np.exp(curve) - 1.0)
    f = f0 + (f1 - f0) * k
    phase = 2.0 * np.pi * np.cumsum(f) / SR
    return np.sin(phase)


def noise(dur, rng):
    return rng.uniform(-1.0, 1.0, int(SR * dur))


def lowpass(x, window):
    """滑动平均做低通（window 越大越闷）。"""
    if window <= 1:
        return x
    k = np.ones(window) / window
    return np.convolve(x, k, mode="same")


def norm(x, peak=0.92):
    m = np.max(np.abs(x))
    return x * (peak / m) if m > 1e-6 else x


def write_wav(name, samples):
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, name)
    data = np.clip(samples, -1.0, 1.0)
    pcm = (data * 32767.0).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print("写出 %s  (%.2fs)" % (path, len(data) / SR))


def mix_at(base, add, at):
    """把 add 叠加到 base 的第 at 秒处（越界自动裁剪）。"""
    i = int(at * SR)
    n = min(len(add), len(base) - i)
    if n > 0:
        base[i:i + n] += add[:n]
    return base


# ─────────────────────────────────────────────
# 各音效
# ─────────────────────────────────────────────

def sfx_fire_player(rng):
    """玩家射击：高频"呲"—— 快速下滑的亮音 + 起始爆音。
    设计意图：高频短促 → 连发时叠起来不糊、不吵；
    下滑音头给"能量武器"的辨识度（区别于枪声）。
    """
    dur = 0.18
    t = t_axis(dur)
    body = chirp(t, 1500.0, 520.0) * env_exp(t, 22.0)
    crack = noise(0.012, rng) * np.exp(-np.arange(int(SR * 0.012)) / (SR * 0.0018))
    sub = np.sin(2 * np.pi * 220.0 * t) * env_exp(t, 30.0) * 0.25
    x = body + sub
    x = mix_at(x, crack * 0.9, 0.0)
    return norm(x)


def sfx_fire_enemy(rng):
    """敌人射击：同族但更低、更长 —— 一听就知道是"对面打过来的"。
    音高差是战场上区分敌我火力最直接的手段。
    """
    dur = 0.24
    t = t_axis(dur)
    body = chirp(t, 760.0, 240.0) * env_exp(t, 16.0)
    sub = np.sin(2 * np.pi * 120.0 * t) * env_exp(t, 20.0) * 0.35
    return norm(body + sub)


def sfx_impact(rng):
    """命中（打在装甲上）：短促的金属"叮"—— 噪声瞬态 + 金属振铃。"""
    dur = 0.11
    t = t_axis(dur)
    hit = noise(dur, rng) * env_exp(t, 70.0)
    ring = (np.sin(2 * np.pi * 2350.0 * t)
            + 0.5 * np.sin(2 * np.pi * 3170.0 * t)) * env_exp(t, 38.0)
    return norm(0.8 * hit + 0.5 * ring)


def sfx_destroy(rng):
    """部位摧毁：低频"轰" + 金属碎裂 + 下滑电容放电。
    是三段叠加：① 80Hz 低音鼓点 ② 噪声碎裂 ③ 1200→300 放电尾。
    """
    dur = 0.60
    t = t_axis(dur)
    boom = np.sin(2 * np.pi * 82.0 * t) * env_exp(t, 9.0)
    crackle = noise(dur, rng) * env_exp(t, 14.0)
    crackle = lowpass(crackle, 4)
    zap = chirp(t, 1200.0, 300.0) * env_exp(t, 11.0) * 0.5
    return norm(0.9 * boom + 0.55 * crackle + 0.45 * zap)


def sfx_dash(rng):
    """冲刺：气流"咻"—— 噪声 + 先扬后抑的包络（喷口打开→回稳）。"""
    dur = 0.38
    t = t_axis(dur)
    n = noise(dur, rng)
    n = lowpass(n, 6)
    u = t / dur
    env = np.sin(np.pi * np.clip(u / 0.8, 0, 1)) ** 1.5
    whoosh = n * env
    thrust = np.sin(2 * np.pi * 95.0 * t) * env_exp(t, 8.0) * 0.3
    return norm(whoosh * 0.9 + thrust)


def sfx_overheat(rng):
    """过热警报：两声急促方波"哔哔"。信息性强、不刺耳（880Hz 而非高频）。"""
    dur = 0.72
    x = np.zeros(int(SR * dur))
    for i, at in enumerate((0.0, 0.22)):
        t = t_axis(0.15)
        sq = np.sign(np.sin(2 * np.pi * 880.0 * t)) * 0.5
        # 方波过 harsh，混一点二次谐波柔化
        sq += 0.15 * np.sin(2 * np.pi * 1760.0 * t)
        # 第二声降低五度（提示"锁定了"而不仅是"警告"）
        if i == 1:
            sq = np.sign(np.sin(2 * np.pi * 587.0 * t)) * 0.5 \
                + 0.15 * np.sin(2 * np.pi * 1175.0 * t)
        x = mix_at(x, sq * env_exp(t, 9.0, 0.004), at)
    return norm(x)


def sfx_pickup(rng):
    """拾取废料：两音上行铃铛（660→990），短、亮、正反馈。"""
    dur = 0.30
    x = np.zeros(int(SR * dur))
    for f, at, amp in ((659.3, 0.0, 0.8), (987.8, 0.07, 0.9)):
        t = t_axis(0.26)
        bell = (np.sin(2 * np.pi * f * t)
                + 0.35 * np.sin(2 * np.pi * f * 2.0 * t)
                + 0.12 * np.sin(2 * np.pi * f * 3.0 * t))
        x = mix_at(x, bell * env_exp(t, 13.0, 0.003) * amp, at)
    return norm(x)


def sfx_ui_click(rng):
    """UI 确认音：极短的一下（菜单/按钮反馈用）。"""
    dur = 0.07
    t = t_axis(dur)
    click = np.sin(2 * np.pi * 1180.0 * t) * env_exp(t, 80.0, 0.001)
    tick = noise(dur, rng) * env_exp(t, 150.0) * 0.3
    return norm(click + tick, 0.7)


def main():
    rng = np.random.default_rng(20261014)
    write_wav("sfx_fire_player.wav", sfx_fire_player(rng))
    write_wav("sfx_fire_enemy.wav", sfx_fire_enemy(rng))
    write_wav("sfx_impact.wav", sfx_impact(rng))
    write_wav("sfx_destroy.wav", sfx_destroy(rng))
    write_wav("sfx_dash.wav", sfx_dash(rng))
    write_wav("sfx_overheat.wav", sfx_overheat(rng))
    write_wav("sfx_pickup.wav", sfx_pickup(rng))
    write_wav("sfx_ui_click.wav", sfx_ui_click(rng))
    print("完成：8 个音效写入 %s" % OUT_DIR)


main()
