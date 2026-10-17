# Airwallex Agentic Banking Hackathon — 零思考注册包（2026-10-17 官方页逐字核实）

> 目标：用户 10-24 02:29（北京）注册截止前，用 ≤15 分钟完成注册 + 沙盒 Key 申请，不错过任何官方坑。
> 官方页：**https://airwallex.hackerearth.com**（HackerEarth 平台，不是 Airwallex 官网报名）

## 一、官方时间线（全部已核实）

| 节点 | 官方口径 | 北京时间 |
|---|---|---|
| 申请开启 | Oct 5, 2026（SF Tech Week） | 已开 |
| **申请截止** | Oct 23（官方页）；Internshala 细化为 10-23 23:59 IST | **10-24 02:29（按最严口径，别卡点）** |
| 录取通知 + 建造期开始 | Oct 25 | 10-25 |
| **提交截止** | Nov 13, 2026 | 11-13 |
| 决赛名单 | Nov 15 | 11-15 |
| Demo Day（SF，可远程） | Nov 19 | 11-19 |

## 二、奖金结构（官方页原文）

| 奖项 | 金额 | 条件 |
|---|---|---|
| **Founder's Choice** | **$30,000** | 开放类，无特定要求 ← **主攻这个（最高现金奖）** |
| Judges' Choice | $20,000 | 开放类，无特定要求 |
| Visa Award | $15,000 | 需使用 Visa + Airwallex 工具 |
| Metal Award | $15,000 | 需使用 Metal + Airwallex 工具 |
| Claude Credits | $10,000 | 全体可申 |
| AWS Credits | $50,000 | 全体可申 |
| Base44 Credits | $16,000 | 全体可申 |

**现金共 $80,000 + credits 共 $76,000。** 打法：AirPilot 打 Founder's Choice（开放类，无需额外集成赞助工具）；Visa/Metal 专项奖各 $15k，若建造窗有剩余时间再评估集成（优先级低于提交质量）。

## 三、注册五步（照做，每步都有官方依据）

1. **打开 https://airwallex.hackerearth.com → Register**（免费；18+；全球开放——中国可参加）
2. **队伍规模 1-4 人**：单人可报（你目前一人队；现场/社区可组队，但不组也能打）
3. **填申请表**：项目方向直接写 "Payment Ops Incident Commander（Track 03）—— an agent that resolves delayed supplier transfers without ever double-paying"（与官方赛道描述字面一致，提高录取率）
4. **注册即得**：Airwallex sandbox + 技术工作坊 + Airwallex 工程导师（官方 FAQ 原文 "every registered participant gets access to the Airwallex sandbox and workshops"）
5. **等 10-25 录取邮件**（官方：Oct 25 accepted teams notified，build period begins）

## 四、⚠️ 沙盒 KYC 坑（官方开发者文档原文，不照做会卡住）

注册 sandbox 后创建实体时，**实体名必须用 "New Business Sandbox" 或 "Sandbox Business"**——这两个名字系统才会自动批准 KYC/KYB 验证。用其他名字会永远卡在 "In review" 不激活。（来源：airwallex.com/docs/developer-tools__demo-environment-overview）

**API Key 获取路径**（官方文档）：
1. Web app → **Account > Developer > API keys** → 生成 sandbox API keys
2. 拿到 **sandbox Client ID + API key** → 用它换 access token → 调 sandbox API 端点
3. Webhook 测试建议白名单 IP（sandbox 环境收 webhook 事件需要）

## 五、参赛载体（已就绪，无需再建）

- **仓**：`github.com/Zhiyilang/airpilot`（10-25 00:30 自动化转公开——正好是建造期开始日，官方要求公开仓可复现）
- **赛道**：Track 03「Payment Ops Incident Commander」——README 标题即官方赛道字面命中（"without ever double-paying" ↔ "without paying twice"）
- **宣称实测**：`python eval.py` → **40/40 全过**（2026-10-17 本地复跑确认）；含 5 类事故检测器（delayed_transfer / duplicate_payment_risk / insufficient_balance + 2 个对抗模式）+ 幂等账本 + 确定性验证器（"proposes, verifier decides"）
- **视频**：`airpilot_demo.mp4` 已在仓
- **提交物要求**（官方）：working demo + **<5 分钟视频走查** + 仓库链接（含 setup 说明）
- **文案**：`airpilot/SUBMISSION.md` + `airpilot/FRICTION_LOG.md`（诚实登记表）

## 六、建造窗计划（10-25 ~ 11-13，19 天）

1. 沙盒 Key 到手 → 真连 Airwallex sandbox API（auth → balances → transfers 三跳，README 的 PERCEIVE 段已是真代码路径）
2. 录 <5min 视频：事故注入 → 检测 → 验证器裁决 → 幂等回执全流程
3. 11-13 前提交；若有余力评估 Visa/Metal 专项集成
4. 决赛（11-15 公布）后准备 11-19 Demo Day（可远程，官方明确 remote teams can access judging）

## 七、申请表字段预制（打开表单直接对照粘，目标 ≤10 分钟）

HackerEarth 申请表字段各站略有差异，下表按官方站常见字段预制；**标 🖊️ 的只有你能填**，其余复制即用。

| 表单字段 | 粘这个 |
|---|---|
| Full name | 支一郎 |
| Country / Region of residence | China（全球开放，中国可参加——官方 FAQ 已核实） |
| Email / Phone | 🖊️ 你的常用邮箱+手机 |
| Team size | 1（solo allowed，官方 1-4 人） |
| GitHub profile | https://github.com/Zhiyilang |
| LinkedIn / portfolio | 🖊️ 没有就填 GitHub 链接（不填通常不卡审） |
| Track / Project direction | Payment Ops Incident Commander（Track 03）— an agent that resolves delayed supplier transfers without ever double-paying |
| What will you build？（项目简述，粘这段） | An agent that watches outbound supplier transfers, classifies five incident types (delayed transfer, duplicate-payment risk, insufficient balance, plus two adversarial retry patterns), and routes each to the right action. The core guarantee: **every proposed action passes a deterministic verifier before execution, and an idempotent ledger makes double-paying structurally impossible** — each decision produces an evidence-carrying receipt. Built on the Airwallex sandbox API (auth → balances → transfers). |
| Skills / tech | Python (stdlib-only), LLM agents, MCP, RPA automation, Airwallex sandbox API |
| How did you hear about this | SF Tech Week / Airwallex |
| Prior hackathon experience | 🖊️ 一句即可（可写"多个 AI agent hackathons; see github.com/Zhiyilang"） |

**提交前最后一眼**：Track 名称与官方赛道描述字面对齐（"without ever double-paying" ↔ 官方 "without paying twice"）——这个词是本赛道原文，评委检索时直接命中。

## 八、用户动作清单（勾选框）

- [ ] 10-24 02:29 前：HackerEarth 注册（第三节五步）
- [ ] 注册后立即按第四节建 sandbox 实体（**实体名用 "Sandbox Business"**）
- [ ] Key 到手后告诉 AI，AI 协助接线与视频脚本
- [ ] 10-25 查收录取邮件
- [ ] 11-13 前提交（第四节路径产出 + 视频 + 仓链接）
