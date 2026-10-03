using System;
using System.Linq;
using ElinTogether.Elements;
using ElinTogether.Net;
using HarmonyLib;
using UnityEngine;

namespace ElinTogether.Patches;

[HarmonyPatch(typeof(Game), nameof(Game.OnUpdate))]
internal class GameSynchronizationContext : SynchronizationContext
{
    private const float MaxGameDeltaBuffer = 0.3f;

    [HarmonyPrefix]
    internal static void OnGameOnUpdate()
    {
        switch (NetSession.Instance.Connection) {
            // its own turns on its own clock, as the host's: fed by the network, the host's game time comes in
            // lumps (none, one or two a frame, in bursts over the Internet) and every step waited for it, while
            // the sprite and the camera glide on the local clock
            case ElinNetClient when NetSession.Instance.Rules.OwnClock:
                GameDelta = 0f;
                break;
            // apply game delta as clients
            case ElinNetClient:
                var buffered = Mathf.Min(GameDelta, MaxGameDeltaBuffer);
                Core.gameDelta = buffered;
                GameDelta = EMono.scene.paused ? buffered : 0f;
                break;
            // allow remote players to trigger turbo
            case ElinNetHost host when !EMono.scene.paused:
                if (ShouldRemoteTurbo(host)) {
                    ActionMode.Adv.SetTurbo();
                }

                break;
            default:
                RefSpeed = pc.Speed;
                return;
        }

        if (NetSession.Instance.CurrentPlayers.All(n => n.Speed == 0)) {
            RefSpeed = pc.Speed;
            return;
        }

        if (NetSession.Instance.Rules.UseSharedSpeed) {
            RefSpeed = NetSession.Instance.SharedSpeed;
        } else {
            var min = (float)NetSession.Instance.CurrentPlayers.Where(n => n.Speed > 0).Min(n => n.Speed);
            var max = (float)NetSession.Instance.CurrentPlayers.Max(n => n.Speed);
            var mult = Math.Sqrt(max / min);

            mult = Math.Min(mult, 8f);

            RefSpeed = (int)(max / mult);
        }
    }

    private static bool ShouldRemoteTurbo(ElinNetHost host)
    {
        if (ActionModeCombat.Activated) {
            return false;
        }

        // a walk (or any act the host only knows as "busy") runs on its player's own clock: no need to speed
        // the host's world up for it, its own character included
        var ownClock = NetSession.Instance.Rules.OwnClock;

        foreach (var chara in host.ActiveRemoteCharas.Values) {
            if (chara.ai is GoalRemote { child: { status: AIAct.Status.Running } child } &&
                !(ownClock && child is NoGoal) &&
                (child.UseTurbo || child.Current is { UseTurbo: true })) {
                return true;
            }
        }

        return false;
    }
}