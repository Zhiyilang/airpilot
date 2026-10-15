# 🛡️ AirPilot — Airwallex 支付运维事故指挥官

**为 Airwallex Agentic Banking Hackathon 打造。** 一个盯着你 Airwallex 转账、

**绝不复付**地处置支付事故的智能体。

大脑只能*提议*补救方案；确定性验证器决定什么能动钱。这就是产品的全部：

**AirPilot 提议，验证器决定什么真正发生。**

## 它解决的问题

对应赛道 **Payment Ops Incident Commander**（starter kit 03）：*“在不重复付款的前提下
处置一笔延迟的供应商转账。”* 现实中这类问题天天发生：

- 供应商转账卡在 `review` 超过 SLA，于是有人“干脆重发一次”。
- 同一张发票被两个系统各排了一次，导致重复付款。
- 余额不够的转账被强行推送。

AirPilot 把这些变成“带审计轨迹的已处置事故”。

## 工作原理

```
感知 → 侦测 → 规划 → 验证 → 执行 → 回执
```

1. **感知** — 从 Airwallex 拉取余额与转账（鉴权 → 余额 → 转账）。
2. **侦测** — 纯函数检测器发现：`delayed_transfer`（延迟）、
   `duplicate_payment_risk`（重复付款风险）、`insufficient_balance`（余额不足）。
3. **规划** — 大脑提议补救（`retry` / `hold` / `refund` / `fund`）。
4. **验证** — 在任何 API 调用前检查五条规则：
   - **幂等** — 绝不创建与已有转账重复的转账
   - **余额** — 转账不得超出可用余额
   - **有界** — 动作必须指向它要处置的事故
   - **白名单** — 仅允许已知安全的补救类型
   - **不自付** — 收款方 ≠ 出款账户
5. **执行** — 只有通过验证的提议才调用 Airwallex（`create_transfer` / `create_refund`）。
6. **回执** — 记录每个事故、提议、裁决与动作，并生成自包含 HTML 报告。

```bash
python -m airpilot command                # 一次事故指挥（JSON 回执）
python -m airpilot command --html r.html
python -m airpilot demo                   # 内置场景
```

## Airwallex 集成

`client.py` 用标准库 `urllib` 封装 Airwallex v1 API（无需 SDK）。无凭据或
任何 API 错误时**自动降级到内置 fixture**，回执标注 `source: offline-fixture`。
接入真实账户只需设置环境变量，无需改代码。

## 自验证

```bash
python eval.py          # 15 条断言，无需联网、无需凭据
```

## 许可证

MIT — 见 `LICENSE`。
