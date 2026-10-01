using System.Collections.Generic;
using System.Linq;

namespace ElinTogether.Helper;

/// <summary>
///     Every player keeps its own companions inside the one party Elin knows, see MODLOG (étape 3) <br />
///     The owner is the chara uid of the player who recruited it, none means the party leader (the host)
/// </summary>
internal static class CompanionHelper
{
    internal const string OwnerKey = "emp_owner";

    extension(Chara chara)
    {
        /// <summary>
        ///     Chara uid of the player this companion follows, 0 for the party leader
        /// </summary>
        internal int CompanionOwnerUid => chara.GetInt(OwnerKey);

        internal bool IsCompanionOf(Chara player)
        {
            if (chara == player || chara.IsPC || chara.GetBool("remote_chara") || chara.party is not { } party ||
                !party.members.Contains(chara)) {
                return false;
            }

            var owner = chara.CompanionOwnerUid;
            return owner == player.uid || (owner == 0 && party.leader == player);
        }

        internal void SetCompanionOwner(Chara? player)
        {
            chara.SetInt(OwnerKey, player?.uid ?? 0);
        }

        /// <summary>
        ///     The player to follow when it stands in this zone, otherwise the party leader
        /// </summary>
        internal Chara? FindCompanionOwnerHere()
        {
            var uid = chara.CompanionOwnerUid;
            if (uid == 0 || chara.IsPC || chara.GetBool("remote_chara")) {
                return null;
            }

            return EClass.game.cards.globalCharas.Find(uid) is { IsAliveInCurrentZone: true } owner ? owner : null;
        }
    }

    /// <summary>
    ///     Companions of the player, wherever they are
    /// </summary>
    internal static List<Chara> CompanionsOf(Chara player)
    {
        var party = player.party ?? EClass.pc?.party;
        return party?.members.Where(c => c is not null && c.IsCompanionOf(player)).ToList() ?? [];
    }
}
