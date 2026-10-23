using ElinTogether.Helper;
using ElinTogether.LangMod;
using UnityEngine;

namespace ElinTogether.Patches;

/// <summary>
///     Council 2026-10-23, Personal Pace, this player's side of its lead (the host keeps and counts it, see
///     ElinNetHost.HoldLead): the hours held back come off its own quests, as they would have with the date
///     moving, and it is told "+N h ahead" once its trip is over. When the world catches up, the catch-up
///     postpones its quests by the whole jump like everyone's (WorldDateAdvanceEvent.CatchUp): they keep the time
///     its trip left them
/// </summary>
internal static class WorldMapLead
{
    // the trip is over when no hour of it was held for this long
    private const float TripEndSeconds = 2f;

    private static float _sayAt;
    private static bool _pumping;

    /// <summary>
    ///     Minutes this player is ahead of the world, as the host last said
    /// </summary>
    internal static int Mine { get; private set; }

    /// <summary>
    ///     This many minutes of this player's step were held back: its quests lose them now
    /// </summary>
    internal static void Held(int minutes, int lead)
    {
        PersonalQuests.Postpone(-minutes);
        Mine = lead;
        _sayAt = Time.realtimeSinceStartup + TripEndSeconds;
        if (!_pumping) {
            _pumping = true;
            EClass.core.actionsNextFrame.Add(OnFrame);
        }
    }

    internal static void Set(int lead)
    {
        if (Mine > 0 && lead == 0 && EClass.core.IsGameStarted) {
            Msg.Say("emp_ui_travel_lead_paid".lang());
        }

        Mine = lead;
    }

    private static void OnFrame()
    {
        if (Time.realtimeSinceStartup < _sayAt) {
            EClass.core.actionsNextFrame.Add(OnFrame);
            return;
        }

        _pumping = false;
        if (Mine >= Date.HourToken && EClass.core.IsGameStarted) {
            Msg.Say("emp_ui_travel_lead".Loc(Mine / Date.HourToken));
        }
    }
}
