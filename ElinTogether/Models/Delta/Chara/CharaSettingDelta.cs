using ElinTogether.Helper;
using System.Linq;
using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     What a player sets on a resident or a companion from its dialog menu (stay here, sleep beside me, shared
///     equipment, the "no ..." switches): values written by hand, read by the AI of the game that keeps the map.
///     The game where the dialog was held sends what changed when the dialog closes, every game takes it
/// </summary>
[MessagePackObject]
public class CharaSettingDelta : ElinDelta
{
    // shared equipment, sleep beside, no fidelity..., no sex, insult: the switches of DramaCustomSequence
    internal static readonly int[] Switches = [113, 123, 126, 119, 108];

    [Key(0)]
    public required RemoteCard Owner { get; init; }

    [Key(1)]
    public required bool NoMove { get; init; }

    /// <summary>
    ///     The tile it stays on (orgPos), null for none
    /// </summary>
    [Key(2)]
    public Position? Stays { get; init; }

    /// <summary>
    ///     The value of each of <see cref="Switches" />, in that order
    /// </summary>
    [Key(3)]
    public required int[] Values { get; init; }

    internal static int[] Read(Chara chara)
    {
        return [chara.noMove ? 1 : 0, chara.orgPos?.x ?? -1, chara.orgPos?.z ?? -1, ..Switches.Select(id => chara.GetInt(id))];
    }

    internal static void Emit(Chara chara)
    {
        if (IsApplying || NetSession.Instance.Connection is not { } connection) {
            return;
        }

        connection.Delta.AddRemote(new CharaSettingDelta {
            Owner = chara,
            NoMove = chara.noMove,
            Stays = chara.orgPos,
            Values = Switches.Select(id => chara.GetInt(id)).ToArray(),
        });
    }

    internal override string? OnHostPermit(ElinNetHost host, Chara? sender)
    {
        // a resident (no owner) is anyone's to talk to; another player's companion takes its orders from that player
        return NoCharacter(sender) ??
               (Owner.Find() is Chara chara && !UntaggedCompanion(chara) && CompanionHelper.OwnerOf(chara) is { } owner && owner.uid != sender!.uid
                   ? $"{chara.uid} follows {owner.uid}"
                   : null);
    }

    protected override void OnApply(ElinNetBase net)
    {
        // never a player's character: these are settings of the characters players give orders to
        if (Values.Length != Switches.Length || Owner.Find() is not Chara { IsPlayer: false } chara) {
            return;
        }

        if (net is ElinNetHost host) {
            host.SendDeltaToAllExcept(OriginPeer, this);
        }

        chara.noMove = NoMove;
        chara.orgPos = Stays is null ? null : new Point(Stays.X, Stays.Z);
        for (var i = 0; i < Switches.Length; i++) {
            chara.SetInt(Switches[i], Values[i]);
        }
    }
}
