using ElinTogether.Helper;
using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     The gene machine used by a guest (n°8 of the hunt of 2026-10-05): the host, which runs the residents, opened the
///     guest's windows on its own screen and kept none of its choices. The guest chooses in its own game; the host only
///     does what the choice does: the resident lies down in the machine (<see cref="Gene" /> null), then the gene goes
///     into it. The end (the gene applied) is the host's own use, as for itself
/// </summary>
[MessagePackObject]
public class GeneMachineDelta : ElinDelta
{
    [Key(0)]
    public required RemoteCard Machine { get; init; }

    [Key(1)]
    public required RemoteCard Chara { get; init; }

    [Key(2)]
    public RemoteCard? Gene { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        if (Machine.Find() is not Thing { trait: TraitGeneMachine trait } machine || Chara.Find() is not global::Chara chara) {
            return;
        }

        if (net is not ElinNetHost host) {
            Mirror(machine, chara);
            return;
        }

        if (!host.ActiveRemoteCharas.TryGetValue(OriginPeer, out var sender) || !machine.IsInstalled || !machine.isOn ||
            chara.isDead || !chara.IsPCFaction) {
            return;
        }

        using (Simulate()) {
            if (Gene is null) {
                // the game's own list: a free machine, a resident of the base not already lying in one
                if (_zone.IsUserZone || trait.GetTarget() is not null || chara.GetCondition<ConSuspend>() is not null ||
                    chara.host is not null || chara.IsPC || chara.IsRemotePlayer || chara.memberType != FactionMemberType.Default) {
                    return;
                }

                // what the choice of the machine's list does (TraitGeneMachine.OnUse)
                if (chara.IsPCParty) {
                    pc.party.RemoveMember(chara);
                }

                if (!chara.pos.Equals(machine.pos)) {
                    chara.Teleport(machine.pos, silent: false, force: true);
                    chara.isRestrained = false;
                }

                chara.RemoveCondition<ConSleep>();
                if (chara.AddCondition<ConSuspend>(100, force: true) is ConSuspend suspend) {
                    suspend.uidMachine = machine.uid;
                }
            } else {
                // what putting the gene in does (InvOwnerGene._OnProcess, after its checks, made in the guest's game)
                if (Gene.Find() is not Thing { c_DNA: not null } gene || (gene.GetRootCard() != sender && gene.parent != chara) ||
                    chara.GetCondition<ConSuspend>() is not { HasGene: false } condition || condition.uidMachine != machine.uid) {
                    return;
                }

                chara.AddCard(gene);
                condition.gene = gene;
                condition.duration = gene.c_DNA.GetDurationHour();
                condition.dateFinish = world.date.GetRaw(condition.duration);
            }
        }

        // every game: the condition the others get carries no machine nor gene (CharaAddConditionDelta)
        host.Delta.AddRemote(this);
    }

    /// <summary>
    ///     A game that does not run the resident: which machine it lies in, which gene it takes (its machine's window
    ///     and progress read them)
    /// </summary>
    private void Mirror(Thing machine, global::Chara chara)
    {
        var condition = chara.GetCondition<ConSuspend>() ?? chara.AddCondition<ConSuspend>(100, force: true) as ConSuspend;
        if (condition is null) {
            return;
        }

        condition.uidMachine = machine.uid;
        if (Gene?.Find() is Thing { c_DNA: not null } gene) {
            condition.gene = gene;
            condition.duration = gene.c_DNA.GetDurationHour();
            condition.dateFinish = world.date.GetRaw(condition.duration);
        }
    }
}
