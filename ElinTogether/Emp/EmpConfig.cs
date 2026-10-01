using BepInEx.Configuration;
using ReflexCLI.Attributes;
using UnityEngine;

namespace ElinTogether;

[ConsoleCommandClassCustomizer("emp")]
internal partial class EmpConfig
{
    internal static void Bind()
    {
        var config = EmpMod.Instance.Config;

        Policy.Verbose = config.Bind(
            "RuntimePolicy",
            "Verbose",
#if DEBUG || true
            // enabled for beta builds
            true,
#else
            false,
#endif
            "Verbose information that may be helpful(spamming) for debugging\n" +
            "Enabled for beta testing by default\n" +
            "Debug用的信息输出\n" +
            "Beta测试版默认启用\n" +
            "デバッグ用の詳細情報を出力(大量ログ発生の可能性あり)");

        Policy.Timeout = config.Bind(
            "RuntimePolicy",
            "Timeout",
            15f,
            new ConfigDescription(
                "Timeout in seconds for any requests\n" +
                "Retry attempts will not be made after timeout\n" +
                "网络请求的最大超时\n" +
                "超时后，将不会重新请求",
                new AcceptableValueRange<float>(1f, 60f)));

        Policy.Retries = config.Bind(
            "RuntimePolicy",
            "Retries",
            1,
            new ConfigDescription(
                "Retries attempts after a failed request\n" +
                "请求失败后的重试次数",
                new AcceptableValueRange<int>(0, 5)));

        Client.PingKeybind = config.Bind(
            "Client",
            "PingKeybind",
            KeyCode.P,
            "Keybind for pinging map\n" +
            "键盘键位用于标记一处地点");

        Server.SourceValidationSet = config.Bind(
            "Server",
            "SourceValidation",
            "",
            "Source validation sets.\n" +
            "  none (or empty): skip all validation\n" +
            "  sources: validate Elin source table checksums\n" +
            "  plugins: validate plugin DLL hashes\n" +
            "  files: validate configured file hashes\n" +
            "  all: enable all checks\n" +
            "Combinations: \"source,plugin\" \"plugin,\" etc.\n" +
            "File paths: append \":path1,path2\" after flags, e.g. \"file:Data/xxx.json\"\n" +
            "File must be the last set\n" +
            "源表校验类型组合：none=跳过 source=源表 plugin=插件DLL file=文件\n" +
            "file必须放置于最后");

        Server.StrictValidationMode = config.Bind(
            "Server",
            "StrictValidationMode",
            false,
            "Server & Client integrity validation mode.\n" +
            "Set to true to block any mismatching clients from joining\n" +
            "双端数据完整性校验模式\n" +
            "开启时禁止任何不匹配的客机加入");

        Server.SharedAverageSpeed = config.Bind(
            "Server",
            "SharedAverageSpeed",
            false,
            "Share an averaged speed for all players\n" +
            "Otherwise each player will have their own speed\n" +
            "所有玩家共享平均速度\n" +
            "否则所有人按各自速度行动");

        Server.TurnBasedCombat = config.Bind(
            "Server",
            "TurnBasedCombatMode",
            true,
            "Players take turns in combat\n" +
            "战斗中玩家轮流行动");

        Server.IndependentTravel = config.Bind(
            "Server",
            "IndependentTravel",
            true,
            "Clients may travel to other zones on their own\n" +
            "The zone is simulated by that client and sent back to the host when leaving\n" +
            "客机可以独自前往其他地图，由该客机模拟，离开时回传给主机");

        Server.PlayerCombatTime = config.Bind(
            "Server",
            "PlayerCombatTime",
            true,
            "Combat runs on each player's own time: what fights a player only acts when that player takes a turn\n" +
            "Nobody waits for the others. Takes over the turn-based combat mode when both are on\n" +
            "战斗按各玩家自己的时间进行：与某位玩家战斗的单位只在该玩家行动时行动，同时开启时优先于回合制战斗");

        Server.PlayerShipping = config.Bind(
            "Server",
            "PlayerShipping",
            true,
            "Every player is paid for the goods it puts in the shipping box, with its own shipping bonus\n" +
            "Otherwise the host gets everything\n" +
            "每位玩家各自获得自己放入出货箱物品的收入与出货奖励，否则全部归主机");

        Server.PersonalQuests = config.Bind(
            "Server",
            "PersonalQuests",
            true,
            "Random quests, fame and karma belong to the player who takes the quest, 5 quests each\n" +
            "Story quests stay shared. Otherwise there is one quest log and one fame for the whole group\n" +
            "随机任务、名声与业力归接任务的玩家所有，每人5个；主线任务仍然共享");

        Server.ChooseCharacter = config.Bind(
            "Server",
            "ChooseCharacter",
            true,
            "A player joining picks one of the characters it already has in this world, or makes a new one\n" +
            "Otherwise it always gets the character it played last\n" +
            "加入的玩家可以选择自己在这个世界已有的角色或新建角色，否则总是使用上次的角色");

        Server.TravelCheckpointSeconds = config.Bind(
            "Server",
            "TravelCheckpointSeconds",
            60,
            new ConfigDescription(
                "Seconds between two checkpoints of a client travelling alone (its zone and character)\n" +
                "If it disconnects, only what happened since the last checkpoint is lost. 0 disables\n" +
                "独自行动的客机每隔多少秒回传一次进度，断线时只丢失最后一次之后的内容。0 为关闭",
                new AcceptableValueRange<int>(0, 600)));

        Dev.Listener = config.Bind(
            "Dev",
            "Listener",
            false,
            "Open the localhost debug listener for scripts/mcp (Debug builds only)\n" +
            "It executes arbitrary C#, never enable on a machine you share\n" +
            "为 scripts/mcp 打开本机调试监听（仅 Debug 构建）\n" +
            "它会执行任意 C#，不要在共用机器上开启");

        Dev.Identity = config.Bind(
            "Dev",
            "Identity",
            0,
            new ConfigDescription(
                "Local udp test identity (Debug builds only), 0 uses the Steam account\n" +
                "Lets several game instances on one Steam account join a local session as different players\n" +
                "本地UDP测试身份（仅 Debug 构建），0 为使用 Steam 账号",
                new AcceptableValueRange<int>(0, 999)));

        Dev.BotLaunchers = config.Bind(
            "Dev",
            "BotLaunchers",
            "",
            "Game copies a bot player can be started from (Debug builds only), separated by ';'\n" +
            "Empty looks for Documents/ElinMods/_lab/Elin*/Elin.exe, made by _tools/make_lab.py");

        Dev.BotAllActions = config.Bind(
            "Dev",
            "BotAllActions",
            false,
            "Bot players also accept quests and sell through the shipping chest (Debug builds only)\n" +
            "Leave off on a world you care about");

        Reload();
    }

