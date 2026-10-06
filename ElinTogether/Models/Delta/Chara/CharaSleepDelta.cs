using System.Collections.Generic;
using System.Linq;
using ElinTogether.Net;
using ElinTogether.Patches;
using MessagePack;

namespace ElinTogether.Models;

[MessagePackObject]
public class CharaSleepDelta : ElinDelta
{
    private static bool _waking;
    private static bool? _dream;

    [Key(0)]
    public required int Power { get; init; }

    [Key(1)]
    public required int Days { get; init; }

    /// <summary>
    ///     Guest -> host, once awake: uid, charges left and read (1) or not (0), for each book of its grimoire that
    ///     its own wake-up went through (the host keeps the books, as for any reading)
    /// </summary>
    [Key(2)]
    public int[]? Books { get; init; }

    /// <summary>
    ///     Guest -> host, once awake: the recipe of its own night, for everyone as any recipe
    /// </summary>
    [Key(3)]
    public string? Recipe { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        if (net is ElinNetHost host) {
            OnGuestAwake(host);
            return;
        }

        if (pc.isDead) {
            return;
        }

        EmpLog.Debug("Applying host sleep {SleepPower}", Power);

        var bed = SleepSynchronizationContext.TakeBed();
        try {
            if (pc.conSleep is { } sleep) {
                WakeUp(net, sleep, bed);
            } else {
                using var _ = Simulate();
                pc.OnSleep(Power, Days, pc.pos.IsSunLit);
                player.DreamSpell();
            }
        } finally {
            SleepSynchronizationContext.CloseSleepLayerIfOpen();
        }
    }

    /// <summary>
    ///     The recipe of the night, in the wake-up this player plays for itself: learnt as its own act it would
    ///     go to the host as any recipe and come back from there, twice for this player. Drawn once the wake-up
    ///     is over, see <see cref="WakeUp" />
    /// </summary>
    internal static bool DeferRecipe(bool ehekatl)
    {
        if (!_waking) {
            return false;
        }

        _dream = ehekatl;
        return true;
    }

    /// <summary>
    ///     This player wakes as one alone would: the power of its own bed (LayerSleep.Advance), then the game's
    ///     own end of the sleep (ConSleep.OnRemoved): its grimoire, a recipe, a dream spell, its pillow, its karma
    /// </summary>
    private void WakeUp(ElinNetBase net, ConSleep sleep, Thing? bed)
    {
        var books = pc.things.Find<TraitGrimoire>()?.things.List(b => b.trait is TraitBaseSpellbook)
            .Select(b => (Book: b, Charges: b.c_charges, Read: b.isOn)).ToList() ?? [];

        _dream = null;
        _waking = true;
        try {
            using var _ = Simulate();
            pc.OnSleep(bed, Days);
            sleep.slept = true;
            sleep.Kill();
        } finally {
            _waking = false;
        }

        string? recipe = null;
        if (_dream is { } ehekatl) {
            var known = new Dictionary<string, int>(player.recipes.knownRecipes);
            player.recipes.OnSleep(ehekatl);
            Rand.SetSeed();

            // one recipe, and the variants the game learns with it (pillar, bridge): the shortest id brings them
            recipe = player.recipes.knownRecipes
                .Where(r => !known.TryGetValue(r.Key, out var count) || count != r.Value)
                .Select(r => r.Key)
                .OrderBy(id => id.Length)
                .FirstOrDefault();
        }

        var read = books.Where(b => b.Book.c_charges != b.Charges || b.Book.isOn != b.Read)
            .SelectMany(b => new[] { b.Book.uid, b.Book.c_charges, b.Book.isOn ? 1 : 0 })
            .ToArray();
        if (read.Length == 0 && recipe is null) {
            return;
        }

        net.Delta.AddRemote(new CharaSleepDelta {
            Power = Power,
            Days = Days,
            Books = read,
            Recipe = recipe,
        });
    }

    private void OnGuestAwake(ElinNetHost host)
    {
        if (!host.ActiveRemoteCharas.TryGetValue(OriginPeer, out var sender)) {
            return;
        }

        // only its own books, only fewer charges
        for (var i = 0; Books is not null && i + 2 < Books.Length; i += 3) {
            var left = Books[i + 1];
            if (CardCache.Find(Books[i]) is not Thing { isDestroyed: false, trait: TraitBaseSpellbook } book ||
                book.GetRootCard() != sender || left < 0 || left > book.c_charges) {
                continue;
            }

            if (Books[i + 2] != 0) {
                book.isOn = true;
            }

            if (left < book.c_charges) {
                book.ModCharge(left - book.c_charges);
                if (left == 0) {
                    book.ModNum(-1);
                }
            }
        }

        if (Recipe is null) {
            return;
        }

        // learnt here, and by the other guests as any recipe: the sender has it already
        player.recipes.Add(Recipe, !player.recipes.IsKnown(Recipe));
        host.SendDeltaToAllExcept(OriginPeer, new AddRecipeDelta {
            RecipeId = Recipe,
        });
    }
}
