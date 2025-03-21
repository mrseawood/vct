# 视频截图工具

一个简单易用的视频截图工具，可以批量处理视频文件并提取指定数量的截图。

## 功能特点

- 支持批量处理多个视频文件
- 递归搜索文件夹中的所有视频文件
- 自动调整截图数量，避免对短视频过度采样
- 均匀分布的截图时间点
- 直观的图形用户界面
- 实时进度显示
- 支持自定义输出目录
- 智能错误处理和超时控制

## 系统要求

- Python 3.6 或更高版本
- FFmpeg（必须安装并添加到系统环境变量）
- Windows/Linux/MacOS

## 安装说明

1. 确保已安装 Python 3.6 或更高版本
2. 安装 FFmpeg：
   - Windows: 下载 FFmpeg 并添加到系统环境变量
   - Linux: `sudo apt-get install ffmpeg`
   - MacOS: `brew install ffmpeg`
3. 安装依赖包：
   ```bash
   pip install -r requirements.txt
   ```

## 使用方法

1. 运行程序：
   ```bash
   python 为每个视频截取指定数量截图并存储在指定文件夹内.py
   ```
2. 在程序界面中：
   - 点击"浏览..."选择包含视频文件的文件夹
   - 程序会自动设置输出文件夹，也可以手动选择其他位置
   - 设置每个视频需要截取的图片数量（默认为8张）
   - 点击"开始处理"按钮开始处理

## 支持的视频格式

- MP4 (.mp4)
- AVI (.avi)
- MKV (.mkv)
- MOV (.mov)
- WMV (.wmv)
- FLV (.flv)
- WebM (.webm)
- M4V (.m4v)
- MPG/MPEG (.mpg, .mpeg)
- 3GP (.3gp)

## 注意事项

- 确保有足够的磁盘空间存储截图
- 对于较短的视频，程序会自动调整截图数量
- 处理大量视频可能需要较长时间
- 如果视频文件损坏或格式不支持，程序会跳过该文件并继续处理其他文件

## 错误处理

- 程序会自动跳过无法处理的视频文件
- 对于提取超时的帧会自动跳过并继续处理
- 所有错误都会在状态栏显示相关信息

## 开发者信息

© 2025 一模型Ai (https://jmlovestore.com)

## 许可证


MIT License

![123](https://github.com/user-attachments/assets/814e1ae5-61f2-4e35-99f8-1e27fb377864)
