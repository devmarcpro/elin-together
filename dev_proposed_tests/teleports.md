# Proposed in-game tests: two involuntary teleports (A3, A6)

Bench: two windows already connected on the same map (`python _tools/mp_test.py`), host on port 27551, guest on
27552, both on a quiet outdoor map (no hostile in sight), host rule AutoResync ticked. Every `eval` below is sent
with `python _tools/emp.py -p PORT eval "CODE"` from `dev/` (`PYTHONPATH=_tools/pylib`). Run each test once on the
build BEFORE the fix (expected red) and once on the build with it (expected green).

These are tool tests: A3 feeds a forged snapshot to the reconciliation by hand, A6 makes the gap by moving the
guest without a move message. A real session (a laggy link, a hitch) is what they stand for, not what they play.

## A3. Reconcile force move needs two snapshots in a row

`CharaStateSnapshot.ApplyReconciliation` used to snap a character on the first snapshot that put it more than 2
tiles away (or more than 10 even right after a move). Now the same mismatch must be seen on two snapshots in a row
(within 1 s), never while the character rides, is ridden or carries a parasite, and up to 10 tiles never while a move
delta just came or a task of its owner's game runs.

Each eval does everything in one frame, so no real snapshot of the host can come in between.

### A3.1 one late snapshot does not move a companion (guest window)

Take a companion of the host that the guest sees (`U` = its uid, from the host:
`return EClass.pc.party.members.Find(x => !x.IsPC).uid;`). On the guest (27552):

```csharp
var c = EClass._map.charas.Find(x => x.uid == U);
var snap = ElinTogether.Models.CharaStateSnapshot.Create(c);          // where the host has it
var away = c.pos.GetRandomPointInRadius(4, 6, false, false);          // 4 to 6 tiles off, free
EClass._map.MoveCard(away, c);                                        // our copy drifted, nobody told
var drifted = c.pos.x + "," + c.pos.z;
snap.ApplyReconciliation();
var first = c.pos.x + "," + c.pos.z;
snap.ApplyReconciliation();
var second = c.pos.x + "," + c.pos.z;
return "home " + snap.Pos.X + "," + snap.Pos.Z + " drifted " + drifted + " after1 " + first + " after2 " + second;
```

- Red (before): `after1` is `home` (snapped on the first snapshot).
- Green (after): `after1` is `drifted`, `after2` is `home`. The guest journal has one line
  "Reconcile force move chara U".

### A3.2 the > 10 tiles fast path also waits for a second snapshot

Same eval with `GetRandomPointInRadius(12, 16, false, false)`. Red: `after1` is `home`. Green: `after1` is
`drifted`, `after2` is `home`.

### A3.3 a stale record does not count (guest window)

Only the move and the drift, no forged snapshot: the real host snapshots (5 per second) do the rest.

```csharp
var c = EClass._map.charas.Find(x => x.uid == U);
EClass._map.MoveCard(c.pos.GetRandomPointInRadius(4, 6, false, false), c);
return c.pos.x + "," + c.pos.z;
```

Read its tile again 2 s later. Red and green: back home (green about 0.2 s later than red: the second snapshot),
one "Reconcile force move chara U" line, never stuck away.

### A3.4 never while riding or ridden (guest window)

A rider/parasite link faked on the guest's copy for the time of the eval (restored at the end):

```csharp
var c = EClass._map.charas.Find(x => x.uid == U);
var other = EClass._map.charas.Find(x => x != c && !x.IsPC && x.ride == null && x.host == null);
var snap = ElinTogether.Models.CharaStateSnapshot.Create(c);
EClass._map.MoveCard(c.pos.GetRandomPointInRadius(4, 6, false, false), c);
var drifted = c.pos.x + "," + c.pos.z;
c.ride = other;
snap.ApplyReconciliation(); snap.ApplyReconciliation(); snap.ApplyReconciliation();
var after = c.pos.x + "," + c.pos.z;
c.ride = null;
return "drifted " + drifted + " after " + after;
```

- Red (before): `after` is home (only `host` was checked).
- Green (after): `after` equals `drifted`. Repeat with `c.parasite = other` instead of `c.ride` (same result).
  Within a second of `c.ride = null` the real snapshots bring it home again.

### A3.5 the same on the host, for the guest's character

The host reconciles the guest's character from the guest's own snapshots (`ElinNetHost.OnClientRemoteCharaSnapshot`).
On the host (27551), with `G` = the guest's pc uid (guest: `return EClass.pc.uid;`):

