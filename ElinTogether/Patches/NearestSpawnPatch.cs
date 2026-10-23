using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Reflection.Emit;
using ElinTogether.Helper;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     Council 2026-10-23, world content, point 3: what a map spawns reads the feats of "the player" (legendary
///     chance 1271, friend or foe of Santa and the like 1270/1271/1216, evolved, big daddy and shrine chances 1270).
///     On the host that is the host's character even when a guest stands next to the spawn. Now it is the nearest
///     player to the spawn point: a documented rule (one monster cannot be friendly to one player and hostile to
///     another, so no aggregate). Alone, or with the rule off, it is the game's own player
/// </summary>
[HarmonyPatch]
internal static class NearestSpawnPatch
{
    private static IEnumerable<MethodBase> TargetMethods()
    {
        yield return AccessTools.Method(typeof(Zone), nameof(Zone.SpawnMob), [typeof(Point), typeof(SpawnSetting)]);
        yield return AccessTools.Method(typeof(Zone), nameof(Zone.TryGenerateEvolved));
        yield return AccessTools.Method(typeof(Zone), nameof(Zone.TryGenerateShrine));
        // the big daddy and its local function (the one that sets the hostility)
        foreach (var method in typeof(Zone).GetMethods(AccessTools.all).Where(m => m.Name.Contains("TryGenerateBigDaddy"))) {
            yield return method;
        }
    }

    [HarmonyTranspiler]
    private static IEnumerable<CodeInstruction> Transpile(IEnumerable<CodeInstruction> instructions, MethodBase original)
    {
        var getPc = AccessTools.PropertyGetter(typeof(EClass), nameof(EClass.pc));
        var at = original.GetParameters().ToList().FindIndex(p => p.ParameterType == typeof(Point));
        var offset = original.IsStatic ? 0 : 1;

        foreach (var instruction in instructions) {
            if (instruction.Calls(getPc)) {
                // the spawn point if the method has one, else none: the game's player
                yield return (at < 0 ? new CodeInstruction(OpCodes.Ldnull) : new CodeInstruction(OpCodes.Ldarg, (short)(at + offset)))
                    .MoveLabelsFrom(instruction);
                yield return CodeInstruction.Call(typeof(NearestSpawnPatch), nameof(PlayerFor));
            } else {
                yield return instruction;
            }
        }
    }

    internal static Chara PlayerFor(Point? pos)
    {
        var pc = EClass.pc;
        // PlayerStandIn: a guest's own action is running, its character is already "the player"
        if (!EmpConfig.Server.NearestSpawns.Value || NetSession.Instance.Connection is not ElinNetHost host ||
            PlayerStandIn.IsActive || pos is not { IsValid: true }) {
            return pc;
        }

        var best = pc;
        var bestDistance = pc.IsInActiveMap ? pos.Distance(pc.pos) : int.MaxValue;
        foreach (var chara in host.ActiveRemoteCharas.Values) {
            if (chara.IsInActiveMap && chara.pos.Distance(pos) is var d && d < bestDistance) {
                best = chara;
                bestDistance = d;
            }
        }

        return best;
    }
}
