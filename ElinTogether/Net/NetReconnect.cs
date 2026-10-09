using System;
using System.Collections;
using UnityEngine;

namespace ElinTogether.Net;

/// <summary>
///     A guest whose link with the host dropped by itself joins the same game again by itself, with a notice on
///     screen the player can cancel. Lives outside the connection component, which dies with the link
/// </summary>
internal static class NetReconnect
{
    private const float RetrySeconds = 5f;
    private const float GiveUpSeconds = 180f;

    private static Coroutine? _routine;
    private static Dialog? _notice;

    internal static bool Active => _routine is not null;

    /// <summary>
    ///     To call before the session is reset: where the game was is read from the connection going away
    /// </summary>
    internal static void Begin()
    {
        var session = NetSession.Instance;

        // only for a player who was in the game: a join that fails is not a link lost
        if (Active || WorldTakeover.Busy || !session.Rules.AllowReconnect || !EClass.core.IsGameStarted ||
            session.Transport is not ElinNetClient { IsZoneSession: false } client ||
            client.Rejoin is not { } rejoin) {
            return;
        }

        EmpLog.Information("Link with the host lost, joining the same game again");

        _routine = EmpMod.Instance.StartCoroutine(Retry(rejoin));
    }

    /// <summary>
    ///     No more attempts, the one under way is left alone
    /// </summary>
    internal static void Stop()
    {
        if (_routine is not null) {
            EmpMod.Instance.StopCoroutine(_routine);
        }

        Clear();
    }

    private static void Clear()
    {
        _routine = null;

        var notice = _notice;
        _notice = null;
        if (notice != null) {
            notice.Close();
        }
    }

    private static IEnumerator Retry(Action rejoin)
    {
        var session = NetSession.Instance;
        var giveUp = Time.realtimeSinceStartup + GiveUpSeconds;
        var tried = float.MinValue;
        var back = false;

        // whatever happens in here, no notice left on screen and nothing left that reads as still trying
        try {
            // the caller resets the session right after Begin: the title screen is up on the next frame
            yield return null;

            ShowNotice();

            // a hard end: a join that connects but never loads the world counts in the same time
            while (Time.realtimeSinceStartup < giveUp) {
                yield return null;

                // back in the game, or the player started something else
                if (EClass.core.IsGameStarted || session.Transport is ElinNetHost) {
                    back = true;
                    yield break;
                }

                var now = Time.realtimeSinceStartup;
                if (now - tried < RetrySeconds) {
                    continue;
                }

                if (session.Transport is ElinNetClient client) {
                    // connected: the join is under way. Through a lobby nothing is connected yet while Steam
                    // lets us in and the key is handed over: that attempt gets the time of any request
                    var direct = client.IsLocalConnection || client.IsDirectConnection;
                    if (client.IsConnected || (!direct && now - tried < EmpConfig.Policy.Timeout.Value)) {
                        continue;
                    }

                    // the component closes its link at the end of the frame, which resets the session once more
                    session.ResetSession();
                    yield return null;
                }

                tried = Time.realtimeSinceStartup;
                Attempt(rejoin);
            }
        } finally {
            Clear();
        }

        if (back) {
            yield break;
        }

        EmpLog.Information("Gave up joining the game again after {Seconds}s", GiveUpSeconds);

        session.ResetSession();
        Dialog.Ok("emp_ui_reconnect_failed");
    }

    private static void Attempt(Action rejoin)
    {
        try {
            rejoin();
        } catch (Exception ex) {
            EmpLog.Warning(ex, "Could not start joining the game again");
            // noexcept
        }
    }

    private static void ShowNotice()
    {
        var cancel = false;
        var notice = _notice = Dialog.Choice("emp_ui_reconnecting",
            d => d.AddButton("emp_ui_reconnect_cancel".lang(), () => cancel = true));
        notice.SetOnKill(() => {
            // closed by Clear
            if (!ReferenceEquals(_notice, notice)) {
                return;
            }

            // closed by the player, a way out. Closed by anything else once the game answers again
            // (the world loading): the join goes on
            _notice = null;
            if (cancel || NetSession.Instance.Transport is not ElinNetClient { IsConnected: true }) {
                EmpLog.Information("Player gave up joining the game again");
                Stop();
                NetSession.Instance.ResetSession();
            }
        });
    }
}
