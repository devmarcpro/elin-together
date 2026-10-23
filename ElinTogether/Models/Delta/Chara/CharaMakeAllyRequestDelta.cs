using System.Linq;
using ElinTogether.Helper;
using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

[MessagePackObject]
public class CharaMakeAllyRequestDelta : ElinDelta
{
    // recruitItems
    private static readonly string[] _excluded = ["mamani2"];

    [Key(0)]
    public required RemoteCard? Owner { get; init; }

    [Key(1)]
    public required string? LocalCardId { get; init; }

    [Key(2)]
    public bool IsCopy { get; init; }

    [Key(3)]
    public bool ShowMsg { get; init; }

    /// <summary>
    ///     Already of the base, only asked to join the party (see PartyJoinEvent)
    /// </summary>
    [Key(4)]
    public bool JoinOnly { get; init; }

    /// <summary>
    ///     The character itself, when it only exists in the game of the player who recruits it: a slave or an
    ///     animal bought from a trader, a pet given by a dialog. Without it the host has nobody to recruit
    /// </summary>
    [Key(5)]
    public LZ4Bytes? Data { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        if (net is not ElinNetHost host) {
            return;
        }

        if (Owner is null) {
            ReplayLocalCopy(host);
            return;
        }

        if (Owner.Find() is not Chara { isDead: false } chara) {
            return;
        }

        if (JoinOnly) {
            JoinParty(host, chara);
            return;
        }

        // already ours: nothing was paid (a client's payment does not change its bag), nothing to give back
        if (chara.IsPCParty) {
            return;
        }

        host.ActiveRemoteCharas.TryGetValue(OriginPeer, out var recruiter);
        using var _ = Simulate();
        // never a player, never a boss; one the game does not invite for free costs what its dialog asks
        if (chara.IsPlayer || chara.c_bossType != BossType.none ||
            (!chara.trait.CanInvite && !PayRecruitCost(recruiter, chara.source))) {
            EmpLog.Warning("Refusing the recruit of {Id} {Uid} from peer {PeerIndex}", chara.id, chara.uid, OriginPeer);
            return;
        }

        // the companion follows the player who recruited it
        chara.SetCompanionOwner(recruiter);
        chara.MakeAlly(ShowMsg);
    }

    private void JoinParty(ElinNetHost host, Chara chara)
    {
        if (chara.party == pc.party || !host.ActiveRemoteCharas.TryGetValue(OriginPeer, out var recruiter)) {
            return;
        }

        using var _ = Simulate();
        // it follows the player who asked
        chara.SetCompanionOwner(recruiter);

        // called from the list of residents while it is somewhere else: it comes, as in the game
        if (chara.currentZone != _zone) {
            chara.MoveZone(_zone);
            chara.MoveImmediate(recruiter.pos.GetNearestPoint(false, false) ?? recruiter.pos);
        }

        pc.party.AddMemeber(chara, ShowMsg);
    }

    private void ReplayLocalCopy(ElinNetHost host)
    {
        if (LocalCardId is null) {
            return;
        }

        var receiver = host.ActiveRemoteCharas.TryGetValue(OriginPeer, pc);
        if (!_excluded.Contains(LocalCardId)) {
            AdoptLocal(host, receiver);
            return;
        }

        using var _ = Simulate();
        // Mamani's copy is what paying for Mamani gives (DramaCustomSequence "_invite")
        if (!PayRecruitCost(receiver == pc ? null : receiver, sources.charas.map["mamani"])) {
            EmpLog.Warning("Refusing {Id} from peer {PeerIndex}: not paid", LocalCardId, OriginPeer);
            return;
        }

        var copy = CharaGen.Create(LocalCardId);
        _zone.AddCard(copy, receiver.pos.GetNearestPoint());
        copy.isCopy = IsCopy;
        copy.SetCompanionOwner(receiver == pc ? null : receiver);
        copy.MakeAlly(ShowMsg);
    }

    /// <summary>
    ///     The character the player bought or was given comes to this world as it is, under uids of this world
    /// </summary>
    private void AdoptLocal(ElinNetHost net, Chara receiver)
    {
        if (Data is null) {
            return;
        }

        Chara chara;
        try {
            chara = Data.Decompress<Chara>();
        } catch (System.Exception ex) {
            EmpLog.Warning(ex, "Could not read the {Id} recruited by player {Peer}", LocalCardId, OriginPeer);
            return;
        }

        using var _ = Simulate();
        chara.currentZone = null;
        game.cards.AssignUIDRecursive(chara);
        chara.isCopy = IsCopy;
        chara.SetCompanionOwner(receiver == pc ? null : receiver);

        // nobody generated it here: the other games learn it whole, as a companion that comes back
        net.Delta.AddRemote(CardGenDelta.Create(chara));
        _zone.AddCard(chara, receiver.pos.GetNearestPoint(false, false) ?? receiver.pos);
        CardCache.Add(chara);
        CardCache.CacheContainer(chara.things);

        chara.MakeAlly(ShowMsg);
    }

    /// <summary>
    ///     The host takes the recruit cost from the recruiter's bag: in a client's game the dialog's ModNum changes
    ///     nothing (CardModNumEvent), so nothing else ever takes it
    /// </summary>
    private static bool PayRecruitCost(Chara? recruiter, SourceChara.Row source)
    {
        if (recruiter is null || source.recruitItems.IsEmpty()) {
            return false;
        }

        var reqs = source.recruitItems[0].Split('/');
        if (reqs.Length < 2) {
            return false;
        }

        var reqId = reqs[0];
        var reqNum = reqs[1].ToInt();
        if (recruiter.things.List(t => t.id == reqId && t.Num >= reqNum, true).FirstOrDefault() is not { } paid) {
            return false;
        }

        paid.ModNum(-reqNum);
        return true;
    }

    /// <summary>
    ///     A character made in this game only, that the host can only recruit if it receives it whole
    /// </summary>
    internal static bool IsLocalOnly(Chara chara)
    {
        return PendingUid.IsPending(chara.uid) && !_excluded.Contains(chara.id);
    }

    public static CharaMakeAllyRequestDelta Create(Chara chara, bool msg)
    {
        var pending = PendingUid.IsPending(chara.uid);
        return new() {
            Owner = pending ? null : chara,
            LocalCardId = pending ? chara.id : null,
            IsCopy = chara.isCopy, // keep sync with host
            ShowMsg = msg,
            Data = pending && !_excluded.Contains(chara.id) ? LZ4Bytes.Create(chara) : null,
        };
    }
}