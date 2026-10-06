using ElinTogether.Models;

namespace ElinTogether.Net;

internal partial class ElinNetClient
{
    private void RegisterWorldCopy()
    {
        Router.RegisterHandler<WorldCopyManifest>(OnWorldCopyOffer);
        Router.RegisterHandler<WorldCopyPiece>(OnWorldCopyPiece);
    }

    /// <summary>
    ///     Net event: the host saved, this is what its save holds
    /// </summary>
    private void OnWorldCopyOffer(WorldCopyManifest offer)
    {
        // the host of a zone session is another guest: the world is not its to hand out
        if (!IsZoneSession) {
            WorldCopyReceiver.Offer(offer);
        }
    }

    private void OnWorldCopyPiece(WorldCopyPiece piece)
    {
        if (!IsZoneSession) {
            WorldCopyReceiver.Piece(piece);
        }
    }
}
