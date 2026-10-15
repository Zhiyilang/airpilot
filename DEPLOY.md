# AirPilot 部署指南

## 本地
```bash
pip install -r requirements.txt
python eval.py                 # 自测，无需密钥
python -m airpilot demo        # 内置事故场景
python app.py                  # Web UI（读 PORT，绑 0.0.0.0）
```

## 接入真实 Airwallex（沙箱 / 生产）
```bash
export AIRWALLEX_API_KEY=...
export AIRWALLEX_API_SECRET=...
export AIRWALLEX_BASE_URL=https://api.airwallex.com   # 沙箱用 api-demo.airwallex.com
python -m airpilot command     # 直连真实账户
```
无上述变量时自动降级到内置 fixture（回执标注 `offline-fixture`）。

## Render（Web UI 公开部署）
仓库含 `render.yaml`，在 Render 新建 Blueprint 即自动按此部署：
- `type: web`，`runtime: python`，`plan: free`
- `buildCommand: pip install -r requirements.txt`
- `startCommand: python app.py`（读 `PORT`，绑 `0.0.0.0`）
- 可选：在 Render 环境变量里填 `AIRWALLEX_API_KEY/SECRET` 直连真实账户

## 健康检查
Web 应用启动即监听 `PORT`；Gradio 默认提供 `/` 页面。
