# opencode-python

OpenCode Python 版本 - 一个基于 Typer 的命令行工具。

## 代码格式化

项目配置了 pre-commit hooks 来自动格式化代码，确保符合 Flake8 标准。

### 设置

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 安装 pre-commit hooks
pre-commit install
```

### 使用

安装后，每次 `git commit` 时会自动运行代码格式化检查。

手动运行检查：
```bash
pre-commit run --all-files
```

## 使用方法

```bash
# 运行应用
python -m cli.chat start
```