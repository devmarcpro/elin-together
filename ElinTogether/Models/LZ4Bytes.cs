using System.IO;
using System.IO.Compression;
using System.Text;
using LZ4;
using MessagePack;
using Newtonsoft.Json;

namespace ElinTogether.Models;

[MessagePackObject]
public class LZ4Bytes
{
    private static readonly JsonSerializer _serializer = JsonSerializer.Create(GameIOContext.Settings);
    public static LZ4Bytes Empty => field ??= new() { Bytes = [] };

    [Key(0)]
    public required byte[] Bytes { get; init; }

    public static LZ4Bytes Create<T>(T data)
    {
        using var ms = new MemoryStream();
        using var lz4 = new LZ4Stream(ms, CompressionMode.Compress);
        using var sw = new StreamWriter(lz4, Encoding.UTF8);
        using var jw = new JsonTextWriter(sw);

        _serializer.Serialize(jw, data, typeof(T));
        jw.Flush();
        sw.Flush();
        lz4.Flush();

        return new() {
            Bytes = ms.ToArray(),
        };
    }

    /// <summary>
    ///     The same text as <see cref="Create{T}" /> compresses, to compare cheaply
    /// </summary>
    public static string ToJson<T>(T data)
    {
        using var sw = new StringWriter();
        using var jw = new JsonTextWriter(sw);
        _serializer.Serialize(jw, data, typeof(T));
        jw.Flush();
        return sw.ToString();
    }

    public static LZ4Bytes CreateFromFile(string filePath)
    {
        using var input = File.Open(filePath, FileMode.Open, FileAccess.Read, FileShare.ReadWrite);
        using var ms = new MemoryStream();
        // fast mode: map files go out every checkpoint and to every joining player, high compression froze the game
        // the flag is stored in the stream header, so Decompress reads either form
        using var lz4 = new LZ4Stream(ms, CompressionMode.Compress);

        input.CopyTo(lz4);
        lz4.Flush();

        return new() {
            Bytes = ms.ToArray(),
        };
    }

    public static LZ4Bytes CreateFromBytes(byte[] input)
    {
        using var ms = new MemoryStream();
        using var lz4 = new LZ4Stream(ms, CompressionMode.Compress, LZ4StreamFlags.HighCompression);

        lz4.Write(input, 0, input.Length);
        lz4.Flush();

        return new() {
            Bytes = ms.ToArray(),
        };
    }

    public T Decompress<T>()
    {
        using var input = new MemoryStream(Bytes);
        using var lz4 = new LZ4Stream(input, CompressionMode.Decompress);
        using var sr = new StreamReader(lz4, Encoding.UTF8);
        using var jr = new JsonTextReader(sr);

        return _serializer.Deserialize<T>(jr)!;
    }

    public string DecompressToString()
    {
        using var input = new MemoryStream(Bytes);
        using var lz4 = new LZ4Stream(input, CompressionMode.Decompress);
        using var sr = new StreamReader(lz4, Encoding.UTF8);

        return sr.ReadToEnd();
    }

    public byte[] DecompressToBytes()
    {
        using var input = new MemoryStream(Bytes);
        using var lz4 = new LZ4Stream(input, CompressionMode.Decompress);
        using var ms = new MemoryStream();

        lz4.CopyTo(ms);

        return ms.ToArray();
    }

    public void DecompressToStream(Stream output)
    {
        using var input = new MemoryStream(Bytes);
        using var lz4 = new LZ4Stream(input, CompressionMode.Decompress);

        lz4.CopyTo(output);
    }

    public void DecompressToFile(string filePath)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(filePath)!);
        using var fs = File.Create(filePath);

        DecompressToStream(fs);
    }
}