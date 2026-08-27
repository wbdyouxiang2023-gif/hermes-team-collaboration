# Hermes Team Collaboration 🚀

**团队：moc-pro (本地) + 小虾米 (云端 Code Review) + 小河虾 (自动化)**

## 🎯 项目目标

利用 GitHub 作为共享文件夹 + CI/CD 平台，实现：
- **moc-pro**: 本地开发、测试、提交代码
- **小虾米**: 代码 Review、质量检查
- **小河虾**: GitHub Actions 自动化、每日备份

---

## 📋 团队协作流程

### 1. 开发流程
```bash
# moc-pro 在本地开发
cd ~/.hermes/hermes-team-collaboration

# 创建功能分支
git checkout -b feature/xxx

# 提交代码
git add .
git commit -m "feat: xxx"

# 推送到远程
git push origin feature/xxx

# 创建 Pull Request
gh pr create --title "feat: xxx" --body "..."
```

### 2. 自动触发
- **PR 创建** → 小虾米自动检查代码质量
- **每日午夜** → 小河虾自动备份
- **推送更新** → 自动验证基础语法

### 3. 飞书通知
- **Code Review 完成** → 飞书群通知
- **每日备份** → 飞书群通知
- **问题报告** → 飞书群@moc-pro

---

## 🔧 CI/CD 流水线

### GitHub Actions 配置

`.github/workflows/hermes-automation.yml`:

| Job | 负责人 | 功能 |
|-----|--------|------|
| `xiaoxiami-review` | 小虾米 | 代码质量检查 |
| `xiaohe-automation` | 小河虾 | 自动化测试 |
| `daily-backup` | 小虾米 + 小河虾 | 每日备份 |

### 触发条件
- `push` (main, develop)
- `pull_request` (main, develop)
- `issues` (opened, labeled, unlabeled)
- `schedule` (每天午夜)

---

## 📁 仓库结构

```
hermes-team-collaboration/
├── .github/
│   └── workflows/
│       └── hermes-automation.yml  # CI/CD 流水线
├── LICENSE                        # MIT 许可证
├── README.md                      # 项目说明
└── ... (开发代码)
```

---

## 🔑 权限配置

### GitHub Token
- **Owner**: 你的账号 (`wbdyouxiang2023-gif`)
- **Bot 认证**: 使用 GitHub Actions `secrets.GITHUB_TOKEN`

### 飞书 Bot
- **群组**: "open 机器大战"
- **@格式**: 必须用富文本卡片 (`post`) + `open_id`
- **小虾米**: `ou_7b550e91fc855f7d61f0f7807f5d2d3d`
- **小河虾**: `ou_e049cabdd12c285fbb2c4c83d4831a69`

---

## 🚀 快速开始

### 克隆仓库
```bash
git clone https://github.com/wbdyouxiang2023-gif/hermes-team-collaboration.git
cd hermes-team-collaboration
```

### 创建功能分支
```bash
git checkout -b feature/your-feature
```

### 提交代码
```bash
git add .
git commit -m "feat: add new feature"
git push origin feature/your-feature
```

### 创建 Pull Request
```bash
gh pr create --title "feat: new feature" --body "Description"
```

---

## 📝 注意事项

1. **私有仓库** - 仅团队可见
2. **License**: MIT
3. **CI/CD**: 自动触发，无需手动配置
4. **飞书通知**: 需要配置 Webhook URL (待添加)

---

## 🤝 贡献流程

1. Fork 本仓库
2. 创建功能分支 (`feature/xxx`)
3. 提交代码并推送到远程
4. 创建 Pull Request
5. 等待自动检查 (小虾米)
6. 等待审核和合并

---

## 📊 状态

- ✅ 仓库已创建
- ✅ CI/CD 流水线已配置
- ✅ 飞书邀请消息已发送
- ⏳ 等待团队确认
- ⏳ 配置飞书 Webhook URL

---

## 🔗 相关链接

- **GitHub 仓库**: https://github.com/wbdyouxiang2023-gif/hermes-team-collaboration
- **飞书群组**: "open 机器大战"
- **项目文档**: 本仓库 README + Wiki

---

**团队协作，共创价值！✨**
