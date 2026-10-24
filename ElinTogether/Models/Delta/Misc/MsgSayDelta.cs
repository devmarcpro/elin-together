using System.Collections.Generic;
using ElinTogether.Net;
using MessagePack;
using UnityEngine;

namespace ElinTogether.Models;

[MessagePackObject]
public class MsgSayDelta : ElinDelta
{
    [Key(1)]
    public required string Text { get; init; }

    [Key(2)]
    public required float R { get; init; }

    [Key(3)]
    public required float G { get; init; }

    [Key(4)]
    public required float B { get; init; }

    [Key(5)]
    public required float A { get; init; }

    /// <summary>
    ///     A line a player typed (not an NPC or game line); only these go global, see GlobalChat
    /// </summary>
    [Key(6)]
    public bool Chat { get; init; }

    /// <summary>
    ///     Identifies a chat line so that a copy reaching a player twice (the map's relay and the global one) is
    ///     shown once
    /// </summary>
    [Key(7)]
    public int ChatId { get; init; }

    private static readonly Queue<int> RecentIds = new();

    /// <summary>
    ///     False when this chat id was already seen
    /// </summary>
    internal static bool Remember(int id)
    {
        if (RecentIds.Contains(id)) {
            return false;
        }

        RecentIds.Enqueue(id);
        while (RecentIds.Count > 64) {
            RecentIds.Dequeue();
        }

        return true;
    }

    protected override void OnApply(ElinNetBase net)
    {
        if (Chat && ChatId != 0 && !Remember(ChatId)) {
            return;
        }

        if (net is ElinNetHost host) {
            // relay to every connected player, including those travelling alone
            // (they are not in CurrentPlayers while away). Global chat off: player chat only to the players
            // that are on a map (not away)
            if (Chat && !NetSession.Instance.Rules.GlobalChat) {
                host.SendDeltaToMapPeers(OriginPeer, this);
            } else {
                host.SendDeltaToAllExcept(OriginPeer, this);
            }

            // a guest holding its own map is a host for the players there: its chat goes up to the real host,
            // which tells everyone (the players here get it from there too, the id keeps them from reading it twice)
            if (Chat && host.IsZoneSession && NetSession.Instance.Rules.GlobalChat &&
                NetSession.Instance.Transport is ElinNetClient up) {
                up.SendChatWhileAway(this);
            }
        }

        Msg.SetColor(new Color {
            r = R,
            g = G,
            b = B,
            a = A,
        });
        Msg.Say(Text);
    }
}