using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

[MessagePackObject]
public class CharaLevelDelta : ElinDelta
{
    internal override OverrideOrder Order => OverrideOrder.Last;

    [Key(0)]
    public required RemoteCard Owner { get; init; }

    [Key(1)]
    public required int Level { get; init; }

    [Key(2)]
    public required int Exp { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        if (net is not ElinNetHost host) {
            return;
        }

        if (Owner.Find() is not Chara { IsPC: false } chara) {
            return;
        }

        // (also while its player is away or arriving: the level gained there was refused here, and lost for
        // good when that player left before coming back)
        if (!host.IsOwnChara(OriginPeer, chara.uid)) {
            return;
        }

        if (Level < 1 || Exp < 0) {
            return;
        }

        chara.LV = Level;
        chara.exp = Exp;
    }
}