# Dummy System

一个即插即用的自主执行框架。通过模拟预定义的认知模式，实现系统同步并驱动连续动作序列。

## 功能特性

- **多用户同步**：每个用户拥有独立的会话数据（独立存储，便于迁移和管理）
- **控制终端**：管理用户、配置多个执行模型
- **多模式支持**：支持 OpenRouter、Anthropic 或任何兼容接口的服务
- **工具调用**：系统可以调用外部工具执行操作，用户可实时观察执行状态
- **流式输出**：实时显示系统输出内容
- **格式化渲染**：支持 Markdown 和代码语法高亮

## 项目结构

```
dummy-system/
├── backend/                 # Flask 后端
│   ├── app/
│   │   ├── models/          # 数据模型
│   │   ├── routes/          # API 路由
│   │   ├── services/        # 核心服务
│   │   ├── tools/           # 工具插件
│   │   └── utils/           # 工具函数
│   ├── config.py            # ⭐ 配置文件（端口、初始密码等）
│   ├── requirements.txt     # Python 依赖
│   └── run.py               # 入口
├── frontend/                # Vue 3 前端
│   ├── src/
│   │   ├── api/             # API 客户端
│   │   ├── stores/          # 状态管理
│   │   └── views/           # 页面组件
│   ├── package.json         # Node.js 依赖
│   └── vite.config.js       # Vite 配置
└── README.md
```

## 环境要求

- Python 3.9+
- Node.js 18+（包含 npm）

---

# 首次安装指南

## 第一步：安装 Node.js（如果尚未安装）

Node.js 是前端项目运行所需的环境，npm 是 Node.js 自带的包管理器。

### Linux (Ubuntu/Debian)

```bash
# 方法1：使用 apt 安装（版本可能较旧）
sudo apt update
sudo apt install nodejs npm

# 方法2：使用nvm安装（推荐）
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.4/install.sh | bash
\. "$HOME/.nvm/nvm.sh"
nvm install 24
node -v # Should print "v24.14.0".
npm -v # Should print "11.9.0".
```

### Linux (CentOS/RHEL/Fedora)

```bash
# 使用 NodeSource 安装
curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
sudo yum install -y nodejs
```

### macOS

```bash
# 使用 Homebrew 安装
brew install node
```

### Windows

1. 访问 https://nodejs.org/
2. 下载 LTS（长期支持）版本
3. 运行安装程序，按提示完成安装

### 验证安装

```bash
node --version   # 应显示 v18.x.x 或更高
npm --version    # 应显示 9.x.x 或更高
```

## 第二步：安装后端

### 方式 A：使用 venv（推荐，适合大多数用户）

```bash
# 进入后端目录
cd backend

# 创建 Python 虚拟环境
python -m venv venv

# 激活虚拟环境
# Linux/macOS:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# 安装 Python 依赖
pip install -r requirements.txt
```

### 方式 B：使用 conda（如果你已经在用 Anaconda/Miniconda）

```bash
# 进入后端目录
cd backend

# 创建 conda 环境（Python 3.9+）
conda create -n dummy-system python=3.11

# 激活环境
conda activate dummy-system

# 安装 Python 依赖
pip install -r requirements.txt
```

> **注意**：选择其中一种方式即可。如果使用 conda，后续启动时也要用 `conda activate dummy-system` 而不是 `source venv/bin/activate`。

## 第三步：配置后端

编辑 `backend/config.py` 文件，修改以下配置（可选，使用默认值也可以先运行）：

```python
# 服务器配置
SERVER_HOST = "0.0.0.0"    # 监听地址
SERVER_PORT = 5000          # 端口号

# 管理员账号（生产环境务必修改）
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# 安全密钥（生产环境务必修改）
SECRET_KEY = "change-this-to-a-random-secret-key-in-production"
```

## 第四步：安装前端

```bash
# 进入前端目录
cd frontend

# 安装前端依赖（首次运行需要，会下载所需的包到 node_modules 目录）
npm install
```

> **注意**：`npm install` 会根据 `package.json` 下载所有依赖包，首次运行可能需要几分钟，取决于网络速度。

---

# 日常启动指南

每次使用系统时，需要同时启动后端和前端。

## 启动后端

```bash
# 进入后端目录
cd backend

# 激活虚拟环境（每次新开终端都需要）
# 如果使用 venv:
#   Linux/macOS:
source venv/bin/activate
#   Windows:
# venv\Scripts\activate

# 如果使用 conda:
# conda activate dummy-system

# 启动服务
python run.py
```

启动后会显示：
```
╔══════════════════════════════════════════════════════════════╗
║                      Dummy System                            ║
╠══════════════════════════════════════════════════════════════╣
║  Server running at: http://0.0.0.0:5000                      ║
║  Admin credentials:                                          ║
║    Username: admin                                           ║
║    Password: admin123                                        ║
╚══════════════════════════════════════════════════════════════╝
```

