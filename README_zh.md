# Eternal League of Networking (EMP)

[![Elin Together CI Deploy](https://github.com/ElinTogether/ElinTogether/actions/workflows/emp_ci.yml/badge.svg)](https://github.com/ElinTogether/ElinTogether/actions/workflows/emp_ci.yml) [![GitHub tag](https://img.shields.io/github/tag/ElinTogether/ElinTogether.svg)](https://GitHub.com/ElinTogether/ElinTogether/tags/) [![.NET SDK 11.0.x](https://img.shields.io/badge/11-green?logoColor=blue&label=dotnet%20SDK&labelColor=blue)](https://dotnet.microsoft.com/en-us/download/dotnet/11.0)

[English](README.md) | 中文 | [日本語](README_ja.md)

> **说明：** 下面的「关于本分支」介绍的是本分支（「独立」版）。再往下 `---` 之后是原项目的 README，描述的是原版 Mod。

## 关于本分支——「独立」版

这是 [Elin Together](https://github.com/ElinTogether/ElinTogether) 的修改版，只有一个目标：**在游戏中，主机玩家与其他玩家没有任何区别**。每个人都可以带着自己的同伴、任务、声望和金钱去想去的地方，而世界（剧情、据点、公会）保持共享。

原版 Mod 让整个队伍留在主机的地图上，并把其他玩家当作主机的队友。原作者不打算支持各自独立的地图；本分支就是尝试这件事的地方。Mod 本身的功劳全部属于原作者（见[致谢](#致谢)）。

> **状态：实验性。** 以下内容都是在一台电脑上、开两个游戏窗口测试的（游戏内自动测试，900 多项检查，见 `dev/`）。通过 Steam 在两台电脑之间**几乎没有玩过**：只有一个晚上，那次发现了测试没有发现的 bug；本版本的新功能还没有在两台电脑上试过。请先备份存档：`%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`

### 本分支增加的内容

| 功能 | 带来的变化 |
|---|---|
| 独立旅行 | 玩家可以不带主机去另一张地图。地图和在那里做过的事都会保留。离开期间进度会定期保存，聊天在所有地图之间都能用。 |
| 共享地图 | 玩家可以不经过主机，加入另一位玩家所在的地图。如果掌管地图的玩家离开，由另一位接手。 |
| 主机不拖人 | 主机切换地图时，留在原地的玩家会留在原地。 |
| 每位玩家各自的同伴 | 同伴跟随招募他的玩家、与他一起旅行，并且只计入该玩家的同伴上限。 |
| 每位玩家各自的出货 | 出货箱只有一个；出售所得归放入物品的玩家。 |
| 按各自节奏战斗 | 怪物按与它战斗的玩家的节奏行动，而不是主机的节奏。 |
| 每位玩家各自的随机任务 | 居民和告示板的任务属于接取的玩家，报酬、声望和业力也归他。任务跟着玩家走。 |
| 共享剧情 | 剧情任务在同一个日志里：任何人都可以开始、推进和完成。看过的对话、关键物品和债务也是共享的。 |
| 人人都能做地下城任务 | 不是主机的玩家也可以接取带有独立区域的任务，一个人完成，或与另一位玩家一起完成（见下一行）。 |
| 两人一起做地下城任务 | 一位玩家出发做任务时，另一位会看到「是／否」的询问框，问是否同行。区域是共用的，报酬归接取任务的人。两个方向都可以；如果任务是客机玩家接的，支持「讨伐」、采集和音乐类任务（防御类仍由一个人完成）。 |
| 玩家之间交易 | 点击另一位玩家 →「交易」：双方放入物品和金币，双方确认。 |
| 更安全的交易 | 单人游戏不让送出的东西会被拒绝；对方背包满了也会被拒绝；并说明原因。 |
| 角色选择 | 加入时，玩家可以在该世界中选择自己的一个角色，或新建一个。 |
| 每位玩家各自的业力和犯罪 | 谁犯的事，谁损失业力；卫兵只追捕那位玩家。 |
| 共享好感度和公会 | 居民的好感度对所有人都一样；加入公会对整个团队有效。 |
| 客机玩家和单人玩家一样玩 | 自 0.26.399 以来的几十项修正：死亡与遗嘱、神的礼物、陷阱、魔法书、治疗师、祝福、投资、符文、自动整理、原本会在主机上弹出的窗口、从一叠中取出的赠礼、已被骑乘的坐骑、用斧头劈原木、同时治疗同伴的祈祷、背包里会变质的食物……完整列表见 [`dev/DOCUMENTATION.md`](dev/DOCUMENTATION.md)（法语）。 |
| 「不要走远」按玩家各自设置 | 同伴的距离设置（「不要走远」「不要乱逛」）是它所属玩家的，而不是主机的。 |
| 客机玩家设置据点 | 研究和家园技能是向主机发出的真实请求（主机检查、只扣一次费，所有人都能看到结果）。政策、床、出售标签、笔记，以及据点、派系和传送器的名称，会双向同步给另一位玩家。 |
| Elin 版本不同也能连接 | 只有 Mod 的版本必须所有人一致。Elin 版本不同的玩家也能连接，并会收到警告。主机一侧的复选框（「Require the same Elin version」，默认不勾选）可以重新要求 Elin 版本也一致。 |

其中大部分是**主机一侧的复选框**（Esc → Mods → Elin Together → *Server Setting*）；取消勾选后，Mod 的行为与原版一致。两人一起做地下城任务，以及「客机玩家和单人玩家一样玩」的这些修正，没有复选框。

### 截图

| | |
|---|---|
| ![主机选项：每项新功能都是一个勾选框](assets/screens/host-options.jpg) | ![主机出发做任务：访客可选择同行](assets/screens/quest-ask-guest.jpg) |
| 主机选项：每项新功能都是一个勾选框 | 主机出发做任务：访客可选择同行 |
| ![两名玩家在同一个任务区域](assets/screens/quest-together.jpg) | ![访客出发做任务：主机也会收到同样的询问](assets/screens/quest-ask-host.jpg) |
| 两名玩家在同一个任务区域 | 访客出发做任务：主机也会收到同样的询问 |
| ![玩家之间的交易](assets/screens/trade.jpg) | ![每位玩家有自己的声望和业力](assets/screens/own-fame-karma.jpg) |
| 玩家之间的交易 | 每位玩家有自己的声望和业力 |
| ![加入时选择角色](assets/screens/character-choice.jpg) | ![据点：访客暂时不能设置的项目会被拒绝，且不扣费](assets/screens/base-host-only.jpg) |
| 加入时选择角色 | 据点：访客暂时不能设置的项目会被拒绝，且不扣费 |

### 已知限制

- 通过 Steam 在两台电脑之间几乎没有玩过（一个晚上）；本版本的新功能还没有。
- 世界的时间仍然跟随主机。
- 测试现在会在几处（治疗师、商店、女祭司）点击真实的游戏对话，但剧情不是：非主机玩家推进的剧情对话，以及接取地下城任务，是直接调用游戏代码来测试的。
- 两人一起做地下城任务：如果任务是客机玩家接的，只支持「讨伐」类。采集、音乐和防御类任务仍由客机玩家单独完成。
- 客机玩家对据点的设置：研究、据点（家园）技能、政策、床、出售标签、笔记、名称（据点、派系、传送器），与主机一样生效。尚未支持：女仆、居民的类型与待命、容器设置（仅在自己的画面上生效）。
- 客机玩家的建造模式（地板、墙、挖掘／砍伐标记）只在自己的画面上生效。目前据点需要由主机来建造。
- Elin 版本不同：只在本地连接中试过；通过 Steam 大厅则未实际玩过。
- 主机回到由客机玩家掌管的地图时，客机玩家的画面会重新加载（会先收到通知）。耗时还没有在两台电脑之间测量过。
- 交易：已装备的物品仍然不能交易（游戏会说明原因）；会检查背包是否已满。
- 有几项修正还没有在游戏中实际玩过：深水溺水、接待券、访客在客机玩家掌管的地图上的业力、背包整理、派系名称，还有其他一些（在提交信息里标注为「未实际玩过」）。
- 已知一些罕见的冲突，尚未修复（两位玩家在同一格建造、旅行后坐骑出现两份）。同一家商店里两人同时购买：后一位会被告知物品已经没有了（未实际玩过）。
- Mod 兼容性与原版相同：Mod 列表尽量精简，并让所有玩家保持一致。

完整列表和后续计划见 [`dev/DOCUMENTATION.md`](dev/DOCUMENTATION.md)（法语）。

### 安装本分支

需要 [YK Framework](https://steamcommunity.com/sharedfiles/filedetails/?id=3400020753)，以及 Elin 的 **Nightly** 分支（本分支基于 EA 23.352 构建）。**所有玩家必须使用同一个构建的本分支**；它不会连接创意工坊上的版本。玩家之间的 Elin 版本略有不同，也不再妨碍连接：会收到警告，主机可以勾选「Require the same Elin version」来要求版本一致。

从 [Releases 页面](https://github.com/devmarcpro/elin-together/releases)下载 `ElinTogether-independance.zip`，解压后运行 `Installer.bat`：它会把创意工坊版本切换成本版本（`Desinstaller.bat` 可以切换回去）。安装程序和随附说明是法语的。

开主机：通过 Steam 启动 Elin，加载一个已有领地的存档，然后 Esc → Mods → Elin Together。

本分支的问题请提交到[本仓库的 issues](https://github.com/devmarcpro/elin-together/issues)，并附上两位玩家的 `Player.log` 和 `ElinMP/Logs/Session_<日期>.log`（位于 `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`）。请不要把本分支的问题报告给原项目。

本分支的修改是在 AI 编程助手（Claude Code）的帮助下、由本分支的所有者指导完成的；每项修改都有对应的游戏内测试，写在提交信息里。本仓库不包含任何游戏文件，也不包含反编译出来的游戏代码。

---

以下是原项目的 README，描述的是原版 Mod，而不是本分支。

和朋友一起闯荡 [Elin](https://store.steampowered.com/app/2135150/Elin/) 的世界——一起建家、一起下地城、一起看红字报错弹窗。

经过数月的开发，本 Mod 目前进入公开测试阶段，如有 bug 请反馈。

## 游玩

需要安装 [YK Framework](https://steamcommunity.com/sharedfiles/filedetails/?id=3400020753)，并确保它排在 Elin Together 上面。

你可以通过 [Steam 创意工坊](https://steamcommunity.com/sharedfiles/filedetails/?id=3773298709) 或 [GitHub Releases](https://github.com/ElinTogether/ElinTogether/releases) 的自动构建版本安装此模组。

### 版本

创意工坊上的版本始终适配夜间版 Nightly 构建；如果遇到稳定版兼容问题，也可以去 GitHub 下载 Stable 版本。

### 开主机

- 通过 **Steam** 启动游戏，加载存档或开新档（推荐）
- 按 **Esc** → **Mods** → **Elin Together** 打开联机面板
- 在面板里开启主机
- 在面板里邀请玩家，或者直接用 Steam 好友列表

![Elin Together 面板](https://i.postimg.cc/vHqQLbV0/Pix-Pin-2026-07-28-09-25-19.png)

与好友联机时，建议使用最少的模组列表，并确保所有玩家保持一致。推荐使用 Steam 创意工坊合集来分享。

## FAQ

### 如何与其他玩家交流？

你可以按 `P` 键发送标记，或者按 `Return` 键聊天。

### 回合制的世界是怎么运作的？

每位玩家按自己的速度行动，主机世界会相应推进。玩家行动可以同时进行，不会互相阻塞。你也可以在设置中配置共享平均速度。

### 战斗怎么打？

在流畅的回合同步系统之上，你还可以在设置中开启经典回合制战斗，每位玩家决定行动后世界才会继续推进。

### 客机玩家无法切换地图

这是预期行为。只有主机玩家可以切换地图。

### 客机玩家无法推进某些任务

这是预期行为。作为客机玩家你可能会遇到错误。只有主机玩家才能实际推进任务。

### 客机玩家看到没法互动的幽灵物品

如果物品出现不同步，请尝试重新同步，主机或客机均可使用面板进行快速重新同步操作。

### 连接卡住、没反应、进不去……

重启游戏以清理 Steam 连接。

### 和 <某某> 模组兼容吗？

目前我们不提供模组兼容性方面的支持。遇到问题请尝试移除相关模组。

## 提交 Bug 和新功能

请使用[问题模板](https://github.com/ElinTogether/ElinTogether/issues/new/choose)提交。

发在创意工坊评论区的错误反馈不会处理。

模组制作相关讨论可以加入 Elin 模组讨论群 872068953。

## 构建

此项目需要设置如下环境变量:

`ElinGamePath`，指向 Elin 游戏安装的根目录。
```
ElinGamePath/
├─ BepInEx/
│  ├─ core/
│  │  ├─ *.dll
├─ Elin_Data/
│  ├─ Managed/
│  │  ├─ *.dll
```

`SteamContentPath`，指向 `steamapps/workshop/content` 目录，以便能够引用 `YKFramework.dll`。

此项目使用 [.NET SDK 11.0](https://dotnet.microsoft.com/en-us/download/dotnet/11.0) 进行编译。

克隆项目：
```ps
git clone https://github.com/ElinTogether/ElinTogether.git
cd ElinTogether
```

安装依赖：
```ps
dotnet restore ./ElinTogether --locked-mode
```

构建项目：
```ps
dotnet build ./ElinTogether -c Debug -o ./out --no-restore
```

## 贡献

请说明你的修改内容，并关联相关的 issue。如使用 AI 生成的代码，请对其负责，未经审查和测试的代码请勿提交。

## 致谢

- [DK](https://github.com/gottyduke) - 代码、框架
- [Redgeioz](https://github.com/Redgeioz) - 代码、框架
- [105gun](https://github.com/105gun) - 代码
- [Han](https://github.com/chuahan) - 大量测试
- [Omega](https://steamcommunity.com/profiles/76561198004587603) - 测试
- [InuiDame](https://github.com/InuiDame) - 测试
- [Drakeny](https://github.com/Drakeny) - 测试
- [Overlord](https://github.com/overlord-99) - 测试
- noa - 支持着项目和模组社区

---
<p align="center">MIT License, 2025-present</p>
