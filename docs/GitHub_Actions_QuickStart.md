# GitHub Actions 快速开始指南

## 🚀 5分钟设置 GitHub Actions

### 步骤 1: 推送代码到 GitHub

```bash
# 如果还没有 Git 仓库
git init
git add .
git commit -m "Add GitHub Actions CI/CD"

# 推送到 GitHub（替换为你的仓库地址）
git remote add origin https://github.com/YOUR_USERNAME/SentimentSense.git
git branch -M main
git push -u origin main
```

### 步骤 2: 创建 GCP 服务账号密钥

```bash
# 设置项目 ID
export PROJECT_ID="your-project-id"

# 创建服务账号
gcloud iam service-accounts create github-actions \
    --display-name="GitHub Actions"

# 授予权限
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/container.developer"

# 创建密钥文件
gcloud iam service-accounts keys create github-actions-key.json \
    --iam-account=github-actions@$PROJECT_ID.iam.gserviceaccount.com

# 查看密钥内容（复制这个内容）
cat github-actions-key.json
```

### 步骤 3: 在 GitHub 中设置 Secrets

1. 打开你的 GitHub 仓库
2. 点击 **Settings** → **Secrets and variables** → **Actions**
3. 点击 **New repository secret**
4. 添加两个 secrets：

| Name | Value |
|------|-------|
| `GCP_PROJECT_ID` | 你的 GCP 项目 ID |
| `GCP_SA_KEY` | github-actions-key.json 的完整内容 |

### 步骤 4: 测试 GitHub Actions

推送任何代码更改：
```bash
git add .
git commit -m "Test GitHub Actions"
git push origin main
```

然后在 GitHub 仓库的 **Actions** 标签查看运行结果！

## 🎯 你现在拥有的功能

### ✅ 自动化检查
- **代码质量**: flake8 linting
- **格式检查**: black formatting
- **测试运行**: pytest 测试
- **Docker 构建**: 验证镜像构建
- **安全扫描**: 基础安全检查

### 🔄 工作流程
1. 推送代码 → 自动触发 CI
2. 所有检查通过 → 绿色勾号 ✅
3. 有问题 → 红色叉号 ❌ + 详细日志

### 📊 查看结果
- GitHub 仓库 → **Actions** 标签
- 点击任何工作流查看详细日志
- 绿色 = 成功，红色 = 失败

## 🛠️ 自定义配置

### 修改触发条件
编辑 `.github/workflows/simple-ci.yml`:
```yaml
on:
  push:
    branches: [ main, develop ]  # 添加更多分支
  pull_request:
    branches: [ main ]
```

### 添加更多检查
在工作流中添加新的 job：
```yaml
  my-custom-check:
    name: My Custom Check
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Run my check
      run: echo "Running custom check"
```

## 🎉 恭喜！

你现在有了一个完整的 CI/CD pipeline！

每次推送代码时，GitHub Actions 会自动：
- 检查代码质量
- 运行测试
- 构建 Docker 镜像
- 进行安全扫描

这就是现代软件开发的标准流程！🚀
