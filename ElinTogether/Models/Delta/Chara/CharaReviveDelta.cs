using System;
using System.Linq;
using ElinTogether.Elements;
using ElinTogether.Helper;
using ElinTogether.Net;
using ElinTogether.Patches;
using MessagePack;

namespace ElinTogether.Models;

[MessagePackObject]
public class CharaReviveDelta : ElinDelta
{
    [Key(0)]
    public required RemoteCard Owner { get; init; }

    [Key(1)]
    public required string? LastWords { get; init; }

    [Key(2)]
    public Position? Pos { get; set; }

    /// <summary>
    ///     The death penalty of a player alone was applied by the game that simulates the map
    /// </summary>
    [Key(3)]
    public bool Penalty { get; set; }

    protected override void OnApply(ElinNetBase net)
    {
        if (Owner.Find() is not Chara chara) {
            return;
        }

        if (net is ElinNetHost host) {
            // only the game that simulates the map says so
            Penalty = false;

            // duplicate
            if (!chara.isDead) {
                Pos = chara.pos;
                host.Delta.AddRemote(this);
                return;
            }

            Point point;
            if (Pos is { IsInActiveMapBounds: true } requested) {
                point = requested;
            } else if (chara.IsInActiveMap) {
                point = chara.pos.Copy();
            } else {
                point = pc.pos.GetNearestPoint() ?? pc.pos.Copy();
            }

            if (!chara.pos.IsValid) {
                chara.pos.Set(point.x, point.z);
            }

            chara.Revive(point, true);

            // a player who dies here pays what one playing alone pays, by the same rules: after day 90, unless
            // its will spares it, a share of its gold falls where it stands. Once, here; the experience of its
            // attributes is its own game's to take (below). Council decision of 2026-10-04, see MODLOG
            if (chara.IsRemotePlayer && (player.stats.days > 90 || game.principal.disableDeathPenaltyProtection) &&
                !(chara.things.Find("letter_will") is not null && rnd(10) == 0)) {
                Penalty = true;
                if (chara.GetCurrency() is var gold and > 0) {
                    var lost = Math.Max(1, gold / 3 + rnd(gold / 3 + 1));
                    using var simulate = Simulate();
                    using (MsgRelayContext.RedirectTo(chara)) {
                        Msg.Say("panaltyMoney", chara, Lang._currency(lost));
                    }

                    chara.ModCurrency(-lost);
                    _zone.AddCard(ThingGen.CreateCurrency(lost), chara.pos);
                }
            }

            using (Simulate()) {
                chara.MakeGrave(LastWords);
            }

            // Zone.AddCard during Revive
            if (chara.IsActiveRemoteChara) {
                chara.SetAI(GoalRemote.Default);
            }

            Pos = point;
            host.Delta.AddRemote(this);
        } else {
            // duplicate
            if (chara.isDead) {
                if (Pos is { IsInActiveMapBounds: true } pos) {
                    if (!chara.pos.IsValid) {
                        chara.pos.Set(pos.X, pos.Z);
                    }

                    chara.Revive(pos, true);
                } else {
                    chara.Revive(msg: true);
                }
            }

            // recursion
            if (chara.IsPC) {
                player.deathDialog = false;

                // the gold was taken where the map is simulated; the experience of its attributes is its own
                if (Penalty) {
                    using var _ = Simulate();
                    foreach (var element in chara.elements.dict.Values.ToArray()) {
                        if (rnd(5) == 0 && element.IsMainAttribute) {
                            chara.elements.ModExp(element.id, -500f);
                        }
                    }
                }
            }
        }

        EmpLog.Debug("Revive chara {Uid} at {@Pos}",
            chara.uid, Pos);

        // add back to party
        if (chara is { c_wasInPcParty: true, IsPCParty: false }) {
            pc.party.AddMemeber(chara);
        }
    }
}