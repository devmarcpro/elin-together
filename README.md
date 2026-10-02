# Elin Together — "independence" fork

English | [Français](README_fr.md)

A fork of [Elin Together](https://github.com/ElinTogether/ElinTogether), the multiplayer mod for
[Elin](https://store.steampowered.com/app/2135150/Elin/), with one goal: **in game, no difference between the host
and the other players**. Everyone goes where they want, with their own companions, quests, fame and money, while
the world (story, home base, guilds) stays shared.

The original mod keeps the whole party on the host's map and treats the other players as teammates of the host.
Its authors consider separate maps out of scope; this fork is where that is tried. All credit for the mod itself
goes to them (see [Credits](#credits)).

> **Status: experimental.** Everything below is tested on one PC with several game windows (automated in-game
> test suites, see `dev/`). It has been **played only once between two PCs over Steam**, and that one evening
> found a bug the tests had missed. Back up your saves first: `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## What the fork adds

| Feature | What it changes |
|---|---|
| Independent travel | A player leaves for another map without the host. The map and what was done there are kept. Progress is saved regularly while away; chat works across maps. |
| Shared maps | A player can join another player on their map, without the host. If the one holding the map leaves, another takes over. |
| The host drags nobody along | When the host changes map, the players who stayed behind stay. |
| Companions per player | Companions follow the player who recruited them, travel with them, and count in that player's ally limit only. |
| Shipping per player | One shipping chest; the money of a sale goes to whoever put the item in. |
| Combat at each player's pace | A monster acts at the pace of the player it fights, not the host's. |
| Random quests per player | Quests from inhabitants and boards belong to the player who takes them, with the reward, fame and karma. They follow the player everywhere. |
| Shared story | Story quests are in one log: anyone starts, advances and finishes them. Dialog memory, key items and debt are shared. |
| Dungeon quests for everyone | A player who is not the host can take a quest that has its own zone and settle it alone. |
| Trade between players | Click another player → "Trade": both put items and gold, both confirm. |
| Character choice | When joining, a player picks one of their characters in that world or makes a new one. |
| Karma and crime per player | The player who did it loses the karma; guards only chase that player. |
| Shared affinity and guilds | An inhabitant's affinity is the same for all; joining a guild counts for the group. |

Every one of these is a **checkbox on the host's side** (Esc → Mods → Elin Together → *Server Setting*).
Unchecked, the mod behaves like the original.

## Known limits

- Barely played between two PCs over Steam (one evening).
- The world's clock still follows the host.
- Story dialogs played by a non-host player are covered by tests that call the game's code directly, not yet by
  clicking through the real dialogs.
- Dungeon quests: only the taker enters the quest's zone.
- Trade: no equipped items, no check for a full bag.
- A few rare conflicts are known and not fixed (two purchases at the same instant from the same shop, two players
  building on the same tile, a mount existing twice after a trip).
- Mod compatibility is the original's: keep the mod list short and identical for every player.

The full list, and what is planned, is in [`dev/DOCUMENTATION.md`](dev/DOCUMENTATION.md) (French).

## Install

Requires [YK Framework](https://steamcommunity.com/sharedfiles/filedetails/?id=3400020753) and Elin on the
**Nightly** branch (the fork is built against EA 23.351). **Every player must run the same build of this fork**;
it does not talk to the Workshop version.

Download `ElinTogether-independance.zip` from the
[Releases page](https://github.com/devmarcpro/elin-together/releases), unzip it and run `Installer.bat`: it
switches from the Workshop version to this one (`Desinstaller.bat` switches back). The installer and its notes are
in French; the steps are also on the release page. `dev/make_release.ps1` builds that zip from the sources.

To host: launch Elin through Steam, load a save that has a claimed land, then Esc → Mods → Elin Together.

## Build

Environment variables: `ElinGamePath` (root folder of the game) and `SteamContentPath`
(`steamapps/workshop/content`, for `YKFramework.dll`). .NET SDK 11.0 preview, see `global.json`.

```ps
git clone https://github.com/devmarcpro/elin-together
cd elin-together
dotnet restore ./ElinTogether --locked-mode
dotnet build ./ElinTogether -c ReleaseNightly
```

The development setup (several game windows on one PC, the in-game test suites, the debug bridge) is described in
[`dev/SETUP.md`](dev/SETUP.md) (French).

## How it works, in short

The original design: the host simulates the world, every change goes to the clients as a delta, clients send
their actions to the host. The fork adds **zone leases**: a player leaving the host's map asks the host for a lease
on the map it goes to, loads its own copy of the world and simulates that map itself. It sends the map back when it
returns and at regular checkpoints; the host stays the reference. The holder of a lease can host that map for
other players, and hands it over when leaving.

## Reporting

Problems with this fork: [issues here](https://github.com/devmarcpro/elin-together/issues), with both players'
`Player.log` and `ElinMP/Logs/Session_<date>.log` from `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.
Please do not report fork problems to the original project.

## Credits

The mod is the work of the Elin Together team: [DK](https://github.com/gottyduke) and
[Redgeioz](https://github.com/Redgeioz) (code, framework), [105gun](https://github.com/105gun) (code),
[Han](https://github.com/chuahan), Omega, [InuiDame](https://github.com/InuiDame),
[Drakeny](https://github.com/Drakeny) (testing), noa (Elin). MIT license, see [LICENSE](LICENSE).

The fork's changes were written with an AI coding assistant (Claude Code), directed by the fork's owner; each change comes with an in-game test, listed in its commit message. No game file and no decompiled game
code is in this repository.

The original project's README is kept in [中文](README_zh.md) and [日本語](README_ja.md); they describe the original
mod, not this fork.
