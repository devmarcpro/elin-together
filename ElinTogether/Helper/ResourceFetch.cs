using System.IO;
using UnityEngine;

namespace ElinTogether.Helper;

internal class ResourceFetch
{
    internal static readonly GameIOContext Context = GameIOContext.GetPersistentModContext("ElinMP")!;

    internal static string TempFolder { get; private set; } = Path.Combine(Application.persistentDataPath, "ElinMP/Temp");

    internal static void SetTempFolder(string path)
    {
        TempFolder = path;
        EmpPop.PopupInternal("emp_temp_folder_path".lang(), path);
    }

    /// <summary>
    ///     Save id of the world a client replicates from its host
    /// </summary>
    internal static string EmpSaveId =>
#if DEBUG
        // test instances on one machine share the save folder, each keeps its own copy
        EmpConfig.Dev.Identity.Value > 0 ? $"world_emp_{EmpConfig.Dev.Identity.Value}" : "world_emp";
#else
        "world_emp";
#endif

    internal static string GetEmpSavePath()
    {
        var tempSave = Path.Combine(CorePath.RootSave, EmpSaveId);
        return tempSave;
    }

    internal static void InvalidateTemp()
    {
        if (Directory.Exists(TempFolder)) {
            try {
                Directory.Delete(TempFolder, true);
            } catch {
                // noexcept
            }
        }

        var tempSave = GetEmpSavePath();
        if (Directory.Exists(tempSave)) {
            try {
                Directory.Delete(tempSave, true);
            } catch {
                // noexcept
            }
        }

        EmpLog.Verbose("Cleared temp folder");
    }
}