using System.Collections.Generic;
using ElinTogether.API.SourceValidation;
using ElinTogether.Net;
using ElinTogether.Patches;
using MessagePack;

namespace ElinTogether.Models;

[MessagePackObject]
public class CharaTaskCancelDelta : ElinDelta
{
    public const int ForceCancelCountRequired = 2;

    public static readonly Dictionary<int, int> LastCancelDelta = [];

    [Key(0)]
    public required RemoteCard Owner { get; init; }

    [Key(1)]
    public required int ActId { get; init; }

    internal const byte ReadFailed = 1;

    /// <summary>
    ///     Why it stops, when the game that stops it knows more than "stopped": 0 for nothing to add
    /// </summary>
    [Key(2)]
    public byte Reason { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        if (Owner.Find() is not Chara chara) {
            return;
        }

        var type = ActMappingValidator.Default.IdToActMapping[ActId];

        if (typeof(NoGoal).IsAssignableFrom(type)) {
            LastCancelDelta.Remove(Owner.Uid);
            return;
        }

        var ai = chara.ai.Current;
        while (ai is not null && ai.GetType() != type) {
            ai = ai.parent;
        }

        if (!LastCancelDelta.TryAdd(Owner.Uid, 1)) {
            LastCancelDelta[Owner.Uid]++;
        }

        if (ai is not { status: AIAct.Status.Running }) {
            if (ai is null) {
                LastCancelDelta.Remove(Owner.Uid);
                return;
            }

            if (LastCancelDelta.GetValueOrDefault(Owner.Uid) >= ForceCancelCountRequired) {
                EmpLog.Warning("Force cancelling possibly stuck act {ActId}, {ActType} on chara {Uid}",
                    ActId, type.Name, Owner.Uid);
            } else {
                return;
            }
        }

        // relay to clients
        if (net.IsHost) {
            net.Delta.AddRemote(this);
        }

        LastCancelDelta.Remove(Owner.Uid);

        // a reading is rolled in the reader's game only (TraitBaseSpellbookPatch): when it failed there, the book
        // loses its charge here, where the charges are kept. Once: the reading is stopped right below
        if (net is ElinNetHost host && Reason == ReadFailed && ai is AI_Read { target.trait: TraitBaseSpellbook book } &&
            host.ActiveRemoteCharas.TryGetValue(OriginPeer, out var sender) && sender == chara) {
            using var _ = Simulate();
            book.ModCharge(chara);
        }

        ai.Stub_Cancel();
    }
}