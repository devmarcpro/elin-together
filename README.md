# Elin Together — "independence" fork

English | [Français](README_fr.md)

[![Latest release](https://img.shields.io/github/v/release/devmarcpro/elin-together?include_prereleases&label=latest%20release)](https://github.com/devmarcpro/elin-together/releases)

A fork of [Elin Together](https://github.com/ElinTogether/ElinTogether), the multiplayer mod for
[Elin](https://store.steampowered.com/app/2135150/Elin/), with one goal: **in game, no difference between the host
and the other players**. Everyone goes where they want, with their own companions, quests, fame and money, while
the world (story, home base, guilds) stays shared. The world itself no longer has to live on one player's PC.

The original mod keeps the whole party on the host's map and treats the other players as teammates of the host.
Its authors consider separate maps out of scope; this fork is where that is tried. All credit for the mod itself
goes to them (see [Credits](#credits)).

> **Status: experimental.** Every version is a pre-release, built for Elin's Nightly branch. Most of it is checked
> by automated in-game tests on one PC (two to five game windows). It has been played for real by one small group
> only: two or three players over Steam, for a few evenings, each of which found bugs the tests had missed. Every
> release note says what was played and what was not. Back up your saves first:
> `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

[What it changes](#what-it-changes) · [Install](#install) · [Play](#play) ·
[The depot](#keeping-the-world-online-the-depot) · [Mods](#mods) · [Host settings](#host-settings) ·
[Known limits](#known-limits) · [Build](#build)

## What it changes

### Everyone goes where they want

- **Independent travel.** A player leaves for another map without the host. The map and what was done there are
  kept, progress is saved every minute while away, and chat works across maps.
- **Shared maps.** A player can join another player on their map, host or not. If the one holding the map leaves,
  another takes over.
- **Nobody is dragged along.** When the host changes map, the others stay where they are. A player enters a map by
  its entrance; nobody is teleported onto the host.
- **Each at their own pace.** A monster acts when the player it fights acts, not at the host's pace, and a guest
  walks as smoothly as the host.
- **Your time is your own.** A player who goes to bed sleeps at once; the night only passes for the world when
  everyone sleeps at the same time. When another player travels or sleeps, the date moves on, but you are no
  hungrier, your food does not rot and your quest deadlines do not move.

### To each player their own

- **Companions** follow the player who recruited them, whatever the way (dialog, monster ball, mount, bought
  animal), travel with them, count in that player's ally limit and obey that player's orders.
- **Random quests, fame and karma.** Five quests each, with their reward. Crime too: the player who did it loses
  the karma, and guards only chase that player.
- **Money.** The money of a shipping sale goes to whoever put the item in the chest; a guest pays a bill with its
  own gold.
- **Your character.** When joining, you get the character you played, with no question asked; a new player makes
  one on the game's creation screen. The host can also let players bring a character from one of their solo saves.
- **Your settings.** Windows, auto combat, bag sorting and companion orders stay yours at every map change and
  reconnection.

### One world for everyone

- **Story.** Story quests are in one log: anyone starts, advances and finishes them. Dialog memory, key items and
  debt are shared.
- **Home base.** A guest builds like the host (floors, walls, furniture, mining, digging, cutting, zones, the
  terrain tool) and what one builds is seen by the other at once. Research, hearth skills, policies, residents and
  chest settings can be managed by any player. The host can keep the base to itself with one checkbox.
- **Guilds, affinity, codex, bank.** Joining a guild counts for the group, an inhabitant's affinity is the same for
  all, the cards one player collects reach everyone's codex, and the bank shows the same content everywhere.
- **Dungeon quests.** Any player can take a quest that has its own zone. When one sets out, the other gets a Yes/No
  box to come along: the zone is shared and the reward goes to whoever took the quest.
- **Between players.** A trade window (both put items and gold, both confirm), duels where nobody dies and nothing
  is lost, and no killing outside a duel.

### A guest plays like a solo player

Dozens of fixes so that what works for the host works for a guest: death and will, the god's gifts, altars, traps,
spellbooks, the healer, blessings, investing, runes, auto-dump, tools held in hand, Kettle's copy shop, bringing a
companion back at the barman's, windows that used to open on the host's screen… The list is in
[`dev/DOCUMENTATION.md`](dev/DOCUMENTATION.md) (French).

### The world does not depend on the host's PC

- **A depot keeps the world**: a private GitHub repository, a shared folder, or a small server application. The
  first player there takes the world and hosts it, every save goes back, and when they leave the next one takes
  over. See [the depot](#keeping-the-world-online-the-depot).
- **A world that changes hands.** Whoever takes the world over plays their own character; the former host gets
  theirs back when joining. If someone already hosts, you are sent into their game instead of opening a copy.
- **Nothing left for the host to do.** The world saves itself every 2 minutes while others play, and a world
  already shared opens to Steam friends as soon as it is loaded.
- **A dropped link is harmless.** A guest who loses the connection comes back into the game by itself (it tries
  for 3 minutes).
- **The games stay in agreement.** No message is dropped when the link is saturated. Every 2 seconds the games
  compare a few numbers per map, and a map that keeps differing is reloaded in place.
- **A dedicated server**, like a Minecraft server: an Elin nobody plays keeps the world running.

### The same mods for everyone, without subscribing

- **The mods of the game are fetched by themselves.** If Workshop mods are missing when you join, they are
  downloaded without subscribing, Elin restarts once with exactly the mods of that game and brings you back into
  it. Your own mod list is back at the next start. See [Mods](#mods).
- **Different Elin versions can play together.** Only the mod's version must be the same for everyone; players on
  another Elin version are let in with a warning.

Almost all of this is a **checkbox on the host's side**: unticked, the mod behaves like the original. See
[Host settings](#host-settings).

## Screenshots

| | |
|---|---|
| ![Host options: every feature is a checkbox](assets/screens/host-options.jpg) | ![The host leaves on a quest: the guest chooses to go along](assets/screens/quest-ask-guest.jpg) |
| Host options: every feature is a checkbox | The host leaves on a quest: the guest chooses to go along |
| ![Both players in the same quest zone](assets/screens/quest-together.jpg) | ![The guest leaves on a quest: the same question for the host](assets/screens/quest-ask-host.jpg) |
| Both players in the same quest zone | The guest leaves on a quest: the same question for the host |
| ![Trading between players](assets/screens/trade.jpg) | ![Each player has its own fame and karma](assets/screens/own-fame-karma.jpg) |
| Trading between players | Each player has its own fame and karma |
| ![Choosing a character when joining](assets/screens/character-choice.jpg) | ![Base: a guest's request is refused, at no cost](assets/screens/base-host-only.jpg) |
| Choosing a character (if the host turns it on) | Base kept to the host: a guest's request is refused, at no cost |

## Install

You need Elin on Steam, on the **Nightly** branch (Steam → right-click Elin → Properties → Betas), and the
[YK Framework](https://steamcommunity.com/sharedfiles/filedetails/?id=3400020753) mod. Subscribing to
[Elin Together](https://steamcommunity.com/sharedfiles/filedetails/?id=3773298709) on the Workshop brings it along.
Launch Elin once after subscribing, then close it.

1. Download `ElinTogether-independance.zip` from the
   [Releases page](https://github.com/devmarcpro/elin-together/releases).
2. Unzip the whole folder and run `Installer.bat`. It finds Elin, copies the mod and switches from the Workshop
   version to this one.
3. Launch Elin through Steam.

`Desinstaller.bat` switches back to the Workshop version; nothing is deleted. The installer and its notes
(`LISEZMOI.txt`) are in French; the steps are also on each release page.

**On a Mac** (Elin in CrossOver, Whisky or Wine): download `ElinTogether-independance-mac.zip`, unzip it, open
Terminal, type `bash` and a space, drag `Installer-Mac.command` into the window and press Enter. It is the same
mod. Not tried on a real Mac yet.

**Every player must install the same release.** This fork does not talk to the Workshop version, nor to another
version of itself. Each release is built for one Elin build, named in its title.

## Play

Open the mod's panel with the *Elin Together* button on the title screen, or Esc → Mods → Elin Together in game.
It has three tabs: *Lobby*, *Server Setting* (the host's rules) and *Client Settings*.

- **Host.** Load a save that has a claimed land, then *Start Server* in the Lobby tab. A world that was already
  shared opens to your Steam friends by itself.
- **Join.** Accept a Steam invite, use *Join Game* on your friend's name in the Steam friends list, or pick the
  game in the Lobby tab. *Join by address* is for a server.
- **Rules.** The host sets them in *Server Setting*; a change applies at once, for everyone.

## Keeping the world online: the depot

A depot keeps the shared world outside any player's saves, so the group does not depend on one person being
there. Each player who may host sets it once, in *Client Settings*: **Depot**, and **Depot key** when there is a
password or a key. A friend who only joins needs neither.

| Depot | What it takes | "Depot" setting |
|---|---|---|
| Private GitHub repository | A GitHub account for one player of the group. No PC left on, no port to open. | `github:owner/repository` |
| Elin Together Server (`ElinTogetherServer.exe`, in the zip) | A PC that stays on. Elin is not needed on it. TCP port 55557. | `host:55557`, or just *Join by address* |
| Shared folder | A folder every player can reach, shared or synced. | The path of the folder |

Then, in the Lobby tab:

- **Put this save on the server**, with a save loaded and the game not yet open to others: that save becomes the
  world of the depot.
- **Take the world from the server and host it**, from the title screen: you get the latest world and host it;
  the others join you through Steam. If someone already hosts, the button names them and lets you join their game.
- Every save goes back to the depot, at most every 5 minutes and once more when quitting. When the host leaves,
  anyone can take the world. If the host crashes, the world frees itself after 3 minutes.

**With GitHub**, the player who owns the repository:

1. creates an empty **private** repository on github.com, only for this world (the mod refuses a public one);
2. creates a fine-grained access token limited to that repository, with *Contents: Read and write*;
3. sets **Depot** to `github:owner/repository` and pastes the token into **Depot key**;
4. gives both to the friends who may host. They need no GitHub account.

The key stays in plain text in the mod's settings file on each PC; it only opens that repository and is revoked in
one click. A world over 20 MB zipped is refused. GitHub keeps every version of the world, which is a free backup
and also means the repository grows with each save: delete it and create a new one when it gets large. The depot
also holds `modlist.txt`, the mods of the world.

**Dedicated server.** `ElinTogetherServer.exe` has a second mode, "With Elin on this PC: the world runs all the
time": Elin runs behind without a window and the players use *Join by address* (`host:55556`, UDP). `Serveur.bat`
does the same with a game window. Windows only.

## Mods

When you join a game, or take a world from a depot, and Workshop mods are missing on your PC: they are downloaded
without your Steam account subscribing to anything, Elin closes and restarts **once** with exactly the mods of
that game, then brings you back into it. If mods of yours block the join, Elin restarts once without them. At the
next start of Elin your own mod list is back, untouched. Nothing is ever deleted or unsubscribed.

- The reference list is the `modlist.txt` of the depot when the world comes from one, else the host's mods.
- If Elin does not restart by itself, start it by hand within half an hour: it brings you back into the game.
- A mod installed by hand, outside the Workshop, cannot be downloaded: its name is shown.
- To keep your own mods and only be told what differs, untick "Fetch the mods of the game by itself" in
  *Client Settings*.

**These mods are chosen by the host and their code runs on your PC: use this with people you trust.**

AutoAct and Dynamic Riding are supported. For other mods, compatibility is the original's.

## Host settings

Esc → Mods → Elin Together → *Server Setting*. Each new behaviour has its own checkbox and a line of explanation
in game. The rules are the host's and apply to everyone as soon as they change.

<details>
<summary>All the checkboxes and their default</summary>

| Checkbox | Default | Ticked |
|---|---|---|
| Independent travel | on | Everyone goes where they want, alone or together. Off: everyone follows the host. |
| Players choose their character when joining | off | A joining player picks one of its characters in this world, or makes a new one. Off: the one it played last. |
| Players can bring a character from their own saves | off | The character, its equipment, bag, gold, fame and karma. Not its companions, base, quests or bank. The save is only read. |
| Random quests, fame and karma per player | on | 5 random quests each, with their reward, fame and karma. Story quests stay shared. |
| Shipping per player | on | Shipping money goes to the player who put the item in. Off: all to the host. |
| Trade window between players | on | Click another player to trade items and gold. Both confirm. |
| Other players can use build mode | on | The other players build in the base; they pay the gold and the materials. Off: only the host builds. |
| Only the host manages the base | off | What the other players ask of the base (research, policies, residents, build mode…) is refused. |
| Duels between players | on | "Challenge to a duel" on another player's character. Nobody dies, both are healed, nothing is lost. |
| Players can kill each other | off | Off: a strike that would kill another player's character leaves it at 0 hit points. |
| Combat on each player's time | on | A monster acts when the player it fights acts: nobody waits. Takes over turn-based combat. |
| Each player on its own clock | on | A guest walks and acts as smoothly as the host, not at the pace of the network. |
| Every player walks at the pace of a solo game | on | The length of a step no longer depends on the other players' speed. |
| One date for the whole world | on | Time passed by a player alone on another map counts for everyone. Off: only the host's date counts. |
| What time does to the world happens once | on | Weather, expired quests, taxes, salaries and letters are handled by one game only. |
| Everyone sleeps for themselves | on | A player who goes to bed sleeps at once. The night passes for the world when all sleep at the same time. |
| Time only jumps when everyone jumps | on | A step on the world map only moves the date when all the players travel together. |
| Tax on the most famous player | on | The monthly tax is computed on the highest fame among the connected players. Off: on the host's. |
| Auto-dump spares hand and tool belt | on | Auto-dump leaves what you hold and what is in your tool belt. Off: as in the game. |
| Players come back by themselves after a connection loss | on | A player who loses the connection joins the game again by itself, for 3 minutes. |
| Repair the map by itself | on | A player whose map no longer matches the host's loads it again, at most once every 30 seconds. |
| The world is saved by itself while others play | on | Every 2 minutes while another player is in the game, and when the last one leaves. |
| The game opens to friends by itself when a world is loaded | on | Friends can join without the host starting the server by hand. |
| The other players keep a copy of the world | off | After each automatic save, every player's PC keeps a copy of the world, outside its own saves. |
| No world reload when the host and a player meet again (new) | off | The player stays on its map, or loads that one map, instead of the whole world. |
| Show the mods of the game to the players | on | The mod list is known before joining, and a refused player is told which mods differ. |
| Require the same Elin version | off | Players on another version of Elin are refused. Off: let in with a warning. |
| Turn-Based Combat | on | The original's rule. No effect while "Combat on each player's time" is on. |
| Shared Average Speed | off | The original's rule: one speed for all players, the average. |

</details>

## Known limits

- **Played for real by one small group only.** Much of the newest work has only run on the test bench. "Not
  played" in a release note or a commit message means exactly that.
- **When the host leaves or crashes, no guest takes the world over by itself.** Someone takes it from the depot by
  hand.
- **One date for the world**, that of the player furthest ahead; only its effects (hunger, rot, deadlines) are per
  player. When the host sleeps alone, the date still moves by about 40 minutes. On the world map, when everyone
  travels together, only the host's steps move it.
- During the few seconds of a night of its own, a player can be attacked: the world goes on for the others.
- When the host and a guest meet again on a map, the guest's screen reloads. The checkbox "No world reload when
  the host and a player meet again" avoids it; it is new and off by default.
- On the host's screen, walking guests can move in jumps of three tiles.
- A player refused by the holder of a map still receives the whole world.
- **More than three players**: five game windows were tested on one PC, never five real PCs. Expect the game to
  slow down as players are added.
- Dungeon quests for two, when the guest took the quest: subdue, harvest and music quests. Defense quests are
  settled alone.
- Duels have no arena, betting or give-up button. Equipped items cannot be traded.
- Mods fetched by themselves: Workshop mods only. Not tried with Elin restarted by Steam, through a Steam lobby,
  on Steam Deck or Linux, or on a Mac.
- A few rare conflicts are known and not fixed: two players building on the same tile, a mount existing twice
  after a trip.

The full list, and what is planned, is in [`dev/DOCUMENTATION.md`](dev/DOCUMENTATION.md) (French).

## If something goes wrong

- The host unticks the checkbox involved: for that point the mod behaves like the original again.
- A player whose game no longer matches the others' types `emp.reconnect_self` in the console.
- Report it [here](https://github.com/devmarcpro/elin-together/issues), with every player's `Player.log` and
  `ElinMP/Logs/Session_<date>.log` from `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`. Please do not report
  fork problems to the original project.

## Build

Environment variables: `ElinGamePath` (root folder of the game) and `SteamContentPath`
(`steamapps/workshop/content`, for `YKFramework.dll`). .NET SDK 11.0 preview, see `global.json`.

```ps
git clone https://github.com/devmarcpro/elin-together
cd elin-together
dotnet restore ./ElinTogether --locked-mode
dotnet build ./ElinTogether -c ReleaseNightly
```

`dev/make_release.ps1` builds the two zips of a release, Windows and Mac. The development setup (several game
windows on one PC, the in-game test suites, the debug bridge) is described in [`dev/SETUP.md`](dev/SETUP.md)
(French).

## How it works, in short

The original design: the host simulates the world, every change goes to the clients as a delta, clients send
their actions to the host. The fork adds **zone leases**: a player leaving the host's map asks the host for a lease
on the map it goes to, loads its own copy of the world and simulates that map itself. It sends the map back when it
returns and at regular checkpoints; the host stays the reference. The holder of a lease can host that map for
other players, and hands it over when leaving.

A depot is the world as one archive, plus a lock that says who hosts. The host renews the lock every minute; a
lock that has not been renewed for 3 minutes is free.

## Credits

The mod is the work of the Elin Together team: [DK](https://github.com/gottyduke) and
[Redgeioz](https://github.com/Redgeioz) (code, framework), [105gun](https://github.com/105gun) (code),
[Han](https://github.com/chuahan), Omega, [InuiDame](https://github.com/InuiDame),
[Drakeny](https://github.com/Drakeny) (testing), noa (Elin). MIT license, see [LICENSE](LICENSE).

The fork's changes were written with an AI coding assistant (Claude Code), directed by the fork's owner; each
change comes with an in-game test, listed in its commit message. No game file and no decompiled game code is in
this repository.

The original project's README is kept in [中文](README_zh.md) and [日本語](README_ja.md): each starts with an
older translation of this fork's description, and the rest of the file describes the original mod, not this fork.
