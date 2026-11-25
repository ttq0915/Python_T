"""俄罗斯方块 —— 纯 Python 标准库实现（tkinter），无需安装任何依赖。

运行:
    python tetris.py

操作:
    ← →          左右移动（长按连发）
    ↓            软降
    ↑ / X        顺时针旋转
    Z / Ctrl     逆时针旋转
    A            180° 旋转
    空格         硬降
    C / Shift    暂存(Hold)
    P / Esc      暂停
    R            重新开始
"""

from __future__ import annotations

import math
import random
import time
import tkinter as tk
from pathlib import Path

# ------------------------------------------------------------------ 配置
COLS, ROWS = 10, 20          # 可视区域
BUFFER = 2                   # 顶部隐藏缓冲行
TOTAL = ROWS + BUFFER
CELL = 28                    # 每格像素
BOARD_W, BOARD_H = COLS * CELL, ROWS * CELL

PAD = 20                     # 窗口边距
SIDE_W = 150                 # 左右侧栏宽度
GAP = 14
BX = PAD + SIDE_W + GAP      # 棋盘左上角
BY = 62
RX = BX + BOARD_W + GAP      # 右侧栏左上角
W = RX + SIDE_W + PAD
H = BY + BOARD_H + 44

LOCK_DELAY = 0.5             # 落地延迟(秒)
MAX_LOCK_RESETS = 15
DAS = 0.15                   # 长按后开始连发的延迟
ARR = 0.042                  # 连发间隔

# 配色（暗色霓虹）
BG = "#070a12"
BOARD_BG = "#080b13"
PANEL = "#0d1220"
PANEL_LINE = "#1b2334"
GRID = "#131a29"
TEXT = "#e7ecff"
DIM = "#7b87a8"
CYAN = "#22d3ee"
PURPLE = "#c084fc"
GOLD = "#fbbf24"
RED = "#f43f5e"

COLORS = {
    "I": "#22d3ee", "J": "#3b82f6", "L": "#fb923c", "O": "#facc15",
    "S": "#4ade80", "T": "#c084fc", "Z": "#f43f5e",
}

F_TITLE = ("Microsoft YaHei UI", 16, "bold")
F_LABEL = ("Microsoft YaHei UI", 9)
F_SMALL = ("Microsoft YaHei UI", 8)
F_VALUE = ("Consolas", 17, "bold")
F_BIG = ("Microsoft YaHei UI", 17, "bold")
F_MID = ("Microsoft YaHei UI", 12, "bold")
F_HUGE = ("Microsoft YaHei UI", 26, "bold")

# 每个旋转态下 4 个方块的相对坐标（以包围盒左上角为原点）
SHAPES = {
    "I": [
        [(0, 1), (1, 1), (2, 1), (3, 1)],
        [(2, 0), (2, 1), (2, 2), (2, 3)],
        [(0, 2), (1, 2), (2, 2), (3, 2)],
        [(1, 0), (1, 1), (1, 2), (1, 3)],
    ],
    "J": [
        [(0, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (2, 2)],
        [(1, 0), (1, 1), (0, 2), (1, 2)],
    ],
    "L": [
        [(2, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (2, 2)],
        [(0, 1), (1, 1), (2, 1), (0, 2)],
        [(0, 0), (1, 0), (1, 1), (1, 2)],
    ],
    "O": [
        [(0, 0), (1, 0), (0, 1), (1, 1)],
        [(0, 0), (1, 0), (0, 1), (1, 1)],
        [(0, 0), (1, 0), (0, 1), (1, 1)],
        [(0, 0), (1, 0), (0, 1), (1, 1)],
    ],
    "S": [
        [(1, 0), (2, 0), (0, 1), (1, 1)],
        [(1, 0), (1, 1), (2, 1), (2, 2)],
        [(1, 1), (2, 1), (0, 2), (1, 2)],
        [(0, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "T": [
        [(1, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (1, 2)],
        [(1, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "Z": [
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(2, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (1, 2), (2, 2)],
        [(1, 0), (0, 1), (1, 1), (0, 2)],
    ],
}

# SRS 踢墙表（y 向下为正，已做过符号转换）
KICKS_JLSTZ = {
    (0, 1): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
    (1, 0): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
    (1, 2): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
    (2, 1): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
    (2, 3): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
    (3, 2): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
    (3, 0): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
    (0, 3): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
}
KICKS_I = {
    (0, 1): [(0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)],
    (1, 0): [(0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)],
    (1, 2): [(0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)],
    (2, 1): [(0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)],
    (2, 3): [(0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)],
    (3, 2): [(0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)],
    (3, 0): [(0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)],
    (0, 3): [(0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)],
}
KICKS_180 = [(0, 0), (0, -1), (1, 0), (-1, 0), (0, 1), (2, 0), (-2, 0)]

TYPES = ("I", "J", "L", "O", "S", "T", "Z")
BEST_FILE = Path(__file__).with_name("tetris_best.txt")


def shade(hex_color: str, p: float) -> str:
    """p>0 变亮，p<0 变暗。"""
    n = int(hex_color[1:], 16)
    r, g, b = (n >> 16) & 255, (n >> 8) & 255, n & 255
    if p >= 0:
        r, g, b = r + (255 - r) * p, g + (255 - g) * p, b + (255 - b) * p
    else:
        r, g, b = r * (1 + p), g * (1 + p), b * (1 + p)
    return "#%02x%02x%02x" % (int(r), int(g), int(b))


class Piece:
    __slots__ = ("type", "rot", "x", "y")

    def __init__(self, type_: str, x: int, y: int) -> None:
        self.type = type_
        self.rot = 0
        self.x = x
        self.y = y

    def cells(self, rot: int | None = None) -> list[tuple[int, int]]:
        return SHAPES[self.type][self.rot if rot is None else rot]


class Tetris:
    # -------------------------------------------------------------- 初始化
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title("俄罗斯方块 · TETRIS")
        root.configure(bg=BG)
        root.resizable(False, False)

        self.canvas = tk.Canvas(
            root, width=W, height=H, bg=BG, highlightthickness=0, bd=0
        )
        self.canvas.pack()

        self._center_window()
        self.best = self._load_best()

        self.board: list[list[str | None]] = []
        self.cur: Piece | None = None
        self.hold_type: str | None = None
        self.can_hold = True
        self.queue: list[str] = []
        self.bag: list[str] = []

        self.score = 0
        self.level = 1
        self.lines = 0
        self.combo = -1
        self.b2b = False

        self.state = "ready"          # ready / playing / paused / over
        self.gravity_t = 0.0
        self.lock_t = 0.0
        self.lock_resets = 0
        self.soft_t = 0.0
        self.clear_rows: list[int] = []
        self.clear_t = 0.0
        self.last_action = "move"
        self.last_kick = 0
        self.shake = 0.0

        self.toast_text = ""
        self.toast_ttl = 0.0

        self.held: set[str] = set()
        self.das_dir = 0
        self.das_t = 0.0
        self.arr_t = 0.0

        self.dirty = True

        self._shade_cache: dict[tuple[str, int], str] = {}
        self._build_static()
        self._bind_keys()

        self.reset()
        self.last_time = time.perf_counter()
        self.root.after(16, self.loop)

    def _center_window(self) -> None:
        self.root.update_idletasks()
        x = max(0, (self.root.winfo_screenwidth() - W) // 2)
        y = max(0, (self.root.winfo_screenheight() - H) // 2 - 24)
        self.root.geometry(f"{W}x{H}+{x}+{y}")

    # -------------------------------------------------------------- 静态界面
    def _build_static(self) -> None:
        c = self.canvas

        # 标题
        c.create_text(W // 2, 30, text="T E T R I S", fill=TEXT, font=F_TITLE)
        c.create_text(W // 2, 48, text="俄 罗 斯 方 块", fill=DIM, font=F_SMALL)

        # 棋盘区域
        c.create_rectangle(
            BX - 4, BY - 4, BX + BOARD_W + 4, BY + BOARD_H + 4,
            fill=BOARD_BG, outline="", width=0,
        )
        c.create_rectangle(
            BX - 4, BY - 4, BX + BOARD_W + 4, BY + BOARD_H + 4,
            fill="", outline="#28334d", width=1,
        )
        # 网格线
        for i in range(1, COLS):
            x = BX + i * CELL
            c.create_line(x, BY, x, BY + BOARD_H, fill=GRID)
        for j in range(1, ROWS):
            y = BY + j * CELL
            c.create_line(BX, y, BX + BOARD_W, y, fill=GRID)

        # 左侧 HOLD 面板
        self._panel(PAD, BY, SIDE_W, 100, "H O L D")
        # 左侧数据面板
        self._panel(PAD, BY + 112, SIDE_W, 274, "S T A T S")

        # 右侧 NEXT 面板
        self._panel(RX, BY, SIDE_W, 372, "N E X T")
        # 右侧按键说明
        self._panel(RX, BY + 384, SIDE_W, BOARD_H - 384, "K E Y S")
        keys = [
            ("移动", "← →"), ("软降", "↓"), ("旋转", "↑ X"),
            ("逆旋", "Z"), ("硬降", "空格"), ("暂存", "C"),
            ("暂停", "P"), ("重开", "R"),
        ]
        ky = BY + 384 + 40
        for name, key in keys:
            c.create_text(RX + 12, ky, text=name, anchor="w", fill=DIM, font=F_SMALL)
            c.create_text(RX + SIDE_W - 12, ky, text=key, anchor="e", fill="#cfd7f0",
                          font=F_SMALL)
            ky += 18

    def _panel(self, x: int, y: int, w: int, h: int, title: str) -> None:
        c = self.canvas
        c.create_rectangle(x, y, x + w, y + h, fill=PANEL, outline=PANEL_LINE, width=1)
        c.create_text(x + w // 2, y + 15, text=title, fill=DIM, font=F_SMALL)

    # -------------------------------------------------------------- 绘制方块
    def _blk(self, x: float, y: float, size: float, color: str, ghost: bool = False) -> None:
        c = self.canvas
        if ghost:
            c.create_rectangle(x + 2, y + 2, x + size - 2, y + size - 2,
                               outline=color, width=2, tags="dyn")
            c.create_rectangle(x + 4, y + 4, x + size - 4, y + size - 4,
                               fill=color, outline="", stipple="gray25", tags="dyn")
            return

        key_l = (color, 1)
        key_d = (color, -1)
        if key_l not in self._shade_cache:
            self._shade_cache[key_l] = shade(color, 0.42)
            self._shade_cache[key_d] = shade(color, -0.4)
        light = self._shade_cache[key_l]
        edge = self._shade_cache[key_d]

        c.create_rectangle(x, y, x + size - 1, y + size - 1,
                           fill=color, outline=edge, width=1, tags="dyn")
        # 顶部高光
        c.create_rectangle(x + 2, y + 2, x + size - 3, y + 5,
                           fill=light, outline="", tags="dyn")
        # 左下暗面
        c.create_line(x + 1, y + size - 2, x + size - 2, y + size - 2,
                      fill=edge, tags="dyn")

    def _piece_center(self, type_: str, cx: float, cy: float, size: float,
                      dim: bool = False) -> None:
        cells = SHAPES[type_][0]
        xs = [p[0] for p in cells]
        ys = [p[1] for p in cells]
        minx, maxx = min(xs), max(xs)
        miny, maxy = min(ys), max(ys)
        w = (maxx - minx + 1) * size
        h = (maxy - miny + 1) * size
        ox, oy = cx - w / 2, cy - h / 2
        color = shade(COLORS[type_], -0.55) if dim else COLORS[type_]
        for px, py in cells:
            self._blk(ox + (px - minx) * size, oy + (py - miny) * size, size, color)

    # -------------------------------------------------------------- 主绘制
    def draw(self) -> None:
        c = self.canvas
        c.delete("dyn")
        t = "dyn"

        sx = sy = 0.0
        if self.shake > 0:
            sx = (random.random() - 0.5) * self.shake * 3
            sy = (random.random() - 0.5) * self.shake * 3

        # 已固定的方块
        for r in range(BUFFER, TOTAL):
            row = self.board[r]
            for col in range(COLS):
                if row[col]:
                    self._blk(BX + col * CELL + sx, BY + (r - BUFFER) * CELL + sy,
                              CELL, COLORS[row[col]])

        # 幽灵落点
        cur = self.cur
        if cur is not None:
            gy = cur.y
            while not self._collides(cur.type, cur.rot, cur.x, gy + 1):
                gy += 1
            if gy != cur.y:
                for px, py in cur.cells():
                    row = gy + py
                    if row < BUFFER:
                        continue
                    self._blk(BX + (cur.x + px) * CELL + sx,
                              BY + (row - BUFFER) * CELL + sy,
                              CELL, COLORS[cur.type], ghost=True)

            for px, py in cur.cells():
                row = cur.y + py
                if row < BUFFER:
                    continue
                self._blk(BX + (cur.x + px) * CELL + sx,
                          BY + (row - BUFFER) * CELL + sy,
                          CELL, COLORS[cur.type])

        # 消行动画
        if self.clear_rows:
            p = min(1.0, self.clear_t / 0.22)
            for r in self.clear_rows:
                y = BY + (r - BUFFER) * CELL + sy
                hh = CELL * (1 - p * 0.85)
                c.create_rectangle(BX + sx, y + (CELL - hh) / 2,
                                   BX + BOARD_W + sx, y + (CELL + hh) / 2,
                                   fill="#eafcff", outline="", tags=t)

        # HOLD 预览
        if self.hold_type:
            self._piece_center(self.hold_type, PAD + SIDE_W / 2, BY + 58, 17,
                               dim=not self.can_hold)
        else:
            c.create_text(PAD + SIDE_W / 2, BY + 58, text="—", fill="#3d4761",
                          font=F_LABEL, tags=t)

        # NEXT 预览
        slot_h = (372 - 30) / 5
        for i in range(5):
            if i >= len(self.queue):
                break
            cy = BY + 30 + slot_h * i + slot_h / 2
            if i == 0:
                c.create_rectangle(RX + 6, BY + 30 + slot_h * i + 2,
                                   RX + SIDE_W - 6, BY + 30 + slot_h * (i + 1) - 2,
                                   fill="#101a2c", outline="#1d2c46", tags=t)
            self._piece_center(self.queue[i], RX + SIDE_W / 2, cy, 15)

        # 数据
        stats = [
            ("得分", str(self.score), CYAN),
            ("最高分", str(self.best), TEXT),
            ("等级", str(self.level), PURPLE),
            ("消行", str(self.lines), TEXT),
            ("连击", "×%d" % (self.combo + 1) if self.combo >= 1 else "—", GOLD),
        ]
        y0 = BY + 112 + 42
        for i, (name, val, color) in enumerate(stats):
            yy = y0 + i * 46
            c.create_text(PAD + SIDE_W / 2, yy, text=name, fill=DIM, font=F_LABEL, tags=t)
            c.create_text(PAD + SIDE_W / 2, yy + 20, text=val, fill=color,
                          font=F_VALUE, tags=t)

        # 浮动提示
        if self.toast_ttl > 0 and self.toast_text:
            k = min(1.0, self.toast_ttl / 0.25)
            col = shade("#ffffff", -(1 - k) * 0.75)
            c.create_text(BX + BOARD_W / 2, BY + BOARD_H * 0.28,
                          text=self.toast_text, fill=col, font=F_BIG, tags=t,
                          justify="center")

        # 状态遮罩
        if self.state != "playing":
            c.create_rectangle(BX - 4, BY - 4, BX + BOARD_W + 4, BY + BOARD_H + 4,
                               fill="#05070d", outline="", stipple="gray50", tags=t)
            cx = BX + BOARD_W / 2
            cy = BY + BOARD_H / 2
            if self.state == "ready":
                c.create_text(cx, cy - 70, text="俄 罗 斯 方 块", fill=TEXT,
                              font=F_HUGE, tags=t)
                c.create_text(cx, cy - 26, text="按 空格 开始游戏", fill=CYAN,
                              font=F_MID, tags=t)
                c.create_text(
                    cx, cy + 30,
                    text="← →  移动      ↑  旋转\n空格  硬降      C  暂存\nP  暂停        R  重开",
                    fill=DIM, font=F_LABEL, justify="center", tags=t,
                )
            elif self.state == "paused":
                c.create_text(cx, cy - 16, text="已 暂 停", fill=TEXT,
                              font=F_HUGE, tags=t)
                c.create_text(cx, cy + 34, text="按 P 继续 · 按 R 重开", fill=DIM,
                              font=F_LABEL, tags=t)
            elif self.state == "over":
                c.create_text(cx, cy - 76, text="游 戏 结 束", fill=RED,
                              font=F_BIG, tags=t)
                c.create_text(cx, cy - 24, text=str(self.score), fill=TEXT,
                              font=F_HUGE, tags=t)
                c.create_text(cx, cy + 22,
                              text="消行 %d · 等级 %d" % (self.lines, self.level),
                              fill=DIM, font=F_LABEL, tags=t)
                c.create_text(cx, cy + 62, text="按 空格 重新开始", fill=CYAN,
                              font=F_MID, tags=t)

    # -------------------------------------------------------------- 逻辑
    def reset(self) -> None:
        self.board = [[None] * COLS for _ in range(TOTAL)]
        self.cur = None
        self.hold_type = None
        self.can_hold = True
        self.queue = []
        self.bag = []
        self.score = 0
        self.level = 1
        self.lines = 0
        self.combo = -1
        self.b2b = False
        self.gravity_t = 0.0
        self.lock_t = 0.0
        self.lock_resets = 0
        self.soft_t = 0.0
        self.clear_rows = []
        self.clear_t = 0.0
        self.last_action = "move"
        self.shake = 0.0
        self.toast_text = ""
        self.toast_ttl = 0.0
        self.state = "ready"
        self._refill_queue()
        self.dirty = True

    def start(self) -> None:
        self.reset()
        self.state = "playing"
        self._spawn()
        self.dirty = True

    def _refill_bag(self) -> None:
        bag = list(TYPES)
        random.shuffle(bag)
        self.bag = bag

    def _pull(self) -> str:
        if not self.bag:
            self._refill_bag()
        return self.bag.pop()

    def _refill_queue(self) -> None:
        while len(self.queue) < 6:
            self.queue.append(self._pull())

    def _spawn(self) -> None:
        self._refill_queue()
        type_ = self.queue.pop(0)
        self._refill_queue()
        x = 4 if type_ == "O" else 3
        self.cur = Piece(type_, x, BUFFER)
        self.can_hold = True
        self.gravity_t = 0.0
        self.lock_t = 0.0
        self.lock_resets = 0
        self.last_action = "move"
        if self._collides(type_, 0, x, BUFFER):
            self._game_over()
        self.dirty = True

    def _collides(self, type_: str, rot: int, px: int, py: int) -> bool:
        for cx, cy in SHAPES[type_][rot & 3]:
            bx, by = px + cx, py + cy
            if bx < 0 or bx >= COLS or by >= TOTAL:
                return True
            if by < 0:
                continue
            if self.board[by][bx]:
                return True
        return False

    def _grounded(self) -> bool:
        if self.cur is None:
            return False
        return self._collides(self.cur.type, self.cur.rot, self.cur.x, self.cur.y + 1)

    def _touch_ground(self) -> None:
        if self.cur is None:
            return
        if self._grounded() and self.lock_t > 0 and self.lock_resets < MAX_LOCK_RESETS:
            self.lock_t = 0.0
            self.lock_resets += 1

    def move(self, dx: int) -> bool:
        p = self.cur
        if p is None:
            return False
        if self._collides(p.type, p.rot, p.x + dx, p.y):
            return False
        p.x += dx
        self.last_action = "move"
        self.dirty = True
        return True

    def _down(self, player: bool) -> bool:
        p = self.cur
        if p is None:
            return False
        if self._collides(p.type, p.rot, p.x, p.y + 1):
            return False
        p.y += 1
        if player:
            self.score += 1
        self.dirty = True
        return True

    def rotate(self, direction: int) -> None:
        p = self.cur
        if p is None:
            return
        frm = p.rot
        to = (frm + direction) % 4
        if direction == 2:
            kicks = KICKS_180
        else:
            table = KICKS_I if p.type == "I" else KICKS_JLSTZ
            kicks = table.get((frm, to), [(0, 0)])
        for i, (kx, ky) in enumerate(kicks):
            nx, ny = p.x + kx, p.y + ky
            if not self._collides(p.type, to, nx, ny):
                p.rot = to
                p.x, p.y = nx, ny
                self.last_action = "rotate"
                self.last_kick = i
                self._touch_ground()
                self.dirty = True
                return

    def hard_drop(self) -> None:
        p = self.cur
        if p is None:
            return
        dist = 0
        while not self._collides(p.type, p.rot, p.x, p.y + 1):
            p.y += 1
            dist += 1
        self.score += dist * 2
        self.shake = min(3.0, 1.4 + dist * 0.05)
        self._lock()

    def hold(self) -> None:
        p = self.cur
        if p is None or not self.can_hold:
            return
        cur_type = p.type
        if self.hold_type is None:
            self.hold_type = cur_type
            self.cur = None
            self._spawn()
        else:
            h = self.hold_type
            self.hold_type = cur_type
            x = 4 if h == "O" else 3
            self.cur = Piece(h, x, BUFFER)
            self.lock_t = 0.0
            self.lock_resets = 0
            self.gravity_t = 0.0
            self.last_action = "move"
            if self._collides(self.cur.type, 0, self.cur.x, self.cur.y):
                self._game_over()
                return
        self.can_hold = False
        self.dirty = True

    # -------------------------------------------------------------- 锁定/消行
    def _tspin(self, p: Piece) -> str | None:
        if p.type != "T" or self.last_action != "rotate":
            return None
        corners = [(p.x, p.y), (p.x + 2, p.y), (p.x, p.y + 2), (p.x + 2, p.y + 2)]
        occ = []
        for cx, cy in corners:
            if cx < 0 or cx >= COLS or cy >= TOTAL:
                occ.append(True)
            elif cy < 0:
                occ.append(False)
            else:
                occ.append(bool(self.board[cy][cx]))
        if sum(occ) < 3:
            return None
        front = [(0, 1), (1, 3), (2, 3), (0, 2)][p.rot]
        if not (occ[front[0]] and occ[front[1]]) and self.last_kick != 4:
            return "mini"
        return "full"

    def _lock(self) -> None:
        p = self.cur
        if p is None:
            return
        for cx, cy in p.cells():
            bx, by = p.x + cx, p.y + cy
            if 0 <= by < TOTAL and 0 <= bx < COLS:
                self.board[by][bx] = p.type

        tspin = self._tspin(p)
        self.cur = None

        full = [r for r in range(TOTAL) if all(self.board[r])]
        n = len(full)
        points = 0
        difficult = False

        if tspin == "full":
            points = [400, 800, 1200, 1600][n]
            difficult = n > 0
        elif tspin == "mini":
            points = [100, 200, 400, 600][n]
            difficult = n > 0
        elif n > 0:
            points = [0, 100, 300, 500, 800][n]
            difficult = n == 4

        if n > 0:
            self.combo += 1
            if self.b2b and difficult:
                points = int(points * 1.5)
            if self.combo > 0:
                points += 50 * self.combo
        else:
            self.combo = -1
        points *= self.level
        self.score += points

        if n > 0:
            self.b2b = difficult

        # 提示文字
        label = ""
        if tspin in ("full", "mini"):
            names = ["", " SINGLE", " DOUBLE", " TRIPLE"]
            label = "T-SPIN" + names[n]
        elif n == 4:
            label = "TETRIS"
        elif n == 3:
            label = "TRIPLE"
        elif n == 2:
            label = "DOUBLE"
        if self.combo >= 1:
            label = (label + "  " if label else "") + "COMBO ×%d" % (self.combo + 1)
        if label:
            self._toast(label)

        if n > 0:
            before = self.lines // 10
            self.lines += n
            self.level = min(20, self.lines // 10 + 1)
            if self.lines // 10 > before:
                self._toast("LEVEL %d" % self.level)
            self.clear_rows = full
            self.clear_t = 0.0
        else:
            self._spawn()

        self.lock_t = 0.0
        self.lock_resets = 0
        self.dirty = True

    def _remove_rows(self, rows: list[int]) -> None:
        for r in sorted(rows):
            self.board.pop(r)
            self.board.insert(0, [None] * COLS)

    def _game_over(self) -> None:
        self.state = "over"
        self.cur = None
        if self.score > self.best:
            self.best = self.score
            self._save_best()
        self.dirty = True

    def _toast(self, text: str) -> None:
        self.toast_text = text
        self.toast_ttl = 1.0

    # -------------------------------------------------------------- 分数存档
    def _load_best(self) -> int:
        try:
            return int(BEST_FILE.read_text(encoding="utf-8").strip())
        except Exception:
            return 0

    def _save_best(self) -> None:
        try:
            BEST_FILE.write_text(str(self.best), encoding="utf-8")
        except Exception:
            pass

    # -------------------------------------------------------------- 主循环
    def gravity_interval(self) -> float:
        lv = min(self.level, 20)
        try:
            base = 1000.0 * math.pow(0.8 - (lv - 1) * 0.007, lv - 1)
        except (ValueError, OverflowError):
            base = 1000.0
        return max(0.042, base / 1000.0)

    def loop(self) -> None:
        now = time.perf_counter()
        dt = now - self.last_time
        self.last_time = now
        if dt > 0.05:
            dt = 0.05
        self.update(dt)
        if self.dirty:
            self.dirty = False
            self.draw()
        self.root.after(16, self.loop)

    def update(self, dt: float) -> None:
        if self.shake > 0:
            self.shake = max(0.0, self.shake - dt * 18)
            self.dirty = True
        if self.toast_ttl > 0:
            self.toast_ttl = max(0.0, self.toast_ttl - dt)
            self.dirty = True

        if self.state != "playing":
            return

        # 消行动画
        if self.clear_rows:
            self.clear_t += dt
            self.dirty = True
            if self.clear_t >= 0.22:
                self._remove_rows(self.clear_rows)
                self.clear_rows = []
                self._spawn()
            return

        if self.cur is None:
            return

        # 左右长按连发
        if self.das_dir:
            self.das_t += dt
            if self.das_t >= DAS:
                self.arr_t += dt
                guard = 0
                while self.arr_t >= ARR and guard < 6:
                    self.arr_t -= ARR
                    guard += 1
                    if not self.move(self.das_dir):
                        break
                if guard:
                    self._touch_ground()

        # 软降 / 重力
        if "Down" in self.held:
            interval = max(0.022, self.gravity_interval() / 16)
            self.soft_t += dt
            guard = 0
            while self.soft_t >= interval and guard < 8:
                self.soft_t -= interval
                guard += 1
                if not self._down(True):
                    break
            self.gravity_t = 0.0
        else:
            self.soft_t = 0.0
            self.gravity_t += dt
            if self.gravity_t >= self.gravity_interval():
                self.gravity_t = 0.0
                self._down(False)

        # 落地延迟
        if self._grounded():
            self.lock_t += dt
            if self.lock_t >= LOCK_DELAY:
                self._lock()
        else:
            self.lock_t = 0.0

    # -------------------------------------------------------------- 键盘
    def _bind_keys(self) -> None:
        self.root.bind("<KeyPress>", self.on_key)
        self.root.bind("<KeyRelease>", self.on_key_up)
        self.root.bind("<FocusOut>", self._on_focus_out)
        self.canvas.focus_set()

    def _on_focus_out(self, event: tk.Event) -> None:
        if event.widget is not self.root and event.widget is not self.canvas:
            return
        self.held.clear()
        self.das_dir = 0
        if self.state == "playing":
            self.toggle_pause()

    def on_key(self, event: tk.Event) -> None:
        ks = event.keysym
        if ks in self.held:
            return                      # 过滤系统自动重复
        self.held.add(ks)

        if self.state in ("ready", "over"):
            if ks in ("space", "Return", "r", "R"):
                self.start()
            return

        if ks in ("p", "P", "Escape"):
            self.toggle_pause()
            return
        if ks in ("r", "R"):
            self.start()
            return
        if self.state != "playing":
            return

        if ks == "Left":
            self._start_move(-1)
        elif ks == "Right":
            self._start_move(1)
        elif ks == "Down":
            pass
        elif ks in ("Up", "x", "X"):
            self.rotate(1)
        elif ks in ("z", "Z", "Control_L", "Control_R"):
            self.rotate(-1)
        elif ks in ("a", "A"):
            self.rotate(2)
        elif ks == "space":
            self.hard_drop()
        elif ks in ("c", "C", "Shift_L", "Shift_R"):
            self.hold()

    def on_key_up(self, event: tk.Event) -> None:
        ks = event.keysym
        self.held.discard(ks)
        if ks in ("Left", "Right"):
            direction = -1 if ks == "Left" else 1
            if self.das_dir == direction:
                other = "Right" if direction == -1 else "Left"
                self.das_dir = (1 if direction == -1 else -1) if other in self.held else 0
                self.das_t = 0.0
                self.arr_t = 0.0

    def _start_move(self, direction: int) -> None:
        if self.das_dir != direction:
            self.das_dir = direction
            self.das_t = 0.0
            self.arr_t = 0.0
            if self.move(direction):
                self._touch_ground()

    def toggle_pause(self) -> None:
        if self.state == "playing":
            self.state = "paused"
        elif self.state == "paused":
            self.state = "playing"
            self.last_time = time.perf_counter()
        self.das_dir = 0
        self.dirty = True


def main() -> None:
    root = tk.Tk()
    Tetris(root)
    root.mainloop()


if __name__ == "__main__":
    main()
