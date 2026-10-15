# AirPilot — Airwallex Agentic Banking Hackathon 提交文案

> 复制本文件到 Airwallex Hackearth 提交表单（Devpost 类）。所有字段可直接粘贴。

## 赛事与赛道
- **赛事**：Airwallex Agentic Banking Hackathon 2026（airwallex.hackerearth.com）
- **主赛道**：Starter Kit 03 — **Payment Ops Incident Commander**
  （"Resolve a delayed supplier transfer without paying twice"）
- **开放奖项**：Founder's Choice $30,000 / Judges' Choice $20,000
  （无特定合作方约束，纯看构建质量）
- **硬要求**：使用 Airwallex API 构建智能体化金融应用；需可运行 demo + <5min 视频 + 仓库链接

## 项目一句话
AirPilot 是一个 Airwallex 原生的“支付运维事故指挥官”：监控转账、发现事故
（延迟 / 重复付款风险 / 余额不足），**由确定性验证器把关，绝不复付**。

## 它如何用 Airwallex API（硬要求命中）
`airpilot/client.py` 封装 Airwallex v1：
- `POST /api/v1/authentication/login`（API Key + Secret 鉴权）
- `GET /api/v1/balances`（余额核对，防透支）
- `GET /api/v1/transfers` / `POST /api/v1/transfers/create`（处置延迟/重发）
- `POST /api/v1/refunds/create`（争议退款）

无凭据时自动降级到内置 fixture（回执标注 `offline-fixture`），因此 demo 与
`eval.py` 无需密钥即可完整运行；填入沙箱凭据即直连真实 API，**代码零改动**。

## 差异化（为什么该拿 Founder's / Judges' Choice）
1. **证明“永不复付”**：验证器在任意动钱动作前执行幂等 + 余额 + 不自付检查。
   `eval.py` 里 `test_retry_blocked_on_duplicate` 直接证明：对一笔已有相同
   已完成转账的重复单，重发被拦截。这是支付场景最致命的失败模式的工程化兜底。
2. **完全可审计**：检测器是纯函数，回执逐条写明“哪笔、多少、哪条规则决定”。
3. **离线优先 / 零 SDK 依赖**：决策层纯标准库，LLM（如接入）只是升级路径，
   不是依赖——符合“agentic banking”对可控、可解释的要求。

## 演示步骤（<5min 视频分镜）
| 时间 | 画面 | 旁白 |
|---|---|---|
| 0:00–0:30 | 终端跑 `python -m airpilot demo`，展示 JSON 回执 | “这是一笔卡在 review 的供应商款 + 一笔重复付款风险” |
| 0:30–1:30 | 切 `eval.py` 输出，指 `test_retry_blocked_on_duplicate` | “验证器在动钱前拦下重复付款——永不付两次” |
| 1:30–2:30 | 浏览器打开 `python app.py`，点 Run | “Web 端同样跑同一套可审计闭环” |
| 2:30–3:30 | 展示 `client.py` 的 Airwallex API 映射 + 降级逻辑 | “直连 Airwallex，无密钥自动降级，零改码” |
| 3:30–4:30 | 回执 HTML 高亮 BLOCKED 行 | “每个事故都有裁决与动作记录，可审计” |

## 评分对照
- **创新性**：把“支付安全”做成智能体的确定性闸门，而非黑箱提示。
- **实用性**：直接命中延迟供应商款 + 重复付款两个高频真实痛点。
- **表达清晰度**：15 条断言自测 + 自包含回执 + 中英 README，开箱即跑。

## 提交清单
- [ ] 仓库公开（MIT），含 README / README.zh / eval.py
- [ ] 录制 <5min 视频（按上表分镜）
- [ ] 填写本文件对应字段
- [ ] 备注：使用 Airwallex v1 API；沙箱凭据直连，无凭据降级演示
- [ ] 注册截止 2026-10-23（IST）／ 提交截止 2026-11-13（IST）