    internal static class Dev
    {
        internal static ConfigEntry<bool> Listener { get; set; } = null!;
        internal static ConfigEntry<int> Identity { get; set; } = null!;
        internal static ConfigEntry<string> BotLaunchers { get; set; } = null!;
        internal static ConfigEntry<bool> BotAllActions { get; set; } = null!;
    }

    internal static class Policy
    {
        internal static ConfigEntry<float> Timeout { get; set; } = null!;
        internal static ConfigEntry<int> Retries { get; set; } = null!;
        internal static ConfigEntry<bool> Verbose { get; set; } = null!;
    }

    internal static class Client
    {
        internal static ConfigEntry<KeyCode> PingKeybind { get; set; } = null!;
    }

    internal static class Server
    {
        internal static ConfigEntry<string> SourceValidationSet { get; set; } = null!;
        internal static ConfigEntry<bool> StrictValidationMode { get; set; } = null!;
        internal static ConfigEntry<bool> SharedAverageSpeed { get; set; } = null!;
        internal static ConfigEntry<bool> TurnBasedCombat { get; set; } = null!;
        internal static ConfigEntry<bool> IndependentTravel { get; set; } = null!;
        internal static ConfigEntry<bool> PlayerShipping { get; set; } = null!;
        internal static ConfigEntry<bool> PersonalQuests { get; set; } = null!;
        internal static ConfigEntry<bool> ChooseCharacter { get; set; } = null!;
        internal static ConfigEntry<bool> PlayerCombatTime { get; set; } = null!;
        internal static ConfigEntry<int> TravelCheckpointSeconds { get; set; } = null!;
    }
}