# Trae 配置指南

## 一、项目导入

### 1. 打开 Trae

1. 启动 Trae 编辑器
2. 点击 "Open Folder" 或 "打开文件夹"
3. 选择 `douyin_downloader_windows` 目录

### 2. 项目结构

导入后 Trae 左侧文件树应显示：

```
douyin_downloader_windows/
├── app.py
├── templates/
│   └── index.html
├── docs/
├── 启动下载器.vbs
├── 启动下载器.bat
├── build.bat
└── README.md
```

---

## 二、运行配置

### 1. 创建运行配置

1. 按 `Ctrl+Shift+P` 打开命令面板
2. 输入 "Python: Create Terminal"
3. 确保终端使用正确的 Python 解释器

### 2. 运行程序

在终端中执行：

```bash
python app.py
```

或使用启动脚本：

```bash
启动下载器.bat
```

---

## 三、调试配置

### 1. 创建 launch.json

1. 点击左侧调试图标（或按 `Ctrl+Shift+D`）
2. 点击 "create a launch.json file"
3. 选择 "Python" → "Flask"

### 2. 修改配置

生成的 `.vscode/launch.json`：

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Flask",
      "type": "python",
      "request": "launch",
      "module": "flask",
      "env": {
        "FLASK_APP": "app.py",
        "FLASK_DEBUG": "1"
      },
      "args": [
        "run",
        "--no-debugger",
        "--no-reload"
      ],
      "jinja": true,
      "justMyCode": true
    }
  ]
}
```

### 3. 开始调试

1. 在代码左侧点击设置断点
2. 按 `F5` 启动调试
3. 使用 `F10`（单步跳过）、`F11`（单步进入）进行调试

---

## 四、常用操作

### 代码跳转

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+Click` | 跳转到定义 |
| `Alt+←` | 返回上一位置 |
| `Ctrl+Shift+O` | 跳转到符号 |
| `Ctrl+T` | 搜索工作区符号 |

### 查找替换

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+F` | 当前文件查找 |
| `Ctrl+H` | 当前文件替换 |
| `Ctrl+Shift+F` | 全局查找 |
| `Ctrl+Shift+H` | 全局替换 |

### 代码编辑

| 快捷键 | 功能 |
|--------|------|
| `Alt+↑/↓` | 移动当前行 |
| `Shift+Alt+↑/↓` | 复制当前行 |
| `Ctrl+/` | 注释/取消注释 |
| `Ctrl+Shift+K` | 删除当前行 |

---

## 五、AI 助手使用

### 1. 打开 AI 助手

- 快捷键：`Ctrl+L`
- 或点击右侧 AI 图标

### 2. 常用指令

#### 解释代码

选中代码后输入：

```
解释这段代码
```

#### 修复问题

```
修复这个错误：[粘贴错误信息]
```

#### 添加功能

```
在 app.py 中添加一个导出下载历史为 CSV 的功能
```

#### 优化代码

```
优化 download_file 函数的性能
```

---

## 六、问题排查

### 1. Python 解释器未找到

**现象**: 终端提示 "python" 不是内部或外部命令

**解决**:
1. 按 `Ctrl+Shift+P`
2. 输入 "Python: Select Interpreter"
3. 选择正确的 Python 版本

### 2. Flask 模块找不到

**解决**:
```bash
python -m pip install flask
```

或在 Trae 终端中：
```bash
pip install flask
```

### 3. 端口被占用

**解决**:
修改 `app.py` 中的端口：

```python
app.run(host="0.0.0.0", port=5002)  # 改为其他端口
```

---

## 七、打包操作

### 使用 Trae 终端打包

1. 打开终端（`Ctrl+``）
2. 执行：

```bash
build.bat
```

或手动：

```bash
python -m pip install pyinstaller
python -m PyInstaller --name="抖音视频下载器" --onefile --windowed --add-data "templates;templates" app.py
```

### 查看打包输出

打包完成后，在 Trae 左侧文件树中查看 `dist/` 目录。

---

## 八、Git 集成（可选）

### 初始化仓库

```bash
git init
git add .
git commit -m "Initial commit"
```

### 常用操作

| 操作 | 命令/快捷键 |
|------|------------|
| 查看更改 | `Ctrl+Shift+G` |
| 暂存文件 | 点击文件旁的 `+` |
| 提交 | 输入消息按 `Ctrl+Enter` |
| 推送 | 点击 "..." → Push |

---

## 九、扩展推荐

在扩展商店搜索安装：

1. **Python** - Python 语言支持（通常已内置）
2. **Markdown All in One** - Markdown 编辑增强
3. **GitLens** - Git 增强（可选）

---

## 十、快速修复清单

遇到问题时的排查步骤：

1. **程序无法启动**
   - [ ] Python 是否安装
   - [ ] Flask 是否安装
   - [ ] 端口是否被占用

2. **获取视频失败**
   - [ ] 网络连接是否正常
   - [ ] Cookie 是否设置（如需登录）
   - [ ] 查看终端错误日志

3. **下载失败**
   - [ ] 下载目录是否有写入权限
   - [ ] 磁盘空间是否充足
   - [ ] 视频 URL 是否有效

4. **打包失败**
   - [ ] PyInstaller 是否安装
   - [ ] 模板文件路径是否正确
   - [ ] 使用 `--console` 查看详细错误
