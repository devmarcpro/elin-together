using System.Collections.Generic;
using System.Linq;
using ElinTogether.Helper;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     The resident board (LayerPeople) of a multiplayer game has a first tab "Players": every player's character, the
///     ones not connected greyed with "offline", and none of them among the residents or the livestock. A player's row
///     offers to go to it only: the resident actions (rename, appearance, maid, livestock, reserve) are not for another
///     player's character. The same on every game (llm-council 2026-10-24: display only, no option)
/// </summary>
[HarmonyPatch]
internal static class PlayerPeoplePatch
{
    /// <summary>
    ///     A player's character: the local one, a connected player's, or one that was a player's (the flag the host sets
    ///     when a player joins, kept in the save)
    /// </summary>
    internal static bool IsPlayerChara(Chara c)
    {
        return c.IsPlayer || c.GetBool("remote_chara");
    }

    private static bool Active => NetSession.Instance.Connection is not null;

    [HarmonyPrefix]
    [HarmonyPatch(typeof(LayerPeople), nameof(LayerPeople.OnInit))]
    internal static void OnInit(LayerPeople __instance)
    {
        // (the board of the base only: another use of the layer has made its lists already)
        if (!Active || __instance.multi.owners.Count != 0) {
            return;
        }

        // the game adds its three tabs when there are none yet: added here after the players', the same way
        __instance.multi.AddOwner(0, new ListPeoplePlayers());
        __instance.multi.AddOwner(0, new ListPeople { memberType = FactionMemberType.Default });
        __instance.multi.AddOwner(0, new ListPeople { memberType = FactionMemberType.Livestock });
        __instance.multi.AddOwner(0, new ListPeople { memberType = FactionMemberType.Guest });
        __instance.langHint = "h_residents";
    }

    [HarmonyPostfix]
    [HarmonyPatch(typeof(BaseListPeople), nameof(BaseListPeople.OnList))]
    internal static void OnList(BaseListPeople __instance)
    {
        if (!Active || __instance.GetType() != typeof(ListPeople) || __instance.memberType == FactionMemberType.Guest) {
            return;
        }

        foreach (var c in __instance.list.objects.OfType<Chara>().Where(IsPlayerChara).ToList()) {
            __instance.list.objects.Remove(c);
        }
    }

    internal class ListPeoplePlayers : ListPeople
    {
        public override string TextTab => "emp_people_players".lang() + " (" + Players().Count() + ")";

        public override string TextHeader => "_listOf".lang("emp_people_players".lang());

        // (greyed: not connected, wherever the character is; no home and work buttons, the base's business)
        public override bool ShowHome => false;

        public override bool IsDisabled(Chara c)
        {
            return !c.IsPlayer;
        }

        private static IEnumerable<Chara> Players()
        {
            var members = (EClass.Branch ?? EClass.pc.homeBranch)?.members ?? [];
            return members.Concat(EClass.pc.party.members).Concat(EClass._map.charas)
                .Where(IsPlayerChara).Distinct();
        }

        public override void OnList()
        {
            foreach (var c in Players()) {
                list.Add(c);
            }
        }

        public override void SetSubText(Chara a, ItemGeneral b)
        {
            if (!a.IsPlayer) {
                b.SetSubText("emp_people_offline", 300);
                return;
            }

            base.SetSubText(a, b);
        }

        public override void OnClick(Chara c, ItemGeneral i)
        {
            // (the local character as the game has it; another player's not here: the game's line where it is)
            if (c.IsPC || !c.IsAliveInCurrentZone) {
                base.OnClick(c, i);
                return;
            }

            var menu = EClass.ui.CreateContextMenuInteraction().SetHighlightTarget(i);
            menu.AddButton("findMember", () => {
                EClass.pc.SetAI(new AI_Goto(c, 1));
                layer.Close();
            });
            menu.Show();
        }
    }
}
