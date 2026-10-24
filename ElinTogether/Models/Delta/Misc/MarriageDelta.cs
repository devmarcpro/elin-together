using System.Collections.Generic;
using ElinTogether.Helper;
using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     Marriage (<see cref="SharedMarriages" />). From a guest: it asks to marry or wed the resident it talks to.
///     From the host: who that resident is married to now, with its LoveData and feat, or the whole list of spouses
/// </summary>
[MessagePackObject]
public class MarriageDelta : ElinDelta
{
    public enum Step : byte
    {
        State,
        Marry,
        Wed,
        Divorced,
        Refused,
    }

    [Key(0)]
    public Step Kind { get; init; }

    [Key(1)]
    public RemoteCard? Npc { get; init; }

    /// <summary>
    ///     The player character it is married to, 0 for none
    /// </summary>
    [Key(2)]
    public int Spouse { get; init; }

    [Key(3)]
    public int DateMarriage { get; init; }

    [Key(4)]
    public int DateWedding { get; init; }

    [Key(5)]
    public int UidZone { get; init; }

    [Key(6)]
    public string? NameZone { get; init; }

    [Key(7)]
    public int Feat { get; init; }

    /// <summary>
    ///     The player this happened to (its game counts the marriage or the divorce, or says it came too late)
    /// </summary>
    [Key(8)]
    public int Told { get; init; }

    /// <summary>
    ///     Resident -> spouse, all of them (a player joins)
    /// </summary>
    [Key(9)]
    public Dictionary<int, int>? Spouses { get; init; }

    internal override string? OnHostPermit(ElinNetHost host, Chara? sender)
    {
        return Kind is Step.Marry or Step.Wed ? NoCharacter(sender) : "not a request";
    }

    protected override void OnApply(ElinNetBase net)
    {
        if (net is not ElinNetHost host) {
            SharedMarriages.Learn(this);
            return;
        }

        if (!FromPeer || host.IsZoneSession || !SharedMarriages.Enabled || Kind is not (Step.Marry or Step.Wed) ||
            host.PlayerChara(OriginPeer) is not { } sender || Npc is null ||
            (Npc.Find() as Chara ?? game.cards.globalCharas.Find(Npc.Uid)) is not { } npc) {
            return;
        }

        if (Kind == Step.Marry) {
            SharedMarriages.MarryFor(host, OriginPeer, sender, npc);
        } else {
            SharedMarriages.WedFor(host, sender, npc);
        }
    }
}