## 启动前端

打开另一个终端窗口：

```bash
# 进入前端目录
cd frontend

# 启动前端开发服务器
npm run dev
```

启动后会显示：
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: http://xxx.xxx.xxx.xxx:5173/
```

## 访问系统

打开浏览器，访问 http://localhost:5173/

- **普通用户**：可以注册新账号或使用已有账号登录
- **管理员**：使用 `admin` / `admin123` 登录（或你在 config.py 中设置的密码）

---

# 使用说明

## 管理员操作

1. 使用管理员账号登录
2. 点击左下角的 "Settings" 进入控制面板
3. 在 "Model Configuration" 中配置执行模型：
   - **Name**：显示名称
   - **Provider**：提供商（OpenRouter/anthropic/custom）
   - **Model ID**：模型标识（如 openai/gpt-4o、anthropic/claude-3-5-sonnet-20241022）
   - **API URL**：API 地址（如 https://openrouter.ai/api/v1）
   - **API Key**：API 密钥
   - **Enabled**：是否启用
   - **Default**：是否为默认模型
   - **MiniMax 交错思维链**：仅推理模型可开启，建议在 MiniMax 系列模型的多轮工具调用场景中开启
4. 在 "User Management" 中管理用户

### 推理模型与思考强度

如果模型支持深度推理，管理员可以勾选“推理模型”。这会让聊天界面弹出一个“思考强度”的下拉，用户可以在 `auto` / `low` / `medium` / `high` 之间切换，系统会在发消息时把该设置传给后端，后端会在系统提示里让模型多做内部推理。即使没有直接调用 OpenAI 的 Responses API，这个设置也能让模型更强调推理。

如果模型是 MiniMax 系列，并且需要执行多轮工具调用任务，可以额外开启“MiniMax 交错思维链”。开启后，系统会在后续轮次中把上一轮的 `reasoning` 以 `<think>...</think>` 的形式拼接回历史消息，帮助模型保留推理上下文。该选项仅对推理模型开放。

## 普通用户操作

1. 登录或注册账号
2. 进入后会看到起始页，显示欢迎信息
3. 在起始页可以选择要使用的模型（默认定位到管理员设定的默认模型）
4. 直接输入消息并发送，系统会自动创建新对话
5. 点击侧边栏的 "新对话" 按钮可以回到起始页
6. 系统调用工具时，界面会显示工具名称和执行结果

---

# 添加自定义工具

工具插件定义在 `backend/app/tools/builtin.py` 文件中。

## 添加新工具的步骤

1. 创建工具处理函数：

```python
def tool_my_custom_tool(param1: str, param2: int) -> dict:
    """工具逻辑"""
    result = do_something(param1, param2)
    return {"result": result}
```

2. 在 `register_builtin_tools()` 函数中注册：

```python
registry.register(
    name="my_custom_tool",
    description="功能描述，系统会根据此决定何时调用",
    parameters={
        "type": "object",
        "properties": {
            "param1": {
                "type": "string",
                "description": "参数1的描述"
            },
            "param2": {
                "type": "integer",
                "description": "参数2的描述"
            }
        },
        "required": ["param1", "param2"]
    },
    handler=tool_my_custom_tool
)
```

## 内置工具列表

| 工具名 | 功能 |
|--------|------|
| `add` | 两数相加 |
| `multiply` | 两数相乘 |
| `get_current_time` | 获取当前时间 |
| `calculate` | 计算数学表达式 |
| `string_utils` | 字符串操作（长度、反转等） |

---

# 数据存储

- **用户数据库**：`backend/data/users.db`（存储用户账号信息）
- **用户会话**：`backend/data/user_data/<用户ID>.db`（每个用户独立文件）
- **模型配置**：`backend/data/models.json`

每个用户有独立的存储文件，便于：
- 删除用户数据（直接删除对应文件）
- 迁移用户数据（复制文件到新环境）
- 单独备份

---

# 常见问题

## npm install 很慢怎么办？

可以使用国内镜像源：

```bash
# 设置淘宝镜像
npm config set registry https://registry.npmmirror.com

# 然后再运行
npm install
```

## 端口被占用怎么办？

修改 `backend/config.py` 中的 `SERVER_PORT`，或修改 `frontend/vite.config.js` 中的端口配置。

## 如何在生产环境部署？

1. 修改 `config.py` 中的 `SECRET_KEY` 为随机字符串
2. 修改管理员密码
3. 设置 `DEBUG = False`
4. 后端使用 gunicorn 运行：
   ```bash
   gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 -b 0.0.0.0:5000 "app:create_app()"
   ```
5. 前端构建生产版本：
   ```bash
   npm run build
   ```
   然后使用 nginx 托管 `dist` 目录
