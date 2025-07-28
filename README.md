# OpenCode Python

OpenCode Python 是一个基于 Typer 的命令行工具，支持多种 AI 模型提供商，并提供智能代理功能来执行各种工具操作。

## 功能特性

- 🤖 **多模型支持**: 支持 OpenAI、Qwen (DashScope)、Ollama 等多种 AI 模型
- 🛠️ **智能代理**: 内置 SimpleToolAgent，能够自动选择合适的工具执行任务
- 📁 **文件操作**: 提供文件读写、目录创建、文件列表等操作
- 🧮 **数学计算**: 支持基本的数学运算（加、减、乘、除）
- 🔧 **工具注册系统**: 灵活的工具注册和管理机制
- 💬 **交互式聊天**: 支持自然语言交互和命令模式

## 系统要求

- Python 3.12+
- 至少配置一个 AI 模型提供商

## 安装

### 1. 克隆仓库

```bash
git clone <repository-url>
cd opencode_python
```

### 2. 安装依赖

```bash
# 安装基本依赖
pip install -e .

# 安装开发依赖（可选）
pip install -e ".[dev]"
```

### 3. 配置环境变量

根据您要使用的 AI 模型提供商，设置相应的环境变量：

#### OpenAI
```bash
export OPENAI_API_KEY="your-openai-api-key"
```

#### Qwen (DashScope)
```bash
export DASHSCOPE_API_KEY="your-dashscope-api-key"
```

#### Ollama
确保 Ollama 服务正在运行：
```bash
# 启动 Ollama 服务
ollama serve
```

## 使用方法

### 基本命令

```bash
# 启动交互式聊天（默认使用代理模式）
python main.py agent

# 启动普通聊天模式
python main.py chat start

# 列出可用的模型提供商
python main.py chat providers

# 测试特定提供商
python main.py chat test --provider openai --user-query "Hello, how are you?"

# 生成单次响应
python main.py chat generate "What is the weather like?" --provider qwen
```

### 命令行选项

#### Agent 模式
```bash
python main.py agent [OPTIONS]

Options:
  -p, --provider TEXT    指定使用的提供商 (openai/qwen/ollama)
  -s, --system-prompt TEXT  设置系统提示词
  -a, --agent BOOLEAN    启用代理模式 (默认: True)
```

#### Chat 模式
```bash
python main.py chat start [OPTIONS]

Options:
  -p, --provider TEXT    指定使用的提供商
  -s, --system-prompt TEXT  设置系统提示词
```

### 交互式命令

在聊天界面中，您可以使用以下命令：

#### 基本命令
- `/help` - 显示帮助信息
- `/quit`, `/exit`, `/bye` - 退出聊天
- `/info` - 显示当前提供商信息
- `/switch <provider>` - 切换到其他提供商

#### 系统设置
- `/system <prompt>` - 设置系统提示词
- `/clear` - 清除系统提示词

#### 工具操作
- `/tools` - 列出可用工具
- `/math <operation> <args>` - 执行数学运算
- `/file <operation> <args>` - 执行文件操作
- `/agent <query>` - 使用代理处理查询

### 数学运算示例

```bash
# 在聊天中使用
/math add 5 3 2
/math subtract 10 3
/math multiply 4 5
/math divide 20 4

# 直接使用工具命令
python main.py tools math add 5 3 2
python main.py tools math subtract 10 3
```

### 文件操作示例

```bash
# 在聊天中使用
/file read example.txt
/file write new_file.txt "Hello, World!"
/file list .
/file create new_directory

# 直接使用工具命令
python main.py tools read example.txt
python main.py tools write new_file.txt "Hello, World!"
python main.py tools ls .
python main.py tools mkdir new_directory
```

## 支持的 AI 模型提供商

### 1. OpenAI
- 需要设置 `OPENAI_API_KEY` 环境变量
- 支持 GPT-3.5 和 GPT-4 模型

### 2. Qwen (DashScope)
- 需要设置 `DASHSCOPE_API_KEY` 环境变量
- 支持通义千问系列模型

### 3. Ollama
- 需要本地运行 Ollama 服务
- 支持各种开源模型（如 Llama、Mistral 等）

## 工具系统

### 内置工具

#### 数学工具
- `add` - 加法运算
- `subtract` - 减法运算
- `multiply` - 乘法运算
- `divide` - 除法运算

#### 文件工具
- `read_file` - 读取文件内容
- `write_file` - 写入文件内容
- `list_dir` - 列出目录内容
- `create_dir` - 创建目录

### 自定义工具

您可以通过 `@register_tool` 装饰器注册自定义工具：

```python
from tool_registry.registry import register_tool

@register_tool(
    name="my_tool",
    description="My custom tool",
    tags=["custom"],
    version="1.0.0"
)
def my_custom_tool(param1: str, param2: int) -> str:
    """Custom tool implementation"""
    return f"Processed: {param1}, {param2}"
```

## 代理系统

OpenCode 使用 SimpleToolAgent 来智能处理用户查询：

1. **规划阶段**: 分析用户查询，确定需要使用的工具
2. **执行阶段**: 调用相应的工具执行操作
3. **响应阶段**: 生成最终的用户响应

### 代理使用示例

```bash
# 启动代理模式
python main.py agent

# 在聊天中询问
You: 计算 15 加 23 的结果
Assistant: 我将使用数学工具来计算 15 + 23 的结果。
Tool 'add' returned: 38
Result: 38

You: 读取当前目录的文件列表
Assistant: 我将使用文件工具来列出当前目录的内容。
Tool 'list_dir' returned: ['file1.txt', 'file2.py', 'README.md']
当前目录包含以下文件：file1.txt, file2.py, README.md
```

## 开发

### 代码格式化

项目配置了 pre-commit hooks 来自动格式化代码：

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 安装 pre-commit hooks
pre-commit install

# 手动运行检查
pre-commit run --all-files
```

### 项目结构

```
opencode_python/
├── agents/           # 代理系统
├── cli/             # 命令行界面
├── providers/       # AI 模型提供商
├── tools/           # 工具实现
├── tool_registry/   # 工具注册系统
├── examples/        # 示例代码
└── main.py         # 主入口文件
```

## 故障排除

### 常见问题

1. **没有可用的提供商**
   - 确保至少配置了一个 AI 模型提供商
   - 检查环境变量是否正确设置
   - 对于 Ollama，确保服务正在运行

2. **工具执行失败**
   - 检查文件权限
   - 确保路径正确
   - 查看错误信息进行调试

3. **代理模式不工作**
   - 确保提供商配置正确
   - 检查网络连接
   - 查看日志信息

### 调试模式

```bash
# 启用详细日志
export PYTHONPATH=.
python -m cli.agent_chat start --provider openai
```

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 贡献

欢迎提交 Issue 和 Pull Request 来改进项目！

## 更新日志

### v0.1.0
- 初始版本发布
- 支持多 AI 模型提供商
- 实现智能代理系统
- 提供基础工具集
- 完整的命令行界面