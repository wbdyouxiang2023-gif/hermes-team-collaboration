# Hermes Team Collaboration - Project Guide

## 仓库定位

这是 Hermes 项目的**统一代码仓库**，用于团队协作、版本管理和 CI/CD。
所有子项目以**子目录**形式共存，互不干扰。

---

## 目录结构

```
hermes-team-collaboration/          <- 仓库根目录
├── .github/
│   └── workflows/
│       └── hermes-automation.yml   <- CI/CD 自动化
├── docs/
│   └── guide.md                    <- 本文件（项目指导）
├── evolution/                       <- Evolution V6.1 记忆系统
│   ├── evolution/                  <- Python 包
│   │   ├── __init__.py
│   │   ├── schema.py               <- 数据模型
│   │   ├── logger.py               <- 经验记录 + 脱敏
│   │   ├── config.py               <- 集中配置
│   │   ├── bridge_worker.py        <- Hermes 子进程桥接
│   │   ├── memory/
│   │   │   ├── episodic.py         <- 情景记忆（JSONL 查询）
│   │   │   ├── semantic.py         <- 语义记忆（BGE 向量）
│   │   │   ├── retriever.py        <- 统一检索层
│   │   │   ├── intelligence.py     <- 记忆智能（规则引擎）
│   │   │   └── memory_activation.py <- 软降权
│   │   └── context/
│   │       └── context_builder.py  <- 检索结果 → LLM 上下文
│   ├── tests/                      <- 36 个单元测试
│   ├── pyproject.toml              <- 包配置
│   ├── README.md                   <- Evolution 专属文档
│   └── .gitignore
├── LICENSE                          <- MIT
├── README.md                       <- 仓库总览
└── .gitignore
```

---

## 如何添加新子项目

### 步骤

1. **在仓库根目录创建子目录**
   ```bash
   mkdir my-new-project
   ```

2. **初始化项目文件**
   ```bash
   # 如果是 Python 项目
   cd my-new-project
   # ... 创建代码文件 ...
   ```

3. **提交到独立分支**（推荐）
   ```bash
   git checkout -b feature/my-new-project
   git add my-new-project/
   git commit -m "feat: add my-new-project"
   git push origin feature/my-new-project
   ```

4. **创建 PR 合并到 main**
   ```bash
   gh pr create --title "feat: add my-new-project" --body "Description"
   ```

### 规则

| 规则 | 说明 |
|------|------|
| 子项目独立目录 | 每个项目一个顶级子目录 |
| 不要改别人的目录 | 除非有明确授权 |
| 新项目先开分支 | `feature/xxx` 分支开发，PR 合并 |
| 敏感信息不入库 | API key / token / 密码走 .gitignore |
| 测试随代码走 | 每个子项目自带测试 |

---

## 分支策略

```
main                    <- 生产稳定版（受保护）
  └── develop           <- 开发集成分支
       ├── feature/xxx <- 功能分支
       ├── fix/xxx      <- 修复分支
       └── experiment/xxx <- 实验分支
```

### 命名规范

- `feature/项目名-功能描述` 例：`feature/evolution-v6.2`
- `fix/项目名-问题描述`    例：`fix/evolution-retriever-bug`
- `experiment/描述`       例：`experiment/rag-vs-keyword`

---

## 部署指南

### Evolution 部署到服务器

```bash
# 1. 拉取最新代码
cd ~/.hermes/hermes-team-collaboration
git pull origin main

# 2. 部署 evolution 到运行目录
for f in evolution/evolution/__init__.py \
         evolution/evolution/schema.py \
         evolution/evolution/logger.py \
         evolution/evolution/config.py \
         evolution/evolution/bridge_worker.py \
         evolution/evolution/evaluate_intelligence.py; do
    cp "$f" ~/.hermes/evolution/$(basename "$f")
done

for f in evolution/evolution/memory/__init__.py \
         evolution/evolution/memory/episodic.py \
         evolution/evolution/memory/semantic.py \
         evolution/evolution/memory/retriever.py \
         evolution/evolution/memory/intelligence.py \
         evolution/evolution/memory/memory_activation.py; do
    cp "$f" ~/.hermes/evolution/memory/$(basename "$f")
done

for f in evolution/evolution/context/__init__.py \
         evolution/evolution/context/context_builder.py; do
    cp "$f" ~/.hermes/evolution/context/$(basename "$f")
done

# 3. 重建 venv（如需要）
cd ~/.hermes/evolution
python3 -m venv venv
source venv/bin/activate
pip install numpy sentence-transformers

# 4. 验证
cd ~/.hermes
python3 -c "import sys; sys.path.insert(0, '.'); \
  from evolution.memory.intelligence import MemoryIntelligence; \
  m = MemoryIntelligence(); \
  print('Deploy OK')"
```

---

## 团队协作

### 角色

| 成员 | 职责 |
|------|------|
| moc-pro | 本地开发、测试、提交代码（Owner） |
| 小虾米 | Code Review、质量检查 |
| 小河虾 | GitHub Actions 自动化 |

### 工作流

1. moc-pro 在本地开发，推送到 feature 分支
2. 创建 PR → 自动触发 CI 测试
3. 合并到 main → 自动部署

### 飞书群

群组："open 机器大战"

---

## 安全注意事项

1. **GitHub Token** 不入库，使用 GitHub Secrets
2. **API Keys** 写在服务器 `~/.hermes/.env`，不入仓库
3. **敏感数据** 在 Logger 中自动脱敏（sk- / ghp_ / Bearer 等）
4. **私有仓库** - 仅团队可见

---

## 常用命令速查

```bash
# 克隆
gh repo clone wbdyouxiang2023-gif/hermes-team-collaboration

# 创建功能分支
git checkout -b feature/xxx

# 提交并推送
git add . && git commit -m "feat: xxx" && git push origin feature/xxx

# 创建 PR
gh pr create --title "feat: xxx" --body "Description"

# 查看仓库状态
gh repo view

# 查看 CI 状态
gh run list --limit 5
```