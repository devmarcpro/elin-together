using ElinTogether.Net;
using HarmonyLib;
using UnityEngine;

namespace ElinTogether.Patches;

[HarmonyPatch]
internal class GameSaveLoad
{
    [HarmonyPrefix]
    [HarmonyPatch(typeof(Game), nameof(Game.Save))]
    internal static bool OnSaveRemoteGame(ref bool __result)
    {
        // an away client reads as host but only holds a copy of the host world
        if (NetSession.Instance.IsHost && !NetSession.Instance.IsAway) {
            return true;
        }

        EmpLog.Debug("Blocked saving game as client");
        __result = true;

        // the game also saves by itself (changing map, sleeping): one line now and then, not one per save
        if (EClass.core.IsGameStarted && Time.realtimeSinceStartup - _saveNoticeAt > 60f) {
            _saveNoticeAt = Time.realtimeSinceStartup;
            Msg.Say("emp_ui_save_kept".lang());
        }

        return false;
    }

    private static float _saveNoticeAt = float.MinValue;

    [HarmonyPrefix]
    [HarmonyPatch(typeof(Game), nameof(Game.TryLoad))]
    internal static bool OnLoadRemoteGame()
    {
        if (NetSession.Instance.IsClient || EClass.game?.player?.chara is null) {
            return true;
        }

        // TODO: add full client reconnection
        EmpPop.Debug("Blocked loading game as host with active client connection");
        return false;
    }

    [ElinPreLoad]
    internal static void TerminateConnectionOnLoad(GameIOContext context)
    {
        NetSession.Instance.ResetSession();
    }

    [ElinPostSceneInit]
    internal static void TerminateConnectionOnLoad(Scene.Mode mode)
    {
        if (mode == Scene.Mode.Title) {
            NetSession.Instance.ResetSession();
        }
    }
}