```csharp
var c = EClass._map.charas.Find(x => x.uid == G);
var snap = ElinTogether.Models.CharaStateSnapshot.Create(c);
EClass._map.MoveCard(c.pos.GetRandomPointInRadius(4, 6, false, false), c);
var drifted = c.pos.x + "," + c.pos.z;
snap.ApplyReconciliation(c);
var first = c.pos.x + "," + c.pos.z;
snap.ApplyReconciliation(c);
return "drifted " + drifted + " after1 " + first + " after2 " + c.pos.x + "," + c.pos.z;
```

Red: `after1` is home. Green: `after1` is `drifted`, `after2` home.

### A3.6 like a player plays

Both players walk for 60 s with turbo (`steps()` of `resync_suite.py`, or by hand), the host's companions follow.
Count "Reconcile force move" lines in both journals over that minute: expected fewer than before, and none for a
companion that just stepped (compare with the "Move delta jump" lines of the same uid and second).

## A6. A map reloaded to repair it keeps the guest on its own tile

Before: NetDesync on the guest asks for its map again; the host stores the tile of its copy of the guest
(`KeepSpotForResync`) and the guest is put there (`OnZoneActivateResponse`, `pc.Stub_Move(response.Pos)`). When
that copy lags (moves not arrived yet, or the guest walked during the round trip) the guest is snapped back. Now the
guest notes the request (`MarkResync`), keeps its own tile just before the old map is left (`TakeResyncSpot`) and
stands there again on the reloaded map when that tile is free and not blocked, then tells the host
(`CharaMoveDelta`). Else the host's tile, as before.

### A6.1 host's copy 2 tiles behind, then a repair (guest window, then both)

The reconciliation lets a gap of 2 tiles be (dist <= 2): moving the guest 2 tiles without a move message leaves the
host's copy behind for good, which stands for the lagging copy.

1. Guest (27552): note its uid `G` and move it 2 tiles, silently:

   ```csharp
   var p = new Point(EClass.pc.pos.x + 2, EClass.pc.pos.z);
   if (p.IsBlocked || p.HasChara) return "pick another direction";
   EClass._map.MoveCard(p, EClass.pc);
   return EClass.pc.pos.x + "," + EClass.pc.pos.z;
   ```

2. Host (27551), after 2 s: `var c = EClass._map.charas.Find(x => x.uid == G); return c.pos.x + "," + c.pos.z;`
   must still be the old tile (2 tiles behind).
3. Guest: make a map gap the guest alone has, as `resync_suite.py` R2 does (a floor item removed inside a
   `DynamicDelta`, the `LOCAL` template of that suite):

   ```csharp
   new ElinTogether.Models.DynamicDelta { Action = n => {
       EClass._zone.RemoveCard(EClass._map.things.Find(x => x.isThing && !x.IsInstalled && x.parent == EClass._zone));
   } }.Apply(ElinTogether.Net.NetSession.Instance.Connection);
   return "ok";
   ```

   (if the map holds no loose item, drop one first from the host and wait for it on the guest). The guest must
   then stay idle.
4. Within about 10 s the guest journal shows "Reloading ... to repair it", then "Received zone activation".
   15 s after step 3, read the guest's tile (`return EClass.pc.pos.x + "," + EClass.pc.pos.z;`) and the host's copy
   of it (step 2's eval).

- Red (before): the guest is back on the old tile (2 tiles back, the host's copy).
- Green (after): the guest is on the tile of step 1, the guest journal has "Resync: keeping our own tile", and the
  host's copy shows the same tile within 1 s (the move delta sent after the placement).

### A6.2 walking during the round trip (like a player plays)

As A6.1 without step 1, but right after "Reloading ... to repair it" appears, walk the guest 3 tiles by hand (or
`steps(A, 3)` of `resync_suite.py`). Red: snapped back to where it stood when asking. Green: it stays where its
walk ended. (Timing is by hand: the round trip on one machine is short; repeat a few times.)

### A6.3 own tile taken: falls back to the host's tile

As A6.1, but before step 3, on the host, put a companion on the guest's step-1 tile `gx,gz` without a move
message: `var n = EClass.pc.party.members.Find(x => !x.IsPC); EClass._map.MoveCard(new Point(gx, gz), n); return "ok";`.
The reloaded map is the host's copy, the companion stands there. Green: the guest is put on the host's tile (old
behaviour), no "keeping our own tile" line.

### Not covered

A soft rejoin whose map numbers differ (`ElinNetClientSoftRejoin`, also marked now) is not played here; a reload
that is not a repair (travel, recall) is unchanged by design (`TakeResyncSpot` needs the mark and the same map).
