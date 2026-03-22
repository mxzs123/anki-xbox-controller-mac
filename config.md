# Xbox Controller for Anki - 配置说明

## button_mapping（按键映射）

将 Xbox 手柄按键映射到 Anki 动作。

| 手柄按键 | 配置键名 | 默认动作 | 说明 |
|---------|---------|---------|------|
| A | `A` | `answer_1` | Again（重来） |
| B | `B` | `answer_2` | Hard（困难） |
| X | `X` | `answer_3` | Good（良好） |
| Y | `Y` | `answer_4` | Easy（简单） |
| 左扳机 | `left_trigger` | `replay_audio` | 重放音频 |
| 右扳机 | `right_trigger` | `undo` | 撤回上一步 |

### 可用动作

- `answer_1` ~ `answer_4`：复习时从左到右的四个答题按钮
- `replay_audio`：重放当前卡片音频
- `undo`：撤回上一次操作
- `show_answer`：翻牌/显示答案
- `none`：不执行任何操作

### 操作逻辑

- 卡片正面时：按任意答题键 → 先翻牌显示背面
- 卡片背面时：按答题键 → 提交对应答案，进入下一张卡

## sounds（音效反馈）

- `enabled`：是否启用音效（true/false）
- `volume`：全局音量（0.0 ~ 1.0）
- `profiles`：每个动作对应的音效文件路径（相对于插件目录）

## poll_interval_ms

手柄轮询间隔（毫秒），默认 16ms（约 60Hz）。值越小响应越快但 CPU 占用越高。
