// One player of the GitHub depot, without the game: GitHubDepot.Ask behind a command line.
//     github_depot_cli <owner/repository> <id> <name> [where its game is joined]
//                                                           (key: DEPOT_TOKEN; address: ELINTOGETHER_GITHUB_API)
// One request per line read: WHO | TAKE <file to write> | PUT <file to send> [version it descends from] | BEAT | RELEASE,
// MODS <file to write> (modlist.txt of the depot as it is there; the answer is its length),
// or JOIN (no request: where the holder last read is joined), or PARSE <file> (no request: the mods ModListFile
// reads in that text, "Workshop number;id;title" each).
// One answer per line written: "OK text", "NO text", or "ERR type: message" when GitHub does not answer.
using System;
using System.IO;
using System.Linq;
using ElinTogether.Helper;

Console.OutputEncoding = System.Text.Encoding.UTF8;
var token = Environment.GetEnvironmentVariable("DEPOT_TOKEN") ?? "";
// the game gives the text of modlist.txt; here the test does
if (Environment.GetEnvironmentVariable("DEPOT_MODLIST") is { Length: > 0 } mods) {
    GitHubDepot.ModListText = () => mods;
}
for (var line = Console.ReadLine(); line is not null; line = Console.ReadLine()) {
    var words = line.Split(' ');
    try {
        if (words[0] == "JOIN") {
            Console.WriteLine("OK " + GitHubDepot.HeldJoin);
            continue;
        }

        if (words[0] == "PARSE") {
            Console.WriteLine("OK " + string.Join(" | ", ModListFile.Parse(File.ReadAllText(words[1]))
                .Select(m => $"{m.Workshop};{m.Id};{m.Title}")));
            continue;
        }

        var reply = GitHubDepot.Ask(args[0], token, words[0], args[1], args[2],
            words[0] == "PUT" ? File.ReadAllBytes(words[1]) : null, words.Length > 2 ? words[2] : null, args.Length > 3 ? args[3] : null);
        if (reply.Body is not null) {
            File.WriteAllBytes(words[1], reply.Body);
        }

        if (words[0] == "MODS" && reply.Ok) {
            File.WriteAllText(words[1], reply.Text);
            Console.WriteLine("OK " + reply.Text.Length);
            continue;
        }

        Console.WriteLine((reply.Ok ? "OK " : "NO ") + reply.Text);
    } catch (Exception ex) {
        // all of it, as a log would keep it: the test looks for the key in there
        Console.WriteLine("ERR " + ex.ToString().Replace("\r", "").Replace("\n", " | "));
    }
}
