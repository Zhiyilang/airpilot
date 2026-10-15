# AirPilot 演示脚本（< 5 分钟）

> 🎬 **成品视频已产**：`airpilot/airpilot_demo.mp4`（20.1s，英文终端实录+字幕，
> 全部为真实运行输出，非表演）——可直接上传 YouTube Unlisted 提交；下方分镜为
> 备用人工录制版（需旁白）。

目标：在 5 分钟内让评委相信“这个智能体用 Airwallex API 真能处置支付事故，
且绝不复付”。

## 前置（30 秒，镜头外完成）
- 已 `pip install -r requirements.txt`
- 终端在 `airpilot/` 目录
- 浏览器待命 `python app.py`

## 分镜
1. **0:00–0:30 终端 demo（最有说服力）**
   跑 `python -m airpilot demo`。
   镜头停在 JSON 回执：`incidents_found: 2, acted: 1, blocked: 1`，
   高亮 `duplicate_payment_risk` 那行 `BLOCKED`。
   旁白：“一笔延迟供应商款被重发，一笔重复付款被拦下——后者一分钱没动。”

2. **0:30–1:30 跑 eval，指关键断言**
   跑 `python eval.py`，滚到 `test_retry_blocked_on_duplicate ... ok`。
   旁白：“验证器在任意动钱动作前跑幂等检查；这笔重复单会被直接拒绝。
   这是支付场景最贵的错误——付两次——的工程化兜底。”

3. **1:30–2:30 Web 演示**
   开 `python app.py`，点 “Run Incident Commander”。
   旁白：“同一套可审计闭环，Web 端一样跑。”

4. **2:30–3:30 代码即证据**
   打开 `airpilot/client.py`，指 Airwallex API 映射；打开 `verifier.py`
   指五条规则。旁白：“直连 Airwallex v1；无密钥自动降级到 fixture，零改码。”

5. **3:30–4:30 回执审计价值**
   打开生成的 HTML 回执，高亮 `BLOCKED` 行与 `source: offline-fixture`。
   旁白：“每个事故都有裁决与动作，可审计、可复盘。”

## YouTube / 视频元数据
- 标题：`I built an Airwallex agent that is physically unable to pay twice`
- 描述：AirPilot — Payment Ops Incident Commander for the Airwallex Agentic
  Banking Hackathon. Proposes remedies; a deterministic verifier decides what
  moves money. Never double-pays. github.com/Zhiyilang/airpilot
- 标签：`airwallex` `agentic-banking` `fintech` `ai-agents` `python` `open-source`
