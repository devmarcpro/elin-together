using System;
using System.Linq;
using System.Globalization;
using System.IO;
using System.Net;
using System.Security.Cryptography;
using System.Text;
using System.Threading;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace ElinTogether.Helper;

/// <summary>
///     The save depot kept in a private GitHub repository: it answers the same five requests as Elin Together
///     Server (WHO, TAKE, PUT, BEAT, RELEASE) with two files of the default branch, `lock.json` (who hosts) and
///     `world.zip`. Every write names the version it replaces (`sha`), so of two players writing at once GitHub
///     accepts one: that refusal is the lock. Nothing is ever forced, and the history keeps every world. <br />
///     Nothing of the game in here (dev/_tools/github_depot_cli compiles this file alone). The access key only
///     ever travels in the Authorization header: never in an address, a message or a log
/// </summary>
internal static class GitHubDepot
{
    /// <summary>
    ///     Above this, the world does not go to GitHub (the request costs about six times the archive in memory)
    /// </summary>
    internal const int MaxWorld = 20 * 1024 * 1024;

    private static readonly TimeSpan _lockLife = TimeSpan.FromMinutes(3);
    private static readonly object _gate = new();

    // tests talk to dev/_tools/fake_github.py: nothing but this machine can stand in for GitHub
    private static readonly string _api =
        Uri.TryCreate(Environment.GetEnvironmentVariable("ELINTOGETHER_GITHUB_API"), UriKind.Absolute, out var test) &&
        test.Scheme == "http" && test.Host == "127.0.0.1"
            ? "http://127.0.0.1:" + test.Port
            : "https://api.github.com";

    private static string _repo = "";
    private static string _token = "";

    // the repository was seen, and it is private
    private static bool _seen;

    // the version of the world this game took or last sent: what its next save replaces, and nothing else
    private static string? _worldSha;

    // the world changed in the depot while this game hosted it: nothing more goes there until it is taken again
    private static bool _changed;

    // the save last sent, accepted or not: GitHub may have taken it and its answer been lost on the way
    private static string? _triedSha;

    // where the game of this player is joined, written in the lock with its name
    private static string _join = "";

    /// <summary>
    ///     The version of the depot's world this game plays from (taken, or last sent). Null: none
    /// </summary>
    internal static string? WorldSha => _worldSha;

    /// <summary>
    ///     Where the player who holds the world is joined, as the lock last read says (the `join` of that player's
    ///     requests). Empty: nobody else holds it, or the lock was written by a version that did not say
    /// </summary>
    internal static string HeldJoin { get; private set; } = "";

    static GitHubDepot()
    {
        ServicePointManager.SecurityProtocol |= SecurityProtocolType.Tls12;
    }

    /// <summary>
    ///     One request, answered like SaveDepot.Ask. Refusals: "password" (key refused), "missing", "public",
    ///     "held name", "empty", "too big", "changed". GitHub not answering is an IOException
    /// </summary>
    /// <param name="descends">
    ///     PUT of a save kept from an earlier session: the version of the depot's world it was played from. The
    ///     depot holding anything else is "changed": such a save never replaces a world it does not come from
    /// </param>
    /// <param name="join">where the others join this player's game, kept in the lock while it holds the world</param>
    internal static (bool Ok, string Text, byte[]? Body) Ask(string repo, string token, string command, string me,
        string name, byte[]? body = null, string? descends = null, string? join = null)
    {
        // one request at a time: two writes of one player would refuse each other
        lock (_gate) {
            if (repo != _repo) {
                _repo = repo;
                _seen = _changed = false;
                _worldSha = _triedSha = null;
            }

            _token = token.Trim();
            _join = join ?? "";
            // (a save of an earlier session is compared for this one request: refused, it leaves nothing behind
            // that a save put in the depot afterwards would be compared with)
            var lent = command == "PUT" && _worldSha is null && descends is not null;
            if (lent) {
                _worldSha = descends;
            }

            var done = false;
            try {
                var reply = Handle(command, me, name, body);
                done = true;
                return reply;
            } catch (No no) {
                return (false, no.Message, null);
            } catch (Exception ex) when (ex is JsonException or FormatException or InvalidCastException) {
                throw new IOException("GitHub sent something unreadable");
            } finally {
                if (lent && !done) {
                    _worldSha = null;
                    _changed = false;
                }
            }
        }
    }

