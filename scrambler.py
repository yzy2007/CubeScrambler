import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import random
import datetime

# -------------------------------
# 业务逻辑：打乱生成
# -------------------------------

FACES = ["R", "L", "U", "D", "F", "B"]
MODIFIERS = ["", "'", "2"]
# 轴分组（用于“避免同轴连续”选项）
AXIS_MAP = {
    "R": "X", "L": "X",
    "U": "Y", "D": "Y",
    "F": "Z", "B": "Z"
}


def generate_single_scramble(length=20, avoid_same_face=True, avoid_same_axis=False, rng=None):
    """
    生成一条打乱公式。
    规则：
      - 避免同面：相邻两步不能是同一个面（R 后不接 R/R'/R2）
      - 避免同轴：相邻两步不能在同一轴（R/L 后不接 R/L）
    """
    rng = rng or random
    scramble = []
    last_face = None
    last_axis = None

    for _ in range(length):
        while True:
            face = rng.choice(FACES)
            axis = AXIS_MAP[face]
            if avoid_same_face and face == last_face:
                continue
            if avoid_same_axis and last_axis is not None and axis == last_axis:
                continue
            mod = rng.choice(MODIFIERS)
            move = face + mod
            scramble.append(move)
            last_face = face
            last_axis = axis
            break

    return " ".join(scramble)


def generate_scrambles(count=1, length=20, avoid_same_face=True, avoid_same_axis=False, seed=None):
    """
    批量生成打乱。可选 seed 以便复现。
    """
    rng = random.Random(seed) if seed is not None else random
    return [
        generate_single_scramble(length, avoid_same_face, avoid_same_axis, rng=rng)
        for _ in range(count)
    ]


# -------------------------------
# UI：Tkinter 应用
# -------------------------------

class ScramblerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("魔方打乱公式生成器（WCA风格）")
        self.geometry("760x520")
        self.minsize(720, 480)

        # 主题
        try:
            self.style = ttk.Style()
            if "clam" in self.style.theme_names():
                self.style.theme_use("clam")
        except Exception:
            pass

        self._build_widgets()

    def _build_widgets(self):
        # ---------- 参数区 ----------
        frame_top = ttk.LabelFrame(self, text="参数设置", padding=10)
        frame_top.pack(side=tk.TOP, fill=tk.X, padx=12, pady=8)

        # 打乱长度
        ttk.Label(frame_top, text="打乱长度：").grid(row=0, column=0, sticky="w")
        self.length_var = tk.StringVar(value="20")
        self.length_entry = ttk.Entry(frame_top, textvariable=self.length_var, width=8)
        self.length_entry.grid(row=0, column=1, padx=(0, 12))

        # 数量
        ttk.Label(frame_top, text="生成数量：").grid(row=0, column=2, sticky="w")
        self.count_var = tk.StringVar(value="10")
        self.count_entry = ttk.Entry(frame_top, textvariable=self.count_var, width=8)
        self.count_entry.grid(row=0, column=3, padx=(0, 12))

        # 随机种子（可选）
        ttk.Label(frame_top, text="随机种子（可选）：").grid(row=0, column=4, sticky="w")
        self.seed_var = tk.StringVar(value="")
        self.seed_entry = ttk.Entry(frame_top, textvariable=self.seed_var, width=12)
        self.seed_entry.grid(row=0, column=5, padx=(0, 12))

        # 规则选项
        self.avoid_same_face_var = tk.BooleanVar(value=True)
        self.avoid_same_axis_var = tk.BooleanVar(value=False)
        chk1 = ttk.Checkbutton(frame_top, text="避免连续同面", variable=self.avoid_same_face_var)
        chk2 = ttk.Checkbutton(frame_top, text="避免连续同轴（更“均匀”）", variable=self.avoid_same_axis_var)
        chk1.grid(row=1, column=0, columnspan=3, sticky="w", pady=(6, 0))
        chk2.grid(row=1, column=3, columnspan=3, sticky="w", pady=(6, 0))

        # 操作按钮
        btn_frame = ttk.Frame(frame_top)
        btn_frame.grid(row=0, column=6, rowspan=2, padx=4, sticky="ns")

        gen_btn = ttk.Button(btn_frame, text="生成", command=self.on_generate)
        copy_btn = ttk.Button(btn_frame, text="复制所选", command=self.on_copy_selected)
        save_btn = ttk.Button(btn_frame, text="保存TXT", command=self.on_save)
        clear_btn = ttk.Button(btn_frame, text="清空", command=self.on_clear)

        gen_btn.pack(fill=tk.X, pady=2)
        copy_btn.pack(fill=tk.X, pady=2)
        save_btn.pack(fill=tk.X, pady=2)
        clear_btn.pack(fill=tk.X, pady=2)

        # ---------- 结果区 ----------
        frame_mid = ttk.LabelFrame(self, text="生成结果", padding=6)
        frame_mid.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=12, pady=(0, 8))

        self.listbox = tk.Listbox(frame_mid, selectmode=tk.EXTENDED)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(frame_mid, orient=tk.VERTICAL, command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)

        # ---------- 状态栏 ----------
        self.status_var = tk.StringVar(value="就绪")
        status = ttk.Label(self, textvariable=self.status_var, anchor="w")
        status.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=(0, 8))

        # 快捷键
        self.bind("<Control-g>", lambda e: self.on_generate())
        self.bind("<Control-c>", lambda e: self.on_copy_selected())
        self.bind("<Delete>", lambda e: self.on_clear())

        # 提示
        self.after(300, lambda: self._set_status("提示：Ctrl+G 生成，Ctrl+C 复制，Delete 清空"))

    # ---------- 事件处理 ----------
    def _parse_int(self, s, name, min_v, max_v):
        try:
            v = int(s)
        except ValueError:
            raise ValueError(f"{name} 需为整数")
        if not (min_v <= v <= max_v):
            raise ValueError(f"{name} 需在 [{min_v}, {max_v}] 区间")
        return v

    def on_generate(self):
        try:
            length = self._parse_int(self.length_var.get().strip(), "打乱长度", 8, 200)
            count = self._parse_int(self.count_var.get().strip(), "生成数量", 1, 1000)
            seed_text = self.seed_var.get().strip()
            seed = int(seed_text) if seed_text else None

            scrambles = generate_scrambles(
                count=count,
                length=length,
                avoid_same_face=self.avoid_same_face_var.get(),
                avoid_same_axis=self.avoid_same_axis_var.get(),
                seed=seed
            )
            for s in scrambles:
                self.listbox.insert(tk.END, s)

            self._set_status(f"已生成 {count} 条（长度 {length}）。当前总数：{self.listbox.size()}。")

        except Exception as e:
            messagebox.showerror("参数错误", str(e))
            self._set_status("参数错误，请检查。")

    def on_copy_selected(self):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showinfo("提示", "请先在列表中选择要复制的条目（可多选）。")
            return
        lines = [self.listbox.get(i) for i in selection]
        text = "\n".join(lines)
        self.clipboard_clear()
        self.clipboard_append(text)
        self._set_status(f"已复制 {len(lines)} 条到剪贴板。")

    def on_save(self):
        if self.listbox.size() == 0:
            messagebox.showinfo("提示", "列表为空，无可保存内容。")
            return
        init_name = f"scrambles_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
            initialfile=init_name,
            title="保存打乱结果"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                for i in range(self.listbox.size()):
                    f.write(self.listbox.get(i) + "\n")
            self._set_status(f"已保存到：{path}")
        except Exception as e:
            messagebox.showerror("保存失败", str(e))
            self._set_status("保存失败。")

    def on_clear(self):
        self.listbox.delete(0, tk.END)
        self._set_status("已清空列表。")

    def _set_status(self, msg):
        self.status_var.set(msg)


if __name__ == "__main__":
    app = ScramblerApp()
    app.mainloop()
