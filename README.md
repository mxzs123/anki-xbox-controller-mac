# Xbox Controller for Anki (macOS)

用 Xbox 手柄复习 Anki 卡片。支持连击计数（Combo）、震动反馈（Haptics）和音效，把枯燥的背卡变成游戏体验。

适合 ADHD 用户 -- 手柄的物理反馈和游戏化机制有助于保持注意力集中。

## 功能

- **手柄按键映射** -- A/B/X/Y 对应四个答题按钮，扳机键撤回和重放音频
- **Combo 连击系统** -- 连续答对触发连击计数，达到阈值升级段位（ON FIRE / UNSTOPPABLE / GODLIKE）
- **震动反馈** -- 不同答题结果和连击段位对应不同震动模式（需手柄支持 CoreHaptics）
- **音效反馈** -- 答对、答错、翻牌等操作各有音效
- **视觉特效** -- 连击数字显示、段位提升动画、答错红屏闪烁

## 系统要求

- macOS（使用 Apple GameController 和 CoreHaptics 框架）
- Anki 2.1.45+
- Xbox 无线手柄（通过蓝牙连接到 Mac）

## 安装

1. 找到 Anki 插件目录：
   ```
   ~/Library/Application Support/Anki2/addons21/
   ```

2. 将本仓库克隆到插件目录：
   ```bash
   cd ~/Library/Application\ Support/Anki2/addons21/
   git clone https://github.com/mxzs123/anki-xbox-controller-mac.git xbox_controller
   ```

3. 重启 Anki，插件会自动安装所需的 Python 依赖（pyobjc 相关包）。

## 默认按键映射

| 手柄按键 | 动作 |
|---------|------|
| A | Again（重来） |
| B | Hard（困难） |
| X | Good（良好） |
| Y | Easy（简单） |
| 左扳机 | 重放音频 |
| 右扳机 | 撤回 |

复习时按答题键的行为：
- 卡片正面 → 翻牌显示答案
- 卡片背面 → 提交对应答案，进入下一张

## 配置

在 Anki 菜单栏选择 **Tools → Xbox Controller Settings** 打开配置界面。

也可以直接编辑 `config.json`：

```json
{
  "button_mapping": {
    "A": "answer_1",
    "B": "answer_2",
    "X": "answer_3",
    "Y": "answer_4",
    "left_trigger": "replay_audio",
    "right_trigger": "undo"
  },
  "sounds": {
    "enabled": true,
    "volume": 0.7
  },
  "haptics": {
    "enabled": true,
    "intensity_scale": 1.0
  },
  "combo": {
    "enabled": true,
    "visual_effects": true,
    "milestone_interval": 25,
    "streak_thresholds": [5, 10, 20]
  },
  "poll_interval_ms": 16
}
```

### 可用动作

| 动作名 | 说明 |
|-------|------|
| `answer_1` | Again（重来） |
| `answer_2` | Hard（困难） |
| `answer_3` | Good（良好） |
| `answer_4` | Easy（简单） |
| `replay_audio` | 重放当前卡片音频 |
| `undo` | 撤回上一步 |
| `show_answer` | 翻牌显示答案 |
| `none` | 无操作 |

### Combo 连击系统

连续答对（answer_2/3/4）会累积连击数。按 answer_1（Again）会断连击。

| 连击数 | 段位 | 效果 |
|-------|------|------|
| 5+ | ON FIRE | 金色连击数字，段位震动 |
| 10+ | UNSTOPPABLE | 橙色，更强震动 |
| 20+ | GODLIKE | 红色，最强震动 |

每复习 25 张卡片触发里程碑提示（可通过 `milestone_interval` 调整）。

## 手柄连接

1. 按住 Xbox 手柄的配对按钮进入配对模式
2. 在 Mac 的 **系统设置 → 蓝牙** 中连接手柄
3. 启动 Anki，插件会自动检测手柄并提示连接状态

## License

MIT
