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

        Client.DepotPath = config.Bind(
            "Client",
            "DepotPath",
            "",
            "Folder of the save depot: a folder every player of the group can reach (shared or synced), which keeps the world. Empty: no depot\n" +
            "The first player takes the world from it and hosts, every save goes back to it, the next player can take over\n" +
            "Also the address of Elin Together Server (host:55557), or a private GitHub repository: github:owner/repository\n" +
            "存档仓库文件夹：小组所有玩家都能访问的文件夹（共享或同步），用于保存世界。留空：不使用");

        Client.DepotPassword = config.Bind(
            "Client",
            "DepotPassword",
            "",
            "Password of the save depot, when it is Elin Together Server and one was set there\n" +
            "For a GitHub depot: the access key (fine-grained token, this repository only, Contents: read and write). Never share this file");

        Client.ServerAddress = config.Bind(
            "Client",
            "ServerAddress",
            "",
            "Address of the server joined last with \"Join by address\", as host:port (the port is 55556)\n" +
            "上次通过“按地址加入”连接的服务器地址，格式为 主机:端口（端口为 55556）");

        Client.FetchMods = config.Bind(
            "Client",
            "FetchMods",
            true,
            "When the game joined (or the world taken from the depot) has Workshop mods that are not loaded here, download them without subscribing,\n" +
            "restart Elin with exactly the mods of that game for one session, and come back to the game by itself\n" +
            "Your own mod list is back at the next start. Untick it to keep your own mods: you are then only told which mods differ\n" +
            "These mods are chosen by the host (or by the modlist.txt of the depot) and their code runs on this PC: only with people you trust\n" +
            "这些模组由主机（或仓库的 modlist.txt）决定，其代码会在本机运行：仅与你信任的人一起使用\n" +
            "加入的游戏（或从仓库取得的世界）有本机未加载的创意工坊模组时：不订阅直接下载，以该游戏的模组重启 Elin 一次并自动回到游戏；下次启动恢复你自己的模组列表。取消勾选则保留自己的模组，只提示差异");

        Client.KeepMods = config.Bind(
            "Client",
            "KeepMods",
            false,
            "Keep the mods of the game you join: your Steam account subscribes to them on the Workshop and they stay on in your own mod list\n" +
            "Elin still restarts once, the first time. After that, joining the same game again needs no restart, even after closing Elin\n" +
            "Off: they are fetched without subscribing and your own list is back at each start, so Elin restarts at each first join\n" +
            "To undo: unsubscribe from them on the Workshop, or switch them off in the Mod Viewer. Only with \"Fetch the mods of the game by itself\"\n" +
            "保留所加入游戏的模组：你的 Steam 账号会在创意工坊订阅它们，并在你自己的模组列表中保持启用。第一次仍会重启一次，之后再次加入同一游戏无需重启。关闭时：不订阅直接获取，每次启动后第一次加入都会重启");

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

        Server.SameGameVersion = config.Bind(
            "Server",
            "SameGameVersion",
            false,
            "Refuse players whose version of Elin is not the host's\n" +
            "Off: they are let in and both are told; the same version of the mod is always required\n" +
            "拒绝游戏版本与主机不同的玩家");

        Server.PublishMods = config.Bind(
            "Server",
            "PublishMods",
            true,
            "The list of the mods of the game is shown to the players before they join (Steam lobby) and sent when they do\n" +
            "It is the list of the world when it came from a depot (modlist.txt), else the mods of the host\n" +
            "A player who is refused, or who takes the world, is told which mods differ. Otherwise nothing is said\n" +
            "游戏的模组列表会在玩家加入前显示（Steam 大厅）并在加入时发送；世界来自仓库时使用仓库的列表（modlist.txt），否则使用主机的模组。被拒绝或取得世界的玩家会被告知哪些模组不同");

        Server.PlayerCombatTime = config.Bind(
            "Server",
            "PlayerCombatTime",
            true,
            "Combat runs on each player's own time: what fights a player only acts when that player takes a turn\n" +
            "Nobody waits for the others. Takes over the turn-based combat mode when both are on\n" +
            "战斗按各玩家自己的时间进行：与某位玩家战斗的单位只在该玩家行动时行动，同时开启时优先于回合制战斗");

        Server.PlayerClock = config.Bind(
            "Server",
            "PlayerClock",
            true,
            "Every player walks and acts on the clock of its own game, as the host does\n" +
            "Otherwise a guest's steps follow the host's game time as it arrives over the network, which makes them uneven\n" +
            "Only with combat on each player's time\n" +
            "每位玩家按自己游戏的时钟移动和行动，与主机一样；否则客机的步伐取决于经网络传来的主机时间，会不均匀。需要开启“战斗按各玩家时间进行”");

        Server.PlayerStepPace = config.Bind(
            "Server",
            "PlayerStepPace",
            true,
            "Every player walks and acts at the pace of a solo game, whatever the speed of the other players\n" +
            "Otherwise the length of a step depends on the gap between the fastest and the slowest player\n" +
            "Speed still counts in a fight. Only with combat on each player's time\n" +
            "每位玩家按单人游戏的节奏移动和行动，不受其他玩家速度影响；否则每一步的时长取决于最快与最慢玩家的差距。战斗中速度仍然有效。需要开启“战斗按各玩家时间进行”");

        Server.SharedWorldTime = config.Bind(
            "Server",
            "SharedWorldTime",
            true,
            "One date for the whole world: time passed by a player alone on another map counts for everyone, the most advanced date is the world's\n" +
            "Otherwise only the host's date counts, and a player coming back from a map of its own jumps to it\n" +
            "整个世界共用一个日期：独自在其他地图的玩家所经过的时间对所有人都有效，最靠前的日期就是世界的日期；否则只以主机的日期为准");

        Server.WorldKeeper = config.Bind(
            "Server",
            "WorldKeeper",
            true,
            "What time does to the world (weather, expired quests, taxes, salaries, letters) is done once, by one game, the same for everyone\n" +
            "Otherwise every player holding a map runs it too in its own copy: a quest expires twice, each copy has its own weather\n" +
            "时间对世界的影响（天气、任务过期、税金、工资、信件）只由一个游戏处理一次，所有人相同；否则每个持有地图的玩家也会在自己的副本中各自处理");

        Server.PlayerKill = config.Bind(
            "Server",
            "PlayerKill",
            false,
            "A player (or its companions) can kill another player's character\n" +
            "Off: a strike that would kill it leaves it at 0 hit points\n" +
            "玩家（及其同伴）可以杀死其他玩家的角色；关闭时，致命一击只会让对方的生命值降为 0");

        Server.Duels = config.Bind(
            "Server",
            "Duels",
            true,
            "A player can challenge another player to a duel from the menu on its character: nobody dies, both are healed at the end, nothing is lost\n" +
            "Potions, arrows and charges used during the duel stay spent\n" +
            "玩家可以通过对方角色的菜单发起决斗：不会有人死亡，结束时双方恢复，没有任何损失；决斗中使用的药水、箭矢和充能不会返还");

        Server.GuestBuild = config.Bind(
            "Server",
            "GuestBuild",
            true,
            "The other players may use the build mode of the base (floors, walls, furniture, mining, cutting): the game of the host builds for them, they pay\n" +
            "Otherwise only the host builds\n" +
            "其他玩家可以使用据点的建造模式（地板、墙、家具、挖掘、砍伐）：由主机的游戏代为建造，费用由该玩家支付；否则只有主机可以建造");

        Server.HostManagesBase = config.Bind(
            "Server",
            "HostManagesBase",
            false,
            "Only the host manages the base: what the other players ask of it (research, hearth skills, policies, names, settings, residents, build mode) is refused\n" +
            "Otherwise every player manages the base as the host does (leaving the base for good stays the host's)\n" +
            "只有主机可以管理据点：其他玩家对据点的操作（研究、炉灶技能、政策、命名、设置、居民、建造模式）会被拒绝；否则每位玩家都可像主机一样管理据点（永久放弃据点仍只有主机可以）");

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

        Server.PlayerTrade = config.Bind(
            "Server",
            "PlayerTrade",
            true,
            "Players next to each other can trade items and gold through a window both confirm\n" +
            "Otherwise the game's own menu opens the other player's bag, as for an ally\n" +
            "相邻的玩家可以通过双方确认的窗口交换物品和金币");

        // not the "ChooseCharacter" key of earlier versions: every settings file already written holds it as true,
        // and a player who comes back is no longer asked at every connection
        Server.ChooseCharacter = config.Bind(
            "Server",
            "AskCharacter",
            false,
            "Every joining player is asked which of its characters in this world to play, or to make a new one\n" +
            "Otherwise it gets the character it played last, without a question\n" +
            "每位加入的玩家都会被询问使用自己在这个世界的哪个角色或新建角色，否则直接使用上次的角色");

        Server.AutoReconnect = config.Bind(
            "Server",
            "AutoReconnect",
            true,
            "A player who loses the connection joins the same game again by itself, every 5 seconds for 3 minutes\n" +
            "Not after leaving, being kicked or being refused. Otherwise it is left on the title screen\n" +
            "掉线的玩家会自动重新加入同一个游戏（每 5 秒一次，持续 3 分钟）；主动离开、被踢出或被拒绝时不会。关闭时回到标题画面");

        Server.AutoResync = config.Bind(
            "Server",
            "AutoResync",
            true,
            "A player whose copy of the map no longer matches the host's (a missing item or character) loads the map again by itself\n" +
            "At most once every 30 seconds, never during a fight, a task or with a menu open. Otherwise the difference is only written to the log\n" +
            "玩家的地图与主机不一致（缺少物品或角色）时，会自动重新载入地图；最多每 30 秒一次，战斗中、行动中或打开菜单时不会。关闭时只写入日志");

        Server.AutoSave = config.Bind(
            "Server",
            "AutoSave",
            true,
            "The world is saved by itself every 2 minutes while another player is in the game, and when the last one leaves\n" +
            "Every 5 minutes when a save takes more than half a second. Otherwise only when the host saves\n" +
            "有其他玩家在游戏中时，世界每 2 分钟自动保存一次，最后一位玩家离开时也会保存；保存超过半秒时改为每 5 分钟。关闭时只在主机保存时保存");

        Server.SharedTax = config.Bind(
            "Server",
            "SharedTax",
            true,
            "The monthly tax is computed on the highest fame among the connected players, not always on the host's\n" +
            "Otherwise on the host's fame, as the game does\n" +
            "每月税金按在线玩家中最高的名声计算，而不总是按主机的名声。关闭时按主机的名声计算（与原版相同）");

        Server.SoftRecall = config.Bind(
            "Server",
            "SoftRecall",
            false,
            "When the host walks onto the map a player holds alone, that player stays on its map without loading the whole world again; when that player walks into the map the host is on, it loads that one map only\n" +
            "New, off until it has been played more. Should anything not match, the world is loaded as before. Otherwise the world is loaded at each such meeting\n" +
            "主机走进某位玩家独自所在的地图时，该玩家留在原地图上，不再重新载入整个世界；该玩家走进主机所在的地图时，只载入那一张地图。新功能，默认关闭；如有任何不一致，仍会像以前一样载入世界。关闭时每次这样相遇都会重新载入世界");

        Server.WorldCopy = config.Bind(
            "Server",
            "WorldCopy",
            false,
            "After each save the game makes by itself, every other player's game keeps a copy of the world on its own disk, outside its saves\n" +
            "Sent in the background, a little at a time, only what changed. Otherwise the world is on the host's PC only\n" +
            "每次自动保存后，其他玩家的游戏会在自己的硬盘上保留一份世界副本（不在存档文件夹内）；在后台一点一点发送，只发送有变化的部分。关闭时世界只存在于主机的电脑上");

        Server.AutoHost = config.Bind(
            "Server",
            "AutoHost",
            true,
            "The game opens to the other players by itself when a world is loaded, without \"Start Server\"\n" +
            "Only friends can join, and the world needs a claimed land. Otherwise the host clicks \"Start Server\"\n" +
            "读取世界时游戏自动对其他玩家开放，无需点击“启动服务器”；只有好友可以加入，且世界需要已占领的土地。关闭时由主机点击“启动服务器”");

        Server.OwnSleep = config.Bind(
            "Server",
            "OwnSleep",
            true,
            "A player who goes to bed sleeps at once, for itself, without waiting for the others\n" +
            "The night only passes for the world when every player is asleep at the same time. Otherwise everyone waits for everyone\n" +
            "玩家上床后立刻为自己睡觉，不用等别人；只有所有玩家同时睡着时，世界才会过夜。关闭时所有人互相等待");

        Server.TimeJumpsTogether = config.Bind(
            "Server",
            "TimeJumpsTogether",
            true,
            "A step on the world map only moves the date of the world when all the players travel on it together\n" +
            "Otherwise the traveller pays its own turns and the date stays. Off: every step of anyone adds 3 hours for all\n" +
            "只有所有玩家一起在世界地图上旅行时，世界地图上的一步才会推进世界日期；否则旅行者只消耗自己的回合。关闭时任何人的每一步都会让所有人过 3 小时");

        Server.DumpSparesBelt = config.Bind(
            "Server",
            "DumpSparesBelt",
            true,
            "Auto-dump leaves what the player holds and what is in the tool belt, as it leaves the hotbar\n" +
            "Otherwise as in the game\n" +
            "自动收纳不会收走玩家手持的物品和工具腰带里的物品，就像它不会收走快捷栏一样。关闭时与原版相同");

        Server.ImportCharacter = config.Bind(
            "Server",
            "ImportCharacter",
            false,
            "A player joining can bring the character of one of its own saves: the character, its equipment, bag and gold, its fame and karma\n" +
            "Not its companions, base, quests or bank. Its save is only read, never changed\n" +
            "加入的玩家可以带来自己存档中的角色：角色本身、装备、背包、金币、声望和业力；不包括同伴、据点、任务和银行。存档只被读取，不会被修改");

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
            "Empty looks for Elin*/Elin.exe, made by dev/_tools/make_lab.py, in the folder the environment variable\n" +
            "ELINTOGETHER_LAB names, else in Documents/ElinMods/_lab");

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
        internal static ConfigEntry<string> DepotPath { get; set; } = null!;
        internal static ConfigEntry<string> DepotPassword { get; set; } = null!;
        internal static ConfigEntry<string> ServerAddress { get; set; } = null!;
        internal static ConfigEntry<bool> FetchMods { get; set; } = null!;
        internal static ConfigEntry<bool> KeepMods { get; set; } = null!;
    }

    internal static class Server
    {
        internal static ConfigEntry<string> SourceValidationSet { get; set; } = null!;
        internal static ConfigEntry<bool> StrictValidationMode { get; set; } = null!;
        internal static ConfigEntry<bool> SharedAverageSpeed { get; set; } = null!;
        internal static ConfigEntry<bool> TurnBasedCombat { get; set; } = null!;
        internal static ConfigEntry<bool> IndependentTravel { get; set; } = null!;
        internal static ConfigEntry<bool> SameGameVersion { get; set; } = null!;
        internal static ConfigEntry<bool> PublishMods { get; set; } = null!;
        internal static ConfigEntry<bool> PlayerShipping { get; set; } = null!;
        internal static ConfigEntry<bool> GuestBuild { get; set; } = null!;
        internal static ConfigEntry<bool> PlayerKill { get; set; } = null!;
        internal static ConfigEntry<bool> HostManagesBase { get; set; } = null!;
        internal static ConfigEntry<bool> Duels { get; set; } = null!;
        internal static ConfigEntry<bool> PersonalQuests { get; set; } = null!;
        internal static ConfigEntry<bool> ChooseCharacter { get; set; } = null!;
        internal static ConfigEntry<bool> AutoReconnect { get; set; } = null!;
        internal static ConfigEntry<bool> AutoResync { get; set; } = null!;
        internal static ConfigEntry<bool> AutoSave { get; set; } = null!;
        internal static ConfigEntry<bool> WorldCopy { get; set; } = null!;
        internal static ConfigEntry<bool> SharedTax { get; set; } = null!;
        internal static ConfigEntry<bool> SoftRecall { get; set; } = null!;
        internal static ConfigEntry<bool> AutoHost { get; set; } = null!;
        internal static ConfigEntry<bool> OwnSleep { get; set; } = null!;
        internal static ConfigEntry<bool> TimeJumpsTogether { get; set; } = null!;
        internal static ConfigEntry<bool> DumpSparesBelt { get; set; } = null!;
        internal static ConfigEntry<bool> ImportCharacter { get; set; } = null!;
        internal static ConfigEntry<bool> PlayerTrade { get; set; } = null!;
        internal static ConfigEntry<bool> PlayerCombatTime { get; set; } = null!;
        internal static ConfigEntry<bool> PlayerClock { get; set; } = null!;
        internal static ConfigEntry<bool> PlayerStepPace { get; set; } = null!;
        internal static ConfigEntry<bool> SharedWorldTime { get; set; } = null!;
        internal static ConfigEntry<bool> WorldKeeper { get; set; } = null!;
        internal static ConfigEntry<int> TravelCheckpointSeconds { get; set; } = null!;
    }
}