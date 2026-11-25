"""贪吃蛇小游戏 —— 纯 Python 标准库实现（tkinter），无需安装任何依赖。

运行:
    python snake_game.py

操作:
    方向键 / WASD   移动
    空格            暂停 / 继续
    R 或 Enter      重新开始
    Esc             退出
"""

from __future__ import annotations

import random
import tkinter as tk
from collections import deque

# ------------------------------------------------------------------ 配置
CELL = 24                 # 每个格子像素
COLS, ROWS = 24, 24       # 横向 / 纵向格子数
W, H = CELL * COLS, CELL * ROWS

START_DELAY = 150         # 初始移动间隔(毫秒)，越小越快
MIN_DELAY = 60            # 速度上限
SPEED_UP = 4              # 每吃一个食物加快多少毫秒

BG = "#0f1220"
GRID_LINE = "#191d2f"
SNAKE_HEAD = "#8ef7ae"
SNAKE_BODY = "#37c273"
SNAKE_EDGE = "#0b3d22"
FOOD_COLOR = "#ff5d73"
TEXT = "#e8ecff"
DIM = "#8b93b5"
ACCENT = "#ffd166"

UP, DOWN, LEFT, RIGHT = (0, -1), (0, 1), (-1, 0), (1, 0)


class SnakeGame:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title("贪吃蛇 · Snake")
        root.configure(bg=BG)
        root.resizable(False, False)

        self.best = 0
        self.delay = START_DELAY
        self.timer: str | None = None
        self.alive = False
        self.paused = False

        self._build_ui()
        self._bind_keys()
        self.reset()

    # -------------------------------------------------------------- 界面
    def _build_ui(self) -> None:
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=16, pady=(12, 6))

        tk.Label(
            header, text="🐍 贪吃蛇", bg=BG, fg=TEXT,
            font=("Microsoft YaHei", 16, "bold"),
        ).pack(side="left")

        self.best_var = tk.StringVar(value="最高 0")
        tk.Label(
            header, textvariable=self.best_var, bg=BG, fg=DIM,
            font=("Microsoft YaHei", 11),
        ).pack(side="right")

        self.score_var = tk.StringVar(value="得分 0")
        tk.Label(
            header, textvariable=self.score_var, bg=BG, fg=ACCENT,
            font=("Microsoft YaHei", 13, "bold"),
        ).pack(side="right", padx=(0, 18))

        self.canvas = tk.Canvas(
            self.root, width=W, height=H, bg=BG, highlightthickness=0,
        )
        self.canvas.pack(padx=16)

        tk.Label(
            self.root,
            text="方向键 / WASD 移动　空格 暂停　R 重开　Esc 退出",
            bg=BG, fg=DIM, font=("Microsoft YaHei", 9),
        ).pack(pady=(8, 12))

    def _bind_keys(self) -> None:
        self.root.bind("<Key>", self._on_key)
        self.canvas.bind("<Button-1>", lambda _e: self.canvas.focus_set())
        self.canvas.focus_set()

    # -------------------------------------------------------------- 逻辑
    def reset(self) -> None:
        self._stop_timer()

        cx, cy = COLS // 2, ROWS // 2
        self.snake: deque[tuple[int, int]] = deque(
            [(cx, cy), (cx - 1, cy), (cx - 2, cy)]
        )
        self.direction = RIGHT
        self.pending: deque[tuple[int, int]] = deque()

        self.score = 0
        self.delay = START_DELAY
        self.alive = True
        self.paused = False
        self.score_var.set("得分 0")

        self._spawn_food()
        self._render()
        self._schedule()

    def _spawn_food(self) -> None:
        occupied = set(self.snake)
        free = [
            (x, y)
            for x in range(COLS)
            for y in range(ROWS)
            if (x, y) not in occupied
        ]
        self.food = random.choice(free) if free else None

    def _schedule(self) -> None:
        self._stop_timer()
        self.timer = self.root.after(self.delay, self._tick)

    def _stop_timer(self) -> None:
        if self.timer is not None:
            self.root.after_cancel(self.timer)
            self.timer = None

    def _tick(self) -> None:
        self.timer = None
        if not self.alive or self.paused:
            return
        self._step()
        if self.alive and not self.paused:
            self._schedule()

    def _step(self) -> None:
        # 取出这一步的方向（忽略反向）
        if self.pending:
            nd = self.pending.popleft()
            if nd != (-self.direction[0], -self.direction[1]):
                self.direction = nd

        hx, hy = self.snake[0]
        nx, ny = hx + self.direction[0], hy + self.direction[1]

        hit_wall = not (0 <= nx < COLS and 0 <= ny < ROWS)
        growing = (nx, ny) == self.food
        # 不增长时尾巴会让位，所以不算撞到自己
        body = set(self.snake) if growing else set(list(self.snake)[:-1])
        hit_self = (nx, ny) in body

        if hit_wall or hit_self:
            self._game_over()
            return

        self.snake.appendleft((nx, ny))
        if growing:
            self.score += 1
            self.best = max(self.best, self.score)
            self.score_var.set(f"得分 {self.score}")
            self.best_var.set(f"最高 {self.best}")
            self.delay = max(MIN_DELAY, START_DELAY - self.score * SPEED_UP)
            self._spawn_food()
        else:
            self.snake.pop()

        self._render()

    def _game_over(self) -> None:
        self.alive = False
        self._stop_timer()
        self._render()

    # -------------------------------------------------------------- 输入
    def _on_key(self, event: tk.Event) -> str:
        key = (event.keysym or "").lower()

        if key in ("left", "a"):
            self._queue_dir(LEFT)
        elif key in ("right", "d"):
            self._queue_dir(RIGHT)
        elif key in ("up", "w"):
            self._queue_dir(UP)
        elif key in ("down", "s"):
            self._queue_dir(DOWN)
        elif key == "space":
            self._toggle_pause()
        elif key in ("r", "return", "kp_enter"):
            self.reset()
        elif key == "escape":
            self.root.destroy()
        return "break"

    def _queue_dir(self, d: tuple[int, int]) -> None:
        if not self.alive or self.paused:
            return
        last = self.pending[-1] if self.pending else self.direction
        # 忽略连续重复与 180° 反向；最多缓存 2 步，转身更跟手
        if d == last or d == (-last[0], -last[1]):
            return
        if len(self.pending) < 2:
            self.pending.append(d)

    def _toggle_pause(self) -> None:
        if not self.alive:          # 游戏结束后按空格 = 重开
            self.reset()
            return
        self.paused = not self.paused
        if self.paused:
            self._stop_timer()
        else:
            self._schedule()
        self._render()

    # -------------------------------------------------------------- 绘制
    def _render(self) -> None:
        c = self.canvas
        c.delete("all")

        # 网格
        for i in range(1, COLS):
            c.create_line(i * CELL, 0, i * CELL, H, fill=GRID_LINE)
        for j in range(1, ROWS):
            c.create_line(0, j * CELL, W, j * CELL, fill=GRID_LINE)
        c.create_rectangle(
            1, 1, W - 1, H - 1, outline="#2a3050", width=2,
        )

        # 食物：果冻豆 + 高光
        if self.food is not None:
            fx, fy = self.food
            x1, y1 = fx * CELL, fy * CELL
            c.create_oval(
                x1 + 4, y1 + 4, x1 + CELL - 4, y1 + CELL - 4,
                fill=FOOD_COLOR, outline="#a81f37", width=2,
            )
            c.create_oval(
                x1 + 8, y1 + 7, x1 + 13, y1 + 12,
                fill="#ffd9de", outline="",
            )

        # 蛇身（尾 → 头，头后画压在上面）
        segs = list(self.snake)
        for idx in range(len(segs) - 1, -1, -1):
            x, y = segs[idx]
            x1, y1 = x * CELL, y * CELL
            head = idx == 0
            pad = 1 if head else 2
            c.create_rectangle(
                x1 + pad, y1 + pad, x1 + CELL - pad, y1 + CELL - pad,
                fill=SNAKE_HEAD if head else SNAKE_BODY,
                outline=SNAKE_EDGE, width=1,
            )

        # 蛇头眼睛（朝行进方向）
        hx, hy = segs[0]
        cx, cy = hx * CELL + CELL / 2, hy * CELL + CELL / 2
        dx, dy = self.direction
        # 垂直于行进方向的偏移
        px, py = -dy, dx
        for sign in (-1, 1):
            ex = cx + dx * 5 + px * 4 * sign
            ey = cy + dy * 5 + py * 4 * sign
            c.create_oval(ex - 2, ey - 2, ex + 2, ey + 2, fill="#0b1220", outline="")

        # 覆盖层
        if self.paused:
            self._overlay("已暂停", "按 空格 继续")
        elif not self.alive:
            self._overlay("游戏结束", f"得分 {self.score}　按 R 或 空格 重开")

    def _overlay(self, title: str, sub: str) -> None:
        c = self.canvas
        c.create_rectangle(
            0, 0, W, H, fill="#000000", outline="", stipple="gray50",
        )
        c.create_text(
            W / 2, H / 2 - 18, text=title, fill=TEXT,
            font=("Microsoft YaHei", 28, "bold"),
        )
        c.create_text(
            W / 2, H / 2 + 24, text=sub, fill=DIM,
            font=("Microsoft YaHei", 12),
        )


def main() -> None:
    root = tk.Tk()
    try:
        # 让界面在高分屏上清晰一些（Windows）
        from ctypes import windll  # type: ignore

        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    SnakeGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
