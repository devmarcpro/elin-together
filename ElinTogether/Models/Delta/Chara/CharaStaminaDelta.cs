using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

[MessagePackObject]
public class CharaStaminaDelta : ElinDelta
{
    [Key(0)]
    public required RemoteCard Chara { get; init; }

    [Key(1)]
    public required int Stamina { get; init; }

    internal override string? OnHostPermit(ElinNetHost host, Chara? sender)
    {
        return base.OnHostPermit(host, sender) ?? NotOwned(sender, Chara, "stamina of");
    }

    protected override void OnApply(ElinNetBase net)
    {
        if (Chara.Find() is not Chara { IsPC: false } chara) {
            return;
        }

        chara.stamina.value = Stamina;
    }
}