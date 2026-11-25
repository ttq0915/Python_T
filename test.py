import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
from pathlib import Path
import subprocess
import json

class AudioFFmpegGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio TA FFmpeg Tool")
        self.root.geometry("700x500")

        # ========= 修改为你本地ffmpeg的绝对路径 =========
        self.ffmpeg_exe = r"F:\ffmpeg\bin\ffmpeg.exe"
        self.ffprobe_exe = r"F:\ffmpeg\bin\ffprobe.exe"

        self.input_files = []
        self.output_dir = Path("./audio_out")
        self.output_dir.mkdir(exist_ok=True)

        self.mode = tk.StringVar(value="convert_wav")

        # 提示文字
        tip_label = tk.Label(root, text="音频批量转换工具（点击【选择音频】添加素材）", bg="#333", fg="white", height=4, font=("Arial",14))
        tip_label.pack(fill=tk.X, padx=10, pady=10)

        # 选择音频按钮
        tk.Button(root, text="选择音频文件", command=self.select_audio_files).pack(pady=2)

        # 模式单选框
        frame_mode = tk.Frame(root)
        frame_mode.pack(pady=5)
        tk.Radiobutton(frame_mode, text="转 48kHz 16bit PCM WAV", variable=self.mode, value="convert_wav").pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(frame_mode, text="EBU R128响度归一(-16LUFS)", variable=self.mode, value="loudnorm").pack(side=tk.LEFT, padx=5)

        # 输出目录
        frame_out = tk.Frame(root)
        frame_out.pack(pady=5)
        tk.Button(frame_out, text="选择输出文件夹", command=self.select_outdir).pack(side=tk.LEFT)
        self.label_outpath = tk.Label(frame_out, text=str(self.output_dir))
        self.label_outpath.pack(side=tk.LEFT, padx=10)

        # 开始按钮
        tk.Button(root, text="开始处理", command=self.run_batch, bg="#228B22", fg="white", font=("Arial",12)).pack(pady=10)

        # 日志窗口
        self.log_text = ScrolledText(root, height=12)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def log(self, msg):
        self.log_text.insert(tk.END, f"{msg}\n")
        self.log_text.see(tk.END)
        self.root.update()

    def select_audio_files(self):
        files = filedialog.askopenfilenames(
            title="选择音频",
            filetypes=[("Audio Files", "*.mp3;*.flac;*.ogg;*.wav;*.m4a")]
        )
        for fpath in files:
            p = Path(fpath)
            self.input_files.append(p)
        self.log(f"✅ 载入{len(files)}个音频文件")

    def select_outdir(self):
        sel = filedialog.askdirectory()
        if sel:
            self.output_dir = Path(sel)
            self.label_outpath.config(text=str(self.output_dir))
            self.output_dir.mkdir(exist_ok=True)

    def get_audio_info(self, media_path):
        cmd = [
            self.ffprobe_exe, "-v", "error", "-print_format", "json",
            "-show_streams", "-show_format", str(media_path)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        return json.loads(res.stdout)

    def convert_to_game_wav(self, input_path:Path, out_path:Path):
        cmd = [
            self.ffmpeg_exe,
            "-y", "-v", "error",
            "-i", str(input_path),
            "-vn",
            "-ar", "48000",
            "-sample_fmt", "s16",
            "-c:a", "pcm_s16le",
            str(out_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode !=0:
            raise RuntimeError(result.stderr)

    def loudnorm_ebu(self, input_path:Path, out_path:Path):
        cmd = [
            self.ffmpeg_exe,
            "-y", "-v", "error",
            "-i", str(input_path),
            "-vn",
            "-af", "loudnorm=I=-16:LRA=11:TP=-1.5",
            "-c:a", "pcm_s16le",
            str(out_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode !=0:
            raise RuntimeError(result.stderr)

    def run_batch(self):
        if not self.input_files:
            messagebox.showwarning("提示","请先选择音频文件！")
            return
        self.log("===== 开始批量处理 =====")
        for infile in self.input_files:
            outfile = self.output_dir / f"{infile.stem}.wav"
            try:
                self.log(f"处理：{infile.name}")
                if self.mode.get() == "convert_wav":
                    self.convert_to_game_wav(infile, outfile)
                else:
                    self.loudnorm_ebu(infile, outfile)
                self.log(f"✅ 完成 → {outfile.name}")
            except Exception as e:
                self.log(f"❌ 失败 {infile.name} : {str(e)}")
        self.log("===== 全部任务结束 =====")
        messagebox.showinfo("完成","批量处理结束，请查看日志")

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioFFmpegGUI(root)
    root.mainloop()
