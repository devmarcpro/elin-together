# Companion AI of another player: "the player" is its own master (proposed bench tests)

Change under test: `RemoteDontWanderPatch` (Patches/Remote/RemoteTacticsPatch.cs) now lends the companion's owner as
"the player" (`RemoteCraft.AsCrafter`) on the host for every step of `AI_Idle.Run`, `Chara.FindNewEnemy` and
`GoalCombat.Run` of a guest's companion, whether or not "don't wander" is ticked, and only while that guest stands on
the map. Before, only `FindNewEnemy`/`GoalCombat` with the guest's box ticked and known were lent.

Bench: host + 1 client A in the Prairie (`python _tools/mp_test.py`, then the scenarios below with `--reuse`, as in
`_tools/companion_suite.py`). Host bridge 27551, guest 27552, `ev(port, code)` evaluates C# in that game. A recruits a
companion C (K1 of `companion_suite.py`); the host keeps its own companion D. `G` below is A's character on the host
(`EClass.game.cards.globalCharas.Find(<A uid>)`). Every check reads the host (27551), which simulates C. Red = build
before this change, green = after.

Driving the idle AI without waiting for the dice: on the host,
`var ai = new AI_Idle(); C.SetAI(ai); for (var i = 0; i < 3000 && C.ai == ai; i++) ai.Tick();`
(the shared-bag roll is 1 in 20 per pass, fishing 1 in 100: 3000 ticks make a miss negligible). Restore with
`C.SetAIIdle()`.

## CA1  the guest's companion takes from the guest's shared bag, not from the host's

Setup on the host: C and D carry nothing to eat (`C.things.DestroyAll(); D.things.DestroyAll();`). The host's
character gets a container with `GetObj<Window.SaveData>(2).sharedType = ContainerSharedType.Shared` holding 5
`bread`; G gets the same with 5 `apple` (both unlocked, `c_lockLv == 0`). C, D, G and the host stand within 2 tiles,
in sight of each other. Drive C's idle AI as above.

- Red: C holds bread, the host's bag lost some; G's bag untouched.
- Green: C holds apples, G's bag lost them (and the guest's own game shows the same, the host's `CardAddThingDelta`
  reaches it); the host's bag still has 5 bread.
- Control (green both builds): drive D the same way: D takes bread, never apples.

## CA2  the guest's companion follows the guest, not the host (non-regression)

Already done by `CompanionFollowPatch`; checked because the follow block now runs with G as "the player". Host at one
end of the map, A 20 tiles away; drive C's idle AI 300 ticks, then `C.pos.Distance(G.pos)` <= 3 and
`C.pos.Distance(EClass.pc.pos)` > 10. Green before and after; D stays by the host.

## CA3  it attacks an enemy the guest sees and the host cannot ("don't wander" known only on the host)

Setup: the host ticks "don't wander" (`EClass.game.config.tactics.dontWander = true`), A has never told its box:
on the host `G.SetInt("emp_tactics", 0)` in the same `eval` as the drive below (A resends its boxes every 10 s, see
`RemoteTacticsPatch.Update`). Put A and C on one side of a wall, the host on the other side, out of
its line of sight. Spawn a hostile `putty` 3 tiles from C, visible to C and G:
`var e = CharaGen.Create("putty"); e.c_originalHostility = e.hostility = Hostility.Enemy; EClass._zone.AddCard(e, C.pos.GetRandomPointInRadius(2, 3));`
then check `EClass.pc.CanSeeLos(e)` is false and `G.CanSeeLos(e)` is true on the host.
Drive C (`C.FindNewEnemy()` once, then 50 `C.ai.Tick()`).

- Red: `C.enemy` stays null (the host's box measured from the host's eyes).
- Green: `C.enemy == e` and `e.hp` drops.
- Control: the host's companion D, same position as C, does not take `e` as enemy (its own master is the host,
  who cannot see it).

## CA4  "the player" is back after every step, even when one throws

After CA1 and CA3, on the host: `EClass.pc.uid` is the host's character, `EClass.game.config.tactics.dontWander` is
the host's own box, and `ElinTogether.Models.RemoteCraft.IsStandingIn` is false. Make one step throw (e.g. a
`Harmony` test prefix on `Chara.TryTakeSharedItems` that throws once) and check the same three again.

## CA5  no enemy-visibility report under the guest's uid when its companion kills (leak guard)

With CA3's setup and combat mode active (both players in company), let C kill `e`. In the host log there is no
"Self enemy visibility changed ... on chara <e> died" for that kill; within 0.5 s the host's own entry
(`ActionModeCombat.EnemyVisibility[<host uid>]`) is false, and A's entry is the one A reported itself.

## CA6  fishing beside its own master (needs the guest's fishing to be `AI_Fish` on the host)

First check on the host while A fishes: `G.ai is AI_Fish` (or its child). If yes: give C a fishing rod, the host does
not fish, drive C's idle AI: green = C starts `AI_Fish` at a point within 3 tiles of G; red = never (the host was not
fishing). If `G.ai` is not `AI_Fish` there, this test is not playable on the bench and the change is neutral for it.
