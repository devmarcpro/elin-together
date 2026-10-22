using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     The title of "the player" (its alias, chosen at the start or by a scroll) is kept on the game's Player: a guest
///     plays on a copy of the host's world and had the host's title, and lost its own at the next copy. Each guest's
///     is kept on its character in the host's world, and put back on its Player when it joins
/// </summary>
[MessagePackObject]
public class PlayerTitleDelta : ElinDelta
{
    public const string TitleKey = "emp_title";

    private static string? _sent;
    private static ElinNetClient? _to;

    [Key(0)]
    public required string Title { get; init; }

    /// <summary>
    ///     Joining: this player's own title, not the host's (the game's first one for a player that never had one here)
    /// </summary>
    internal static void Carry(Chara chara)
    {
        EClass.player.title = chara.GetStr(TitleKey) is { Length: > 0 } title ? title : "master".lang();
        _sent = EClass.player.title;
        _to = NetSession.Instance.Connection as ElinNetClient;
    }

    internal static void Update()
    {
        if (NetSession.Instance.Connection is not ElinNetClient client || EClass.player?.title is not { } title) {
            return;
        }

        if (_to != client) {
            // (the first word of a new connection: what the guest has now)
            _to = client;
            _sent = null;
        }

        if (title != _sent) {
            _sent = title;
            client.Delta.AddRemote(new PlayerTitleDelta { Title = title });
        }
    }

    protected override void OnApply(ElinNetBase net)
    {
        if (net is ElinNetHost host && host.ActiveRemoteCharas.TryGetValue(OriginPeer, out var chara)) {
            chara.SetStr(TitleKey, Title is { Length: > 60 } ? Title[..60] : Title ?? "");
        }
    }
}
