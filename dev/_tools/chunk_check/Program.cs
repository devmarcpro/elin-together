// NetFragments without the game: dotnet run --project dev/_tools/chunk_check
// One line per check, "OK" or "FAIL"; exit code 1 when one fails.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using ElinTogether.Net;

var failed = 0;
var random = new Random(20261006);

void Check(string what, bool ok)
{
    Console.WriteLine((ok ? "OK   " : "FAIL ") + what);
    if (!ok) {
        failed++;
    }
}

byte[] Message(int size)
{
    var bytes = new byte[size];
    random.NextBytes(bytes);
    // a whole message starts with its type hash, never with the magic
    bytes[0] = 0;
    return bytes;
}

bool Throws(Action action)
{
    try {
        action();
        return false;
    } catch (InvalidDataException) {
        return true;
    }
}

// what SteamNetManager.Poll does with each message of one connection
List<byte[]> Receive(NetFragmentAssembler assembler, IEnumerable<byte[]> wire)
{
    var got = new List<byte[]>();
    foreach (var bytes in wire) {
        if (!NetFragments.IsFragment(bytes)) {
            got.Add(bytes);
        } else if (assembler.Add(bytes) is { } whole) {
            got.Add(whole);
        }
    }

    return got;
}

const int piece = NetFragments.PieceSize;

// sizes around the edges, up to a 5 MB world
foreach (var size in new[] { piece + 1, 2 * piece - 1, 2 * piece, 2 * piece + 1, 600_000, 5_000_000 }) {
    var message = Message(size);
    var pieces = NetFragments.Split(message, 7);
    var got = Receive(new(), pieces);

    Check($"{size} bytes: {pieces.Count} pieces, back whole",
        pieces.Count == (size + piece - 1) / piece
        && pieces.All(p => p.Length <= piece + NetFragments.HeaderSize && NetFragments.IsFragment(p))
        && got.Count == 1 && got[0].SequenceEqual(message));
}

// two big messages in a row with small ones around and between, as one connection carries them
{
    var small1 = Message(300);
    var big1 = Message(700_000);
    var small2 = Message(piece);
    var big2 = Message(1_300_000);
    var small3 = Message(12);

    var wire = new List<byte[]> { small1 };
    wire.AddRange(NetFragments.Split(big1, 1));
    wire.Add(small2);
    wire.AddRange(NetFragments.Split(big2, 2));
    wire.Add(small3);

    var assembler = new NetFragmentAssembler();
    var got = Receive(assembler, wire);
    var expected = new[] { small1, big1, small2, big2, small3 };

    Check("two big messages and three small ones, same order, same bytes",
        got.Count == expected.Length && got.Zip(expected).All(p => p.First.SequenceEqual(p.Second)) && !assembler.IsPending);
}

// an unreliable message is not a piece: it passes between two pieces without touching the one being gathered
{
    var big = Message(400_000);
    var pieces = NetFragments.Split(big, 3);
    var loose = Message(64);

    var wire = new List<byte[]>(pieces);
    wire.Insert(2, loose);

    var got = Receive(new(), wire);
    Check("a small message between two pieces", got.Count == 2 && got[0].SequenceEqual(loose) && got[1].SequenceEqual(big));
}

// the sender left in the middle: a new assembler (a new peer) starts clean, the old one keeps nothing after Reset
{
    var pieces = NetFragments.Split(Message(500_000), 4);
    var assembler = new NetFragmentAssembler();
    assembler.Add(pieces[0]);
    assembler.Add(pieces[1]);
    var pending = assembler.IsPending;
    assembler.Reset();

    var next = Message(300_000);
    var got = Receive(assembler, NetFragments.Split(next, 0));
    Check("a message cut short, then a whole one", pending && got.Count == 1 && got[0].SequenceEqual(next));
}

// a message that starts before the previous one ended: the previous one is given up, the new one arrives
{
    var first = NetFragments.Split(Message(500_000), 5);
    var second = Message(300_000);
    var assembler = new NetFragmentAssembler();
    assembler.Add(first[0]);

    var got = Receive(assembler, NetFragments.Split(second, 6));
    Check("a message started over another",
        got.Count == 1 && got[0].SequenceEqual(second) && assembler.InterruptedMessages == 1);
}

// pieces that do not fit are refused and leave nothing behind
{
    var pieces = NetFragments.Split(Message(500_000), 8);
    var other = NetFragments.Split(Message(500_000), 9);

    var assembler = new NetFragmentAssembler();
    Check("a piece without a first one", Throws(() => assembler.Add(pieces[1])) && !assembler.IsPending);

    assembler.Add(pieces[0]);
    Check("a piece skipped", Throws(() => assembler.Add(pieces[2])) && !assembler.IsPending);

    assembler.Add(pieces[0]);
    Check("a piece twice", assembler.Add(pieces[1]) is null && Throws(() => assembler.Add(pieces[1])) && !assembler.IsPending);

    assembler.Add(pieces[0]);
    Check("a piece of another message", Throws(() => assembler.Add(other[1])) && !assembler.IsPending);

    assembler.Add(pieces[0]);
    var shortPiece = pieces[1].Take(pieces[1].Length - 10).ToArray();
    assembler.Add(shortPiece);
    assembler.Add(pieces[2]);
    Check("a piece too short: the last one does not end the message", Throws(() => assembler.Add(pieces[3])) && !assembler.IsPending);

    assembler.Add(pieces[0]);
    var longPiece = pieces[3].Concat(new byte[10]).ToArray();
    assembler.Add(pieces[1]);
    assembler.Add(pieces[2]);
    Check("a last piece too long", Throws(() => assembler.Add(longPiece)) && !assembler.IsPending);

    Check("the whole message still passes after all that", Receive(assembler, pieces).Count == 1);
}

// a header that lies about the size reserves nothing
{
    byte[] Header(int count, int total)
    {
        var header = NetFragments.Split(new byte[2], 1, 1)[0];
        BitConverter.GetBytes(count).CopyTo(header, 12);
        BitConverter.GetBytes(total).CopyTo(header, 16);
        return header;
    }

    var assembler = new NetFragmentAssembler();
    var before = GC.GetTotalMemory(true);
    var refused = Throws(() => assembler.Add(Header(2, NetFragments.MaxMessageSize + 1)))
                  && Throws(() => assembler.Add(Header(2, int.MaxValue)))
                  && Throws(() => assembler.Add(Header(2, -5)))
                  && Throws(() => assembler.Add(Header(0, 100)))
                  && Throws(() => assembler.Add(Header(-1, 100)))
                  && Throws(() => assembler.Add(Header(200, 100)));
    var after = GC.GetTotalMemory(true);

    Check("a size over the limit, negative, or without pieces", refused && !assembler.IsPending && after - before < 1_000_000);
    Check("not a piece at all", Throws(() => assembler.Add(new byte[40])) && !NetFragments.IsFragment(new byte[3]));
}

// the biggest message accepted
{
    var message = Message(NetFragments.MaxMessageSize);
    var got = Receive(new(), NetFragments.Split(message, 10));
    Check($"{NetFragments.MaxMessageSize} bytes, the limit", got.Count == 1 && got[0].SequenceEqual(message));
}

Console.WriteLine(failed == 0 ? "ALL OK" : $"{failed} FAILED");
return failed == 0 ? 0 : 1;
