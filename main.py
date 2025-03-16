import subprocess
import os
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import threading
import time

def is_video_file(file_path):
    """检查文件是否是视频文件"""
    # 首先通过文件扩展名进行快速检查
    video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg', '.3gp']
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if file_ext not in video_extensions:
        return False
    
    # 然后再使用 ffprobe 进行确认
    try:
        ffprobe_cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=format_name', '-of', 'default=noprint_wrappers=1:nokey=1', file_path]
        output = subprocess.check_output(ffprobe_cmd).decode().strip()
        return bool(output)
    except subprocess.CalledProcessError:
        return False

def extract_frames(video_path, output_dir, num_frames, progress_callback=None):
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 使用 FFmpeg 获取视频时长
    ffprobe_cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', video_path]
    duration = float(subprocess.check_output(ffprobe_cmd).decode().strip())
    
    # 获取视频帧率
    ffprobe_fps_cmd = ['ffprobe', '-v', 'error', '-select_streams', 'v', '-show_entries', 'stream=r_frame_rate', '-of', 'default=noprint_wrappers=1:nokey=1', video_path]
    fps_str = subprocess.check_output(ffprobe_fps_cmd).decode().strip()
    
    # 解析帧率（格式可能是 "24/1"）
    if '/' in fps_str:
        num, den = map(int, fps_str.split('/'))
        fps = num / den if den != 0 else 0
    else:
        fps = float(fps_str) if fps_str else 0
    
    # 估算总帧数
    total_frames = int(duration * fps) if fps > 0 else 0
    
    # 调整截图数量，确保不超过视频总帧数的80%
    if total_frames > 0 and num_frames > total_frames * 0.8:
        adjusted_num_frames = max(1, int(total_frames * 0.8))
        if progress_callback:
            progress_callback(0)  # 重置进度条
        return adjusted_num_frames, False  # 返回调整后的帧数和标志表示需要调整
    
    # 计算时间间隔（确保不会太小）
    min_interval = 0.1  # 最小间隔为0.1秒
    if duration <= num_frames * min_interval:
        # 视频太短，调整间隔
        interval = max(min_interval, duration / (num_frames + 1))
    else:
        interval = duration / (num_frames + 1)
    
    # 提取帧
    try:
        for i in range(1, num_frames + 1):
            time_pos = i * interval
            minutes = int(time_pos // 60)
            seconds = int(time_pos % 60)
            milliseconds = int((time_pos % 1) * 1000)
            output_file = os.path.join(output_dir, f'{os.path.splitext(os.path.basename(video_path))[0]}_time_{minutes:02d}m{seconds:02d}s{milliseconds:03d}.jpg')
            
            # 添加超时控制
            ffmpeg_cmd = ['ffmpeg', '-ss', str(time_pos), '-i', video_path, '-vframes', '1', '-q:v', '2', output_file]
            try:
                # 设置超时时间为10秒
                subprocess.run(ffmpeg_cmd, timeout=10)
            except subprocess.TimeoutExpired:
                print(f"提取帧 {i} 超时，跳过")
                continue
            
            # 更新进度
            if progress_callback:
                progress_callback(i / num_frames * 100)
    except Exception as e:
        print(f"提取帧时出错: {str(e)}")
        raise
    
    return num_frames, True  # 返回实际使用的帧数和成功标志

class VideoFrameExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("视频截图工具")
        self.root.geometry("700x650")  # 减小窗口高度以减少底部空白区域
        self.root.resizable(True, True)
        
        self.input_dir = ""
        self.output_dir = ""
        self.num_frames = tk.IntVar(value=8)
        self.processing = False
        
        self.create_widgets()
    
    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 添加使用说明区域
        help_frame = ttk.LabelFrame(main_frame, text="使用说明", padding="5")
        help_frame.pack(fill=tk.X, pady=5)
        
        help_text = """使用步骤：
1. 点击"浏览..."按钮选择包含视频文件的文件夹
2. 程序会自动设置输出文件夹，您也可以点击"浏览..."按钮自定义输出位置
3. 设置每个视频需要截取的图片数量（默认为8张）
4. 点击"开始处理"按钮开始批量处理视频

注意事项：
· 程序会递归搜索所选文件夹中的所有视频文件
· 截图会均匀分布在视频时长内
· 对于较短的视频，程序会自动调整截图数量
· 处理过程中可以通过进度条查看当前进度
· 需要安装FFmpeg才能正常使用本工具"""
        
        help_label = ttk.Label(help_frame, text=help_text, justify=tk.LEFT, wraplength=650)
        help_label.pack(fill=tk.X, padx=5, pady=5)
        
        # 输入文件夹选择
        input_frame = ttk.LabelFrame(main_frame, text="输入设置", padding="5")
        input_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(input_frame, text="导入文件夹:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.input_dir_entry = ttk.Entry(input_frame, width=50)
        self.input_dir_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        ttk.Button(input_frame, text="浏览...", command=self.select_input_dir).grid(row=0, column=2, padx=5, pady=5)
        
        # 输出文件夹选择
        output_frame = ttk.LabelFrame(main_frame, text="输出设置", padding="5")
        output_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(output_frame, text="导出文件夹:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.output_dir_entry = ttk.Entry(output_frame, width=50)
        self.output_dir_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        ttk.Button(output_frame, text="浏览...", command=self.select_output_dir).grid(row=0, column=2, padx=5, pady=5)
        
        # 截图数量设置
        settings_frame = ttk.LabelFrame(main_frame, text="截图设置", padding="5")
        settings_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(settings_frame, text="截取数量:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Spinbox(settings_frame, from_=1, to=1000, textvariable=self.num_frames, width=10).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 进度条
        progress_frame = ttk.LabelFrame(main_frame, text="处理进度", padding="5")
        progress_frame.pack(fill=tk.X, pady=5)
        
        self.progress = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress.pack(fill=tk.X, padx=5, pady=5)
        
        self.status_label = ttk.Label(progress_frame, text="就绪")
        self.status_label.pack(anchor=tk.W, padx=5, pady=5)
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.start_button = ttk.Button(button_frame, text="开始处理", command=self.start_processing)
        self.start_button.pack(side=tk.RIGHT, padx=5)
        
        # 添加版权信息
        copyright_label = ttk.Label(main_frame, text="© 2025 一模型Ai (https://jmlovestore.com) - 不会开发软件吗 🙂 Ai会哦", font=("Arial", 9))
        copyright_label.pack(side=tk.BOTTOM, pady=5)
    
    def select_input_dir(self):
        directory = filedialog.askdirectory(title="选择导入文件夹")
        if directory:
            self.input_dir = directory
            self.input_dir_entry.delete(0, tk.END)
            self.input_dir_entry.insert(0, directory)
            
            # 自动设置输出文件夹为输入文件夹的父目录下的同名_output文件夹
            parent_dir = os.path.dirname(directory)
            folder_name = os.path.basename(directory)
            suggested_output = os.path.join(parent_dir, f"{folder_name}_output")
            
            self.output_dir = suggested_output
            self.output_dir_entry.delete(0, tk.END)
            self.output_dir_entry.insert(0, suggested_output)
    
    def select_output_dir(self):
        directory = filedialog.askdirectory(title="选择导出文件夹")
        if directory:
            self.output_dir = directory
            self.output_dir_entry.delete(0, tk.END)
            self.output_dir_entry.insert(0, directory)
    
    def update_progress(self, value):
        self.progress['value'] = value
        self.root.update_idletasks()
    
    def update_status(self, text):
        self.status_label.config(text=text)
        self.root.update_idletasks()
    
    def start_processing(self):
        if self.processing:
            return
        
        # 检查输入和输出文件夹
        if not self.input_dir or not os.path.isdir(self.input_dir):
            messagebox.showerror("错误", "请选择有效的导入文件夹")
            return
        
        if not self.output_dir:
            messagebox.showerror("错误", "请选择有效的导出文件夹")
            return
        
        # 创建输出文件夹
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 获取帧数
        num_frames = self.num_frames.get()
        if num_frames <= 0:
            messagebox.showerror("错误", "截取数量必须大于0")
            return
        
        # 禁用开始按钮
        self.processing = True
        self.start_button.config(state=tk.DISABLED)
        
        # 在新线程中处理视频
        threading.Thread(target=self.process_videos, args=(self.input_dir, self.output_dir, num_frames), daemon=True).start()
    
    def find_all_videos(self, input_dir, base_input_dir, base_output_dir, current_depth=0, max_depth=10):
        """递归查找所有视频文件"""
        video_files = []        
        # 更新状态显示当前正在搜索的目录
        self.update_status(f"正在搜索目录: {input_dir} (深度: {current_depth}/{max_depth})")
        
        # 检查是否达到最大搜索深度
        if current_depth > max_depth:
            self.update_status(f"已达到最大搜索深度 {max_depth}，跳过目录: {input_dir}")
            return video_files
        
        # 获取当前目录下的所有文件和文件夹
        try:
            items = os.listdir(input_dir)
        except Exception as e:
            self.update_status(f"无法访问目录 {input_dir}: {str(e)}")
            return video_files
            
        # 处理当前目录中的文件
        for item in items:
            item_path = os.path.join(input_dir, item)
            
            # 如果是文件，检查是否为视频
            if os.path.isfile(item_path):
                try:
                    if is_video_file(item_path):
                        # 计算相对路径，用于在输出目录中创建相同的结构
                        rel_path = os.path.relpath(input_dir, base_input_dir)
                        output_subdir = os.path.join(base_output_dir, rel_path)
                        video_files.append((item_path, output_subdir))
                        self.update_status(f"找到视频文件: {os.path.basename(item_path)}")
                except Exception as e:
                    self.update_status(f"检查文件 {item_path} 时出错: {str(e)}")
                    continue
            
            # 如果是目录，递归处理
            elif os.path.isdir(item_path):
                try:
                    # 检查是否为符号链接
                    if not os.path.islink(item_path):
                        video_files.extend(self.find_all_videos(item_path, base_input_dir, base_output_dir, current_depth + 1, max_depth))
                except Exception as e:
                    self.update_status(f"处理目录 {item_path} 时出错: {str(e)}")
                    continue
                
        return video_files
    
    def process_videos(self, input_dir, output_dir, num_frames):
        try:
            self.update_status("正在递归搜索视频文件...")
            
            # 递归查找所有视频文件，并获取对应的输出目录
            video_files = self.find_all_videos(input_dir, input_dir, output_dir, 0, 10)
            
            if not video_files:
                self.update_status("未找到视频文件")
                messagebox.showinfo("信息", "在选定的文件夹及其子文件夹中未找到视频文件")
                self.processing = False
                self.start_button.config(state=tk.NORMAL)
                return
            
            # 处理每个视频文件
            total_videos = len(video_files)
            for i, (video_path, output_subdir) in enumerate(video_files):
                video_name = os.path.basename(video_path)
                self.update_status(f"正在处理 {i+1}/{total_videos}: {video_name}")
                
                # 为每个视频创建一个子文件夹
                video_output_dir = os.path.join(output_subdir, os.path.splitext(os.path.basename(video_path))[0])
                
                # 重置进度条
                self.update_progress(0)
                
                # 提取帧
                actual_frames, success = extract_frames(video_path, video_output_dir, num_frames, self.update_progress)
                
                # 如果帧数被调整，显示提示信息
                if not success:
                    self.update_status(f"视频 {video_name} 太短，已自动调整截图数量为 {actual_frames} 张")
                    # 使用调整后的帧数继续处理
                    extract_frames(video_path, video_output_dir, actual_frames, self.update_progress)
            
            self.update_status("处理完成")
            messagebox.showinfo("完成", f"已成功处理 {total_videos} 个视频文件")
            
        except Exception as e:
            self.update_status(f"处理出错: {str(e)}")
            messagebox.showerror("错误", f"处理视频时出错:\n{str(e)}")
        
        finally:
            # 恢复开始按钮
            self.processing = False
            self.start_button.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoFrameExtractorApp(root)
    root.mainloop()
