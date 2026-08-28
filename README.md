# Hermes Team Collaboration

**统一代码仓库** — Evolution 记忆系统、工具脚本、配置文档的版本管理中心。

---

## 仓库结构

```
hermes-team-collaboration/
├── evolution/           <- Evolution V6.1 记忆系统（核心项目）
├── docs/                <- 项目文档与指导
│   └── guide.md         <- 完整指导文件
├── .github/workflows/   <- CI/CD 自动化
├── LICENSE              <- MIT
└── README.md            <- 本文件
```

## 子项目一览

| 子目录 | 版本 | 状态 | 说明 |
|--------|------|------|------|
| `evolution/` | V6.1 | 生产运行中 | Hermes 经验记忆引擎（情景+语义+智能+激活） |

## 快速开始

```bash
# 克隆
gh repo clone wbdyouxiang2023-gif/hermes-team-collaboration

# 查看 Evolution 文档
cat evolution/README.md

# 查看完整指导（部署、分支策略、团队协作）
cat docs/guide.md
```

## 文档索引

- **完整指导**：[`docs/guide.md`](docs/guide.md) — 添加新项目、部署、分支策略、团队协作
- **Evolution 文档**：[`evolution/README.md`](evolution/README.md) — 架构、组件、Bug 修复记录、配置

## 团队

| 成员 | 角色 |
|------|------|
| moc-pro | Owner / 开发 |
| 小虾米 | Code Review |
| 小河虾 | 自动化 |

---

**License**: MIT