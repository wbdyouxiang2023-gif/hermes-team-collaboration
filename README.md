# Hermes Team Collaboration 🚀

**团队：moc-pro (本地) + 小虾米 (云端) + 小河虾 (自动化)**

## 🎯 目标

利用 GitHub 作为共享文件夹 + 协作平台，实现本地开发 + 云端协作。

## 📋 协作架构

```
┌─────────────────────────────┐
│  本地 (moc-pro)             │
│  - WSL2 Ubuntu              │
│  - 代码开发                 │
│  - 测试验证                 │
└────────────┬────────────────┘
             ↓ git push/pull
┌────────────▼────────────────┐
│  GitHub 仓库 (共享文件夹)   │
│  - wbdyouxiang2023-gif     │
│  - hermes-team-collaboration│
└────────────┬────────────────┘
             ↓ git push
┌────────────▼────────────────┐
│  云端 (小虾米 + 小河虾)    │
│  - PR Review                │
│  - Code Audit               │
│  - CI/CD (Actions)          │
│  - Auto Deploy              │
└─────────────────────────────┘
```

## 📁 目录结构

```
hermes-team-collaboration/
├── .github/
│   └── workflows/          # CI/CD 配置
├── docs/                   # 文档
├── hermes/                 # Hermes 相关代码
├── generative-art/         # 生图项目
├── scripts/                # 自动化脚本
├── CONTRIBUTING.md         # 贡献指南
└── README.md               # 本文件
```

## 🤝 协作流程

### 1. 本地开发
```bash
# 克隆仓库
git clone https://github.com/wbdyouxiang2023-gif/hermes-team-collaboration.git

# 创建功能分支
git checkout -b feature/xxx

# 开发、测试、提交
git add .
git commit -m "feat: xxx"

# 推送到远程
git push origin feature/xxx
```

### 2. 云端协作（小虾米）
```bash
# 创建 Pull Request
gh pr create --title "feat: xxx" --body "..."

# Code Review
gh pr review --approve <pr-number>

# 合并 PR
gh pr merge <pr-number>
```

### 3. 自动化（小河虾）
```yaml
# .github/workflows/ci.yml
# 自动测试、构建、部署
```

## 🚀 快速开始

### 本地 (moc-pro)
```bash
cd ~/.hermes/hermes-team-collaboration
# 开始开发...
```

### 云端 (小虾米/小河虾)
- PR 通知 → 飞书群聊
- Code Review → GitHub
- Auto Deploy → GitHub Actions

## 📝 规范

### 分支命名
- `main` - 生产分支（受保护）
- `develop` - 开发主分支
- `feature/xxx` - 新功能
- `bugfix/xxx` - 修复
- `release/vx.x` - 发布

### Commit 规范
```
feat: 新功能
fix: 修复 bug
docs: 文档更新
style: 格式调整
refactor: 重构
test: 测试
chore: 构建/工具
```

## 🎉 团队职责

| 成员 | 角色 | 职责 |
|------|------|------|
| **moc-pro** | 开发者 | 本地开发、测试、提交 |
| **小虾米** | 审核员 | PR Review、Code Audit |
| **小河虾** | 自动化 | CI/CD、自动部署 |

---

**开始协作吧！🚀**
