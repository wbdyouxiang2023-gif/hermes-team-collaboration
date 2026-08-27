# CI/CD 自动化配置

## 🎯 自动化工具（小河虾）

### GitHub Actions 流水线

#### 1. CI - 自动测试

`.github/workflows/ci.yml`:
```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest black flake8
      
      - name: Run tests
        run: pytest tests/ -v
      
      - name: Code style check
        run: |
          flake8 . --max-line-length=120
          black --check .
```

#### 2. Auto Deploy - 自动部署

`.github/workflows/deploy.yml`:
```yaml
name: Deploy to Pages

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build docs
        run: |
          pip install mkdocs
          mkdocs build
      
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./site
```

#### 3. Daily Backup - 每日备份

`.github/workflows/backup.yml`:
```yaml
name: Daily Backup

on:
  schedule:
    - cron: '0 0 * * *'  # 每天午夜 UTC
  workflow_dispatch:  # 手动触发

jobs:
  backup:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Create backup commit
        run: |
          echo "Backup: ${{ github.sha }}" >> BACKUP_LOG.md
          git config user.name "github-actions"
          git config user.email "github-actions@github.com"
          git add BACKUP_LOG.md
          git commit -m "chore: daily backup ${{ github.sha }}" || echo "No changes"
          git push
```

## 📊 监控与通知

### 飞书通知

当 PR 创建/合并时，发送飞书消息到群聊。

### Issue 追踪

自动给 Issue 添加标签、分配给成员。
