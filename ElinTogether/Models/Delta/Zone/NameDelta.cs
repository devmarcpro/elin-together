using ElinTogether.Net;
using ElinTogether.Patches;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     The name a player gives its base, or the faction: typed in a box of its own game, it only changed its own
///     copy. Seen where it changed (<see cref="NameWatch" />), told to the others
/// </summary>
[MessagePackObject]
public class NameDelta : ElinDelta
{
    public const byte OfZone = 0;
    public const byte OfFaction = 1;

    [Key(0)]
    public required byte Kind { get; init; }

    [Key(1)]
    public int ZoneUid { get; init; }

    [Key(2)]
    public string? Name { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        if (string.IsNullOrEmpty(Name)) {
            return;
        }

        if (net is ElinNetHost host) {
            if (!host.ActiveRemoteCharas.ContainsKey(OriginPeer) || host.IsAwayPeer(OriginPeer)) {
                return;
            }

            // only the host manages the base: the sender gets the name the host keeps, which puts its copy back
            if (NetSession.Instance.Rules.HostManagesBase && !host.IsZoneSession) {
                var kept = Kind == OfFaction ? EClass.Home?.name : (game.spatials.Find(ZoneUid) as Zone)?.name;
                if (!string.IsNullOrEmpty(kept)) {
                    host.SendDeltaTo(OriginPeer, new NameDelta { Kind = Kind, ZoneUid = ZoneUid, Name = kept });
                }

                return;
            }

            host.Delta.AddRemote(this);
        }

        if (Kind == OfFaction) {
            if (EClass.Home is { } home) {
                home.name = Name;
            }
        } else if (game.spatials.Find(ZoneUid) is Zone { IsPCFaction: true } zone) {
            zone.name = Name;
            zone.idPrefix = 0;
            WidgetDate.Refresh();
        }

        NameWatch.Accept();
    }
}
