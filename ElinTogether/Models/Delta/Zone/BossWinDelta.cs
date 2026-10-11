using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     The boss of a zone fell. The game that simulated its death says so: it alone marked the dungeon
///     conquered, played the fanfare and gave fame to "the player". A guest who beat a boss alone in a dungeon
///     told nobody (the host's world still had the boss and an unconquered dungeon), and a player beside the one
///     whose game simulates saw the boss die like any monster. The world's part goes to every game, the
///     victory to every player who stands on that map
/// </summary>
[MessagePackObject]
public class BossWinDelta : ElinDelta
{
    [Key(0)]
    public required int ZoneUid { get; init; }

    [Key(1)]
    public required int TopZoneUid { get; init; }

    [Key(2)]
    public required bool Nefia { get; init; }

    [Key(3)]
    public required int DangerLv { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        if (net is ElinNetHost host) {
            host.SendDeltaToAllExcept(OriginPeer, this);
        }

        if (game.spatials.Find(ZoneUid) is not Zone zone) {
            return;
        }

        // (a game that played the death itself has no boss left there: it had its own fanfare)
        var hadBoss = zone.uidBoss != 0;
        zone.uidBoss = 0;
        if (Nefia && game.spatials.Find(TopZoneUid) is Zone top) {
            top.isConquered = true;
        }

        if (!hadBoss || _zone != zone) {
            return;
        }

        Msg.Say("boss_win", zone.Name);
        if (Nefia) {
            player.stats.nefiaBeaten++;
            SE.Play("Jingle/fanfare2");
            zone.SetBGM(114, refresh: true, 3f);
        }

        player.ModFame(rndHalf(30 + DangerLv * 2));
        player.ModKarma(5);
    }
}
