using System;
using System.Collections.Generic;
using ElinTogether.Helper;
using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

[HarmonyPatch(typeof(Card), nameof(Card.AddThing), typeof(Thing), typeof(bool), typeof(int), typeof(int))]
internal static class CardAddThingEvent
{
    private static readonly List<Thing> _pendingAbilityFakeCards = [];

    internal static bool AbilityLayoutDirty;

    internal static void FlushPendingAbilityFakeCard()
    {
        if (_pendingAbilityFakeCards.Count == 0 && !AbilityLayoutDirty) {
            return;
        }

        if (NetSession.Instance.Connection is ElinNetClient client) {
            foreach (var ab in _pendingAbilityFakeCards) {
                if (ab.isDestroyed || string.IsNullOrEmpty(ab.c_idAbility) || ab.GetRootCard() != EClass.pc) {
                    continue;
                }

                CardCache.UndoDestroy(ab);
                AbilityLayoutDirty = true;
            }

            if (AbilityLayoutDirty) {
                var layout = CollectLayout();
                EmpLog.Debug("Reporting ability layout, {LayoutCount} entries", layout.Count);

                client.Delta.AddRemote(new InvPlaceAbilityDelta {
                    Layout = layout,
                });
            }
        }

        AbilityLayoutDirty = false;
        _pendingAbilityFakeCards.Clear();
    }

    internal static List<InvPlaceAbilityDelta.AbilityTokenSlot> CollectLayout()
    {
        var layout = new List<InvPlaceAbilityDelta.AbilityTokenSlot>();
        foreach (var token in EClass.pc.things) {
            if (token is { trait: TraitAbility, isDestroyed: false } && !string.IsNullOrEmpty(token.c_idAbility)) {
                layout.Add(new() {
                    Alias = token.c_idAbility,
                    InvX = token.invX,
                    InvY = token.invY,
                });
            }
        }

        return layout;
    }

    [HarmonyPrefix]
    internal static bool OnCardAddThing(Card __instance, Thing t, bool tryStack, int destInvX, int destInvY)
    {
        // shipping box: tagged with the player shipping it; travelling, the goods go to the real host
        var shipper = 0;
        if (!ElinDelta.IsRemoteStateLanding && ShippingHelper.IsShippingBox(__instance)) {
            shipper = ShippingHelper.Enabled ? ShippingHelper.ShipperOverride ?? EClass.pc.uid : 0;
            if (ShippingHelper.ShipperOverride is null && NetSession.Instance.Connection is not ElinNetClient &&
                NetSession.Instance.Transport is ElinNetClient away && away.ForwardShippingDeposit(t, shipper)) {
                return false;
            }

            t.SetInt(ShippingHelper.ShipperKey, shipper);
        }

        // the bank and the delivery box: travelling, they are empty copies here, what goes in is sent to the
        // real ones instead of being lost with the copy
        if (!ElinDelta.IsRemoteStateLanding && ShippingHelper.OtherWorldBox(__instance) is var box and not 0 &&
            NetSession.Instance.Connection is not ElinNetClient &&
            NetSession.Instance.Transport is ElinNetClient travelling && travelling.ForwardShippingDeposit(t, 0, box)) {
            return false;
        }

        if (NetSession.Instance.Connection is not { } connection || ElinDelta.IsRemoteStateLanding) {
            if (RemoteCraft.ProductReceiver is not null) {
                EmpLog.Warning("Suppressed add-thing of {Uid} during remote craft, IsApplying guard hit",
                    t.uid);
            }

            return true;
        }

        if (__instance.GetBool("emp_creating")) {
            return true;
        }

        // ability fake card
        if (t.trait is TraitAbility) {
            if (connection.IsClient && __instance.IsPC && PendingUid.IsPending(t.uid)) {
                _pendingAbilityFakeCards.Add(t);
            }

            return true;
        }

        // client pending uid
        if (connection.IsClient && (PendingUid.IsPending(t.uid) || PendingUid.IsPending(__instance.uid))) {
            return true;
        }

        if (!CardCache.Contains(__instance) && !CardCache.TryAdopt(__instance)) {
            if (connection.IsHost) {
                if (!ZoneActivateEvent.IsHappening) {
                    EmpLog.Verbose("Skipping add-thing sync of {Uid} into uncached parent {ParentUid}",
                        t.uid, __instance.uid);
                }
                return true;
            }

            EmpLog.Warning("Suppressed add-thing of {Uid} into uncached parent {ParentUid}",
                t.uid, __instance.uid);
            return false;
        }

        connection.Delta.AddRemote(new CardAddThingDelta {
            Thing = t,
            Parent = __instance,
            TryStack = tryStack,
            DestInvX = destInvX,
            DestInvY = destInvY,
            Shipper = shipper,
        });

        return true;
    }

    extension(Card card)
    {
        [HarmonyReversePatch(HarmonyReversePatchType.Snapshot)]
        internal Thing Stub_AddThing(Thing thing, bool tryStack, int destInvX, int destInvY)
        {
            throw new NotImplementedException("Card.AddThing");
        }
    }
}