    private static (bool Ok, string Text, byte[]? Body) Handle(string command, string me, string name, byte[]? body)
    {
        if (_token.Length == 0) {
            throw new No("password");
        }

        if (body is { Length: > MaxWorld }) {
            throw new No("too big");
        }

        if (!_seen) {
            var about = Send("GET", "");
            if (about.Status != 200) {
                throw new No("missing");
            }

            // a public repository would show the world, and all its history, to everyone
            if ((bool?)JObject.Parse(Encoding.UTF8.GetString(about.Body))["private"] != true) {
                throw new No("public");
            }

            _seen = true;
        }

        switch (command) {
            case "WHO":
                return (true, Holder(ReadLock(), me) ?? "", null);
            case "TAKE":
                _changed = false;
                _worldSha = _triedSha = null;
                Hold(me, name);
                (int Status, byte[] Body, DateTime Date) world;
                try {
                    world = Send("GET", "/contents/world.zip", raw: true);
                } catch (No) {
                    Free(me);
                    throw;
                }

                if (world.Status != 200) {
                    Free(me);
                    throw new No("empty");
                }

                _worldSha = BlobSha(world.Body);
                return (true, "", world.Body);
            case "PUT":
                if (body is null || body.Length == 0) {
                    throw new No("empty");
                }

                if (_changed) {
                    throw new No("changed");
                }

                // the lock first: a player who lost it writes no world
                Hold(me, name);
                var mine = BlobSha(body);
                for (var attempt = 0; attempt < 2; attempt++) {
                    var there = WorldThere();
                    // GitHub took a save and its answer was lost on the way (a big world, a slow link): the world
                    // there is ours, not another player's
                    if (there is not null && there == _triedSha) {
                        _worldSha = there;
                    }

                    if (there == mine) {
                        _worldSha = there;
                        return (true, "", null);
                    }

                    if (_worldSha is not null && there != _worldSha) {
                        // someone else hosted and saved meanwhile: their world stays, ours stays on this PC
                        _changed = true;
                        Free(me);
                        throw new No("changed");
                    }

                    // (GitHub asks for a pause between two writes)
                    Thread.Sleep(_api.StartsWith("https") ? 1000 : 0);
                    _triedSha = mine;
                    // without a version of ours (a save put in the depot while nobody hosts), the world there is
                    // replaced, as the server does; the history keeps it
                    if (Write("world.zip", body, there, "world saved by " + name) is { } sha) {
                        _worldSha = sha;
                        WriteModList(name);
                        return (true, "", null);
                    }
                }

                throw new IOException("GitHub keeps refusing the world");
            case "BEAT":
                if (_changed) {
                    throw new No("changed");
                }

                // cut off long enough for another player to host, save and leave: the lock is free again, and
                // taking it back would hide that the world is no longer the one played here
                if (_worldSha is not null && WorldThere() != _worldSha) {
                    if (Holder(ReadLock(), me) is { } other) {
                        throw new No("held " + other);
                    }

                    _changed = true;
                    Free(me);
                    throw new No("changed");
                }

                Hold(me, name);
                return (true, "", null);
            case "RELEASE":
                _changed = false;
                _worldSha = _triedSha = null;
                Free(me);
                return (true, "", null);
            default:
                throw new No("unknown");
        }
    }

    /// <summary>
    ///     Takes or keeps the lock. The write names the version read: of two players taking a free or expired
    ///     lock at once, one is refused, reads again and finds the other
    /// </summary>
    private static void Hold(string me, string name)
    {
        for (var attempt = 0; attempt < 2; attempt++) {
            var held = ReadLock();
            if (Holder(held, me) is { } who) {
                throw new No("held " + who);
            }

            if (WriteLock(me, name, held)) {
                return;
            }
        }

        throw new IOException("GitHub keeps refusing the lock");
    }

    private static void Free(string me)
    {
        var held = ReadLock();
        if (held.Id == me) {
            WriteLock("", "", held);
        }
    }

    private static string? Holder((string Id, string Name, string? Sha, DateTime Beat, DateTime Now, string Join) held, string me)
    {
        var other = held.Id.Length > 0 && held.Id != me && held.Now - held.Beat < _lockLife;
        HeldJoin = other ? held.Join : "";
        return other ? held.Name : null;
    }

    // the time is GitHub's (the Date of its answer), read and written: two PCs never agree to the second
    private static (string Id, string Name, string? Sha, DateTime Beat, DateTime Now, string Join) ReadLock()
    {
        var reply = Send("GET", "/contents/lock.json");
        if (reply.Status != 200) {
            return ("", "", null, default, reply.Date, "");
        }

        var file = JObject.Parse(Encoding.UTF8.GetString(reply.Body));
        var held = JObject.Parse(Encoding.UTF8.GetString(Convert.FromBase64String((string)file["content"]!)));
        return ((string?)held["id"] ?? "", (string?)held["name"] ?? "", (string)file["sha"]!,
            ((DateTime?)held["beat"] ?? default).ToUniversalTime(), reply.Date, (string?)held["join"] ?? "");
    }

    private static bool WriteLock(string id, string name, (string Id, string Name, string? Sha, DateTime Beat, DateTime Now, string Join) read)
    {
        // (added to the three fields every version reads; a free lock carries none)
        var held = new JObject { ["id"] = id, ["name"] = name, ["beat"] = read.Now };
        if (id.Length > 0 && _join.Length > 0) {
            held["join"] = _join;
        }

        return Write("lock.json", Encoding.UTF8.GetBytes(held.ToString(Formatting.None)), read.Sha,
            id.Length > 0 ? "hosted by " + name : "free") is not null;
    }

    /// <summary>
    ///     The version of the world in the depot, without downloading it. Null: no world
    /// </summary>
    private static string? WorldThere()
    {
        var reply = Send("GET", "/contents/");
        if (reply.Status != 200) {
            // (a repository with no file at all answers 404)
            return null;
        }

        foreach (var file in JArray.Parse(Encoding.UTF8.GetString(reply.Body))) {
            if ((string?)file["name"] == "world.zip") {
                return (string?)file["sha"];
            }
        }

        return null;
    }

    /// <returns>the new version, null when GitHub refused because the file is no longer the version named</returns>
    private static string? Write(string file, byte[] content, string? sha, string message)
    {
        // written by hand, the archive in pieces: one more copy of a 20 MB world is what this avoids
        var head = Encoding.UTF8.GetBytes("{\"message\":" + JsonConvert.ToString(message) +
                                          (sha is null ? "" : ",\"sha\":\"" + sha + "\"") + ",\"content\":\"");
        var reply = Send("PUT", "/contents/" + file, false, head, content);
        return reply.Status switch {
            200 or 201 => (string)JObject.Parse(Encoding.UTF8.GetString(reply.Body))["content"]!["sha"]!,
            409 or 422 => null,
            _ => throw new No("missing"),
        };
    }

    private static (int Status, byte[] Body, DateTime Date) Send(string method, string path, bool raw = false,
        byte[]? head = null, byte[]? content = null)
    {
        if (!System.Text.RegularExpressions.Regex.IsMatch(_repo, @"^(?!\.+/)(?!.*/\.+$)[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$")) {
            throw new No("missing");
        }

        try {
#pragma warning disable SYSLIB0014 // HttpWebRequest is what was seen working from the game's Mono
            var request = (HttpWebRequest)WebRequest.Create(_api + "/repos/" + _repo + path);
#pragma warning restore SYSLIB0014
            request.Method = method;
            request.UserAgent = "ElinTogether";
            request.Accept = raw ? "application/vnd.github.raw" : "application/vnd.github+json";
            request.Headers["Authorization"] = "Bearer " + _token;
            request.Headers["X-GitHub-Api-Version"] = "2022-11-28";
            // (a world gets a second more for every 50 KB)
            request.Timeout = request.ReadWriteTimeout = 30000 + (content?.Length ?? 0) / 50;
            // the key follows no redirection
            request.AllowAutoRedirect = false;
            if (head is not null && content is not null) {
                const int piece = 3 * 16384;
                request.ContentType = "application/json";
                request.ContentLength = head.Length + (content.Length + 2) / 3 * 4 + 2;
                using var to = request.GetRequestStream();
                to.Write(head, 0, head.Length);
                for (var at = 0; at < content.Length; at += piece) {
                    var text = Encoding.ASCII.GetBytes(Convert.ToBase64String(content, at, Math.Min(piece, content.Length - at)));
                    to.Write(text, 0, text.Length);
                }

                to.Write(Encoding.ASCII.GetBytes("\"}"), 0, 2);
            }

            HttpWebResponse response;
            try {
                response = (HttpWebResponse)request.GetResponse();
            } catch (WebException ex) when (ex.Response is HttpWebResponse refused) {
                response = refused;
            }

            using (response) {
                var status = (int)response.StatusCode;
                // (403 and 429 with these headers are GitHub asking to slow down, not a bad key)
                var slowDown = response.Headers["Retry-After"] is not null || response.Headers["X-RateLimit-Remaining"] == "0";
                if (status == 401 || (status == 403 && !slowDown)) {
                    throw new No("password");
                }

                // the repository was renamed or moved: the name is to be checked, as when it is not found
                if (status is 301 or 302 or 307 or 308) {
                    throw new No("missing");
                }

                if (status is not (200 or 201 or 404 or 409 or 422)) {
                    throw new IOException($"GitHub answered {status} to {method} {path}");
                }

                var date = DateTime.TryParse(response.Headers["Date"], CultureInfo.InvariantCulture,
                    DateTimeStyles.AdjustToUniversal | DateTimeStyles.AssumeUniversal, out var said)
                    ? said
                    : DateTime.UtcNow;
                // what is taken has the limit of what is sent
                using var body = new MemoryStream();
                using (var from = response.GetResponseStream()) {
                    var piece = new byte[81920];
                    for (var n = from.Read(piece, 0, piece.Length); n > 0; n = from.Read(piece, 0, piece.Length)) {
                        body.Write(piece, 0, n);
                        if (body.Length > MaxWorld) {
                            throw new No("too big");
                        }
                    }
                }

                return (status, body.ToArray(), date);
            }
        } catch (WebException ex) {
            // (the status only: nothing of the request, which carries the key, goes into a message)
            throw new IOException("GitHub does not answer: " + ex.Status);
        }
    }

    /// <summary>
    ///     modlist.txt next to the world: the mods of the game that first saved it, with their Workshop pages. It is
    ///     the list of the WORLD from then on (who hosts or joins plays with these mods): written when there is
    ///     none, never replaced by the game, changed by hand in the repository (one link a line). Never a reason
    ///     to fail: the world is saved already
    /// </summary>
    private static void WriteModList(string name)
    {
        if (ModListText is not { } text) {
            return;
        }

        try {
            var content = Encoding.UTF8.GetBytes(text());
            var reply = Send("GET", "/contents/");
            if (reply.Status != 200 ||
                JArray.Parse(Encoding.UTF8.GetString(reply.Body)).Any(file => (string?)file["name"] == "modlist.txt")) {
                return;
            }

            Thread.Sleep(_api.StartsWith("https") ? 1000 : 0);
            Write("modlist.txt", content, null, "mods of the world, from " + name);
        } catch (Exception) {
            // the next save tries again
        }
    }

    /// <summary>
    ///     The text of modlist.txt, given by the game (this file knows nothing of it). Null: no such file
    /// </summary>
    internal static Func<string>? ModListText { get; set; }

    /// <summary>
    ///     The name git, and so GitHub, gives to a file of these bytes
    /// </summary>
    private static string BlobSha(byte[] bytes)
    {
        using var sha1 = SHA1.Create();
        var head = Encoding.ASCII.GetBytes("blob " + bytes.Length + "\0");
        sha1.TransformBlock(head, 0, head.Length, null, 0);
        sha1.TransformFinalBlock(bytes, 0, bytes.Length);
        return BitConverter.ToString(sha1.Hash!).Replace("-", "").ToLowerInvariant();
    }

    private sealed class No : Exception
    {
        internal No(string why) : base(why)
        {
        }
    }
}
