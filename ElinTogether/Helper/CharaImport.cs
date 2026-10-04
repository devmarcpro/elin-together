using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Text;
using ElinTogether.Helper.Extensions;
using LZ4;
using Newtonsoft.Json;

namespace ElinTogether.Helper;

/// <summary>
///     Joining with the character of one of the player's own solo saves: read beside the running game, never
///     loaded and never written. Only the character travels (stats, feats, looks, equipment, bag, gold), with
///     its fame and karma; companions, mount, base, quests and bank stay in the solo save
/// </summary>
internal static class CharaImport
{
    internal const int MaxSaves = 8;

    /// <summary>
    ///     Card string kept on the copy at the host: which save it came from, one copy of each per player
    /// </summary>
    internal const string SourceKey = "emp_import";

    internal record Imported(Chara Chara, int Fame, int Karma, string Source);

    /// <summary>
    ///     The most recent local saves this game can read
    /// </summary>
    internal static List<GameIndex> Saves()
    {
        try {
            // the last ones written first: the date a save carries is the one of its world, a copy keeps it
            return GameIO.GetGameList(CorePath.RootSave)
                .Where(index => !index.isBackup && File.Exists(Path.Combine(index.path, "game.txt")) && Readable(index))
                .OrderByDescending(index => File.GetLastWriteTimeUtc(Path.Combine(index.path, "game.txt")))
                .Take(MaxSaves)
                .ToList();
        } catch (Exception ex) {
            EmpLog.Warning(ex, "Could not list the local saves");
            return [];
        }
    }

    private static bool Readable(GameIndex index)
    {
        try {
            return EClass.core.version.IsSaveCompatible(index.version);
        } catch {
            return false;
        }
    }

    internal static string Label(GameIndex index)
    {
        try {
            return $"{index.pcName} - {index.zoneName}, {index.RealDate} ({index.id})";
        } catch {
            // an index without its dates
            return $"{index.pcName} ({index.id})";
        }
    }

    /// <summary>
    ///     Reads the player character out of a save. GameIO.LoadGame without what makes it the current game:
    ///     the file is opened for reading only, and the statics a deserialized Game overwrites are put back
    /// </summary>
    internal static Imported? Read(GameIndex index)
    {
        var path = Path.Combine(index.path, "game.txt");
        var instance = Game.Instance;
        var fallback = new Dictionary<string, string>(ModUtil.fallbackTypes);
        try {
            foreach (var (type, other) in index.fallbackTypes) {
                ModUtil.fallbackTypes[type] = other;
            }

            var save = JsonConvert.DeserializeObject<Game>(ReadText(path), GameIO.jsReadGame);
            if (save?.player is null || save.cards.globalCharas.Find(save.player.uidChara) is not { } chara) {
                EmpLog.Warning("Save {Id} has no player character", index.id);
                return null;
            }

            Detach(chara);
            return new(chara, save.player.fame, save.player.karma, $"{index.id}/{save.player.uidChara}/{chara.Name}");
        } catch (Exception ex) {
            EmpLog.Warning(ex, "Could not read the character of save {Id}", index.id);
            return null;
        } finally {
            Game.Instance = instance;
            ModUtil.fallbackTypes.Clear();
            foreach (var (type, other) in fallback) {
                ModUtil.fallbackTypes[type] = other;
            }
        }
    }

    private static string ReadText(string path)
    {
        using var file = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite);
        if (!IO.IsCompressed(path)) {
            using var plain = new StreamReader(file, Encoding.UTF8);
            return plain.ReadToEnd();
        }

        using var lz4 = new LZ4Stream(file, CompressionMode.Decompress);
        using var reader = new StreamReader(lz4);
        return reader.ReadToEnd();
    }

    /// <summary>
    ///     Cuts what ties the character to its own world, so that only the character is sent: fields only, there
    ///     is no game around it here
    /// </summary>
    private static void Detach(Chara chara)
    {
        chara.party = null;
        chara.ride = null;
        chara.parasite = null;
        chara.host = null;
        chara.held = null;
        chara.quest = null;
        chara.enemy = null;
        chara.global = null;
        // currentZone and homeZone: uids of the solo world, another zone in the host's
        chara._cints[1] = 0;
        chara._cints[2] = 0;
        chara.c_uidMaster = 0;
    }

    /// <summary>
    ///     Host side: the copy becomes a character of this world, with uids of this world
    /// </summary>
    internal static void Adopt(Chara chara, string source)
    {
        var before = chara.uid;

        chara.SetBool(CINT.IsPC, false);
        chara.currentZone = null;
        chara.homeZone = null;

        // debts of the other world
        foreach (var bill in chara.things.Flatten().Where(t => t.trait is TraitBill).ToList()) {
            bill.Destroy();
        }

        EClass.game.cards.AssignUIDRecursive(chara);

        // what is bound to this character stays bound to it under its new uid
        foreach (var thing in chara.things.Flatten()) {
            if (thing.c_uidAttune == before) {
                thing.c_uidAttune = chara.uid;
            }
        }

        if (chara.isDead || chara.hp <= 0) {
            chara.isDead = false;
            chara.hp = chara.MaxHP;
        }

        chara.SetStr(SourceKey, source);
    }
}
