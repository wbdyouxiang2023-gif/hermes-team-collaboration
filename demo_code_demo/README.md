# 团队协作 Demo

## 功能说明

本目录包含团队协作项目的示例代码和演示文件。

## 目录结构

```
demo_code_demo/
├── demo_code_demo.py    # 示例代码
├── demo_readme.md       # 使用说明
└── config.yaml          # 配置文件
```

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/wbdyouxiang2023-gif/hermes-team-collaboration.git
cd hermes-team-collaboration
```

### 2. 创建功能分支

```bash
git checkout -b feature/demo-code-demo
```

### 3. 开发功能

```python
from demo_code_demo import MocPro

moc_pro = MocPro()
moc_pro.develop("新功能")
```

### 4. 提交代码

```bash
git add .
git commit -m "feat: add demo code"
git push origin feature/demo-code-demo
```

### 5. 创建 PR

使用 GitHub CLI:
```bash
gh pr create --title "feat: add demo code" --body "Demo code for team collaboration"
```

## 团队协作流程

1. **moc-pro**: 本地开发，创建功能分支
2. **小虾米**: PR Review，代码质量检查
3. **小河虾**: 自动测试，CI/CD 流水线
4. **团队**: 合并 PR，发布到 main 分支

## 注意事项

- 所有代码需通过自动化测试
- PR 需至少 1 个 Reviewer 批准
- 遵循代码风格指南
- 更新文档和 CHANGELOG

