// Elin Together Server : la petite application serveur d'Elin Together.
// Un seul fichier, compile par le compilateur C# livre avec Windows (dev/server/build.ps1) : rien a installer.
//
// Deux facons de servir un monde :
//  - "Sans Elin" (le depot) : l'application garde le monde (une archive) et dit qui l'heberge. Aucun jeu ne
//    tourne ici. Le premier joueur qui arrive prend le monde et l'heberge, les autres le rejoignent, chaque
//    sauvegarde revient ici. Cote jeu : ElinTogether/Helper/SaveDepot.cs, reglage "Depot folder" = adresse:port.
//  - "Avec Elin" : l'application lance Elin sur ce PC avec -empserver <sauvegarde> (sans fenetre si la case est
//    cochee), lit l'etat qu'il ecrit dans ElinMP/server.txt et l'arrete proprement en posant ElinMP/server.stop.
//    Cote jeu : ElinTogether/Emp/EmpServer.cs. Les joueurs rejoignent par adresse:55556.
//
// Ligne de commande (pour les tests) : --depot <dossier> [--port N] [--password X] [--import <sauvegarde>] demarre
// le depot tout de suite, avec cette sauvegarde comme monde.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Net;
using System.Net.NetworkInformation;
using System.Net.Sockets;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Windows.Forms;
using Microsoft.Win32;

/// <summary>Le depot : garde le monde et le verrou, repond aux jeux. Un fil par demande, un verrou pour tout.</summary>
internal sealed class Depot
{
    private const int MaxWorld = 300 * 1024 * 1024;
    private static readonly TimeSpan LockLife = TimeSpan.FromMinutes(3);

    private readonly object _gate = new object();
    private readonly string _folder;
    private readonly string _password;
    private readonly TcpListener _listener;
    private string _holderId;
    private DateTime _beat;

    public string HolderName { get; private set; }
    public DateTime Received { get; private set; }
    public string Last { get; private set; }

    public Depot(string folder, int port, string password)
    {
        _folder = folder;
        _password = password ?? "";
        Directory.CreateDirectory(folder);
        if (File.Exists(WorldFile)) {
            Received = File.GetLastWriteTime(WorldFile);
        }

        _listener = new TcpListener(IPAddress.Any, port);
        _listener.Start();
        new Thread(Accept) { IsBackground = true }.Start();
    }

    private string WorldFile
    {
        get { return Path.Combine(_folder, "world.zip"); }
    }

    public long WorldSize
    {
        get { return File.Exists(WorldFile) ? new FileInfo(WorldFile).Length : 0; }
    }

    /// <summary>Le joueur qui heberge le monde en ce moment, null si personne (ou si son signe de vie a expire).</summary>
    public string Holder
    {
        get { lock (_gate) { return _holderId != null && DateTime.UtcNow - _beat < LockLife ? HolderName : null; } }
    }

    public void Stop()
    {
        _listener.Stop();
    }

    private void Accept()
    {
        try {
            while (true) {
                var client = _listener.AcceptTcpClient();
                ThreadPool.QueueUserWorkItem(delegate { Serve(client); });
            }
        } catch (SocketException) {
            // arrete
        } catch (ObjectDisposedException) {
        }
    }

    private void Serve(TcpClient client)
    {
        try {
            using (client)
            using (var stream = client.GetStream()) {
                stream.ReadTimeout = stream.WriteTimeout = 60000;
                var password = ReadLine(stream);
                var command = ReadLine(stream);
                var id = ReadLine(stream);
                var name = ReadLine(stream);
                var length = int.Parse(ReadLine(stream));
                if (length < 0 || length > MaxWorld) {
                    Reply(stream, "NO too big", null);
                    return;
                }

                var body = new byte[length];
                for (var read = 0; read < length;) {
                    var n = stream.Read(body, read, length - read);
                    if (n <= 0) {
                        return;
                    }

                    read += n;
                }

                if (password != _password) {
                    Reply(stream, "NO password", null);
                    return;
                }

                byte[] answer;
                string status;
                lock (_gate) {
                    status = Handle(command, id, name, body, out answer);
                    Last = DateTime.Now.ToString("HH:mm:ss") + "  " + name + " : " + command + " -> " + status;
                }

                Reply(stream, status, answer);
            }
        } catch (Exception) {
            // une demande coupee ou mal formee : la suivante
        }
    }

    private string Handle(string command, string id, string name, byte[] body, out byte[] answer)
    {
        answer = null;
        var held = _holderId != null && DateTime.UtcNow - _beat < LockLife;
        var mine = held && _holderId == id;
        switch (command) {
            case "WHO":
                return "OK " + (held && !mine ? HolderName : "");
            case "TAKE":
                if (held && !mine) {
                    return "NO held " + HolderName;
                }

                if (!File.Exists(WorldFile)) {
                    return "NO empty";
                }

                answer = File.ReadAllBytes(WorldFile);
                Hold(id, name);
                return "OK";
            case "PUT":
                // le monde ne vient que de celui qui l'heberge, ou de n'importe qui tant que le depot est vide
                if (!mine && (held || File.Exists(WorldFile))) {
                    return "NO not the holder";
                }

                if (body.Length == 0) {
                    return "NO empty";
                }

                Store(body);
                if (mine) {
                    _beat = DateTime.UtcNow;
                }

                return "OK";
            case "BEAT":
                if (!held || mine) {
                    Hold(id, name);
                    return "OK";
                }

                return "NO held " + HolderName;
            case "RELEASE":
                if (mine) {
                    _holderId = null;
                }

                return "OK";
            default:
                return "NO unknown";
        }
    }

    private void Hold(string id, string name)
    {
        _holderId = id;
        HolderName = name;
        _beat = DateTime.UtcNow;
    }

    /// <summary>
    /// La sauvegarde choisie sur ce PC devient le monde du serveur : un dossier de sauvegarde (celui qui contient
    /// game.txt), une sauvegarde du nuage Steam (son cloud.zip) ou une archive. Renvoie null, ou ce qui l'empeche.
    /// </summary>
    public string Import(string path)
    {
        byte[] world;
        try {
            if (Directory.Exists(path) && !File.Exists(Path.Combine(path, "game.txt")) && File.Exists(Path.Combine(path, "cloud.zip"))) {
                path = Path.Combine(path, "cloud.zip");
            }

            if (File.Exists(path)) {
                world = File.ReadAllBytes(path);
            } else if (File.Exists(Path.Combine(path, "game.txt"))) {
                var packed = Path.Combine(_folder, "import.tmp");
                File.Delete(packed);
                ZipFile.CreateFromDirectory(path, packed);
                world = File.ReadAllBytes(packed);
                File.Delete(packed);
            } else {
                return "This is not an Elin save (no game.txt).";
            }

            using (var zip = new ZipArchive(new MemoryStream(world), ZipArchiveMode.Read)) {
                if (zip.GetEntry("game.txt") == null) {
                    return "This archive holds no Elin save (no game.txt).";
                }
            }
        } catch (Exception ex) {
            return ex.Message;
        }

        lock (_gate) {
            if (_holderId != null && DateTime.UtcNow - _beat < LockLife) {
                return HolderName + " is hosting the world right now: wait until they leave.";
            }

            Store(world);
            Last = DateTime.Now.ToString("HH:mm:ss") + "  save put on the server";
        }

        return null;
    }

    /// <summary>Ecrit a cote puis echange, et garde les trois mondes precedents (world.1.zip est le plus recent).</summary>
    private void Store(byte[] world)
    {
        var incoming = WorldFile + ".new";
        File.WriteAllBytes(incoming, world);
        if (File.Exists(WorldFile)) {
            for (var i = 3; i >= 1; i--) {
                var older = Path.Combine(_folder, "world." + i + ".zip");
                var newer = i == 1 ? WorldFile : Path.Combine(_folder, "world." + (i - 1) + ".zip");
                if (File.Exists(newer)) {
                    File.Delete(older);
                    File.Move(newer, older);
                }
            }
        }

        File.Move(incoming, WorldFile);
        Received = DateTime.Now;
    }

    private static void Reply(Stream stream, string status, byte[] body)
    {
        var head = Encoding.UTF8.GetBytes(status + "\n" + (body == null ? 0 : body.Length) + "\n");
        stream.Write(head, 0, head.Length);
        if (body != null) {
            stream.Write(body, 0, body.Length);
        }
    }

    private static string ReadLine(Stream stream)
    {
        var line = new MemoryStream();
        for (var b = stream.ReadByte(); b != '\n'; b = stream.ReadByte()) {
            if (b < 0 || line.Length > 4096) {
                throw new IOException("ligne incomplete");
            }

            line.WriteByte((byte)b);
        }

        return Encoding.UTF8.GetString(line.ToArray());
    }
}

internal sealed class ServerForm : Form
{
    private const int DepotPort = 55557;
    private static readonly string Data = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), @"AppData\LocalLow\Lafrontier\Elin");
    private static readonly string StatusFile = Path.Combine(Data, @"ElinMP\server.txt");
    private static readonly string StopFile = Path.Combine(Data, @"ElinMP\server.stop");

    private readonly RadioButton _noGame = new RadioButton { Text = "Without Elin: keeps the world, a player hosts it", AutoSize = true, Checked = true };
    private readonly RadioButton _withGame = new RadioButton { Text = "With Elin on this PC: the world runs all the time", AutoSize = true };
    private readonly Label _choice = new Label { AutoSize = true };
    private readonly ComboBox _saves = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList, Width = 330 };
    private readonly Button _browse = new Button { Text = "Browse…", Width = 90, Height = 26 };
    private readonly Button _import = new Button { Text = "Put this save on the server", Width = 232, Height = 26 };
    private readonly Label _passwordTitle = new Label { Text = "Password (empty: none):", AutoSize = true };
    private readonly TextBox _password = new TextBox { Width = 160 };
    private readonly CheckBox _hidden = new CheckBox { Text = "No game window (lighter)", AutoSize = true, Checked = true };
    private readonly Button _toggle = new Button { Text = "Start", Width = 120, Height = 30 };
    private readonly Label _state = new Label { AutoSize = true, Font = new Font("Segoe UI", 11f, FontStyle.Bold) };
    private readonly Label _info = new Label { AutoSize = true };
    private readonly Label _playersTitle = new Label { AutoSize = true };
    private readonly ListBox _players = new ListBox { Width = 330, Height = 64 };
    private readonly ListBox _addresses = new ListBox { Width = 330, Height = 64 };
    private readonly System.Windows.Forms.Timer _timer = new System.Windows.Forms.Timer { Interval = 2000 };
    private readonly string _elin = FindElin();
    private readonly string _depotFolder;
    private readonly int _depotPort = DepotPort;
    private Process _game;
    private Depot _depot;
    private DateTime _stopAsked;

    private ServerForm(string[] args)
    {
        Text = "Elin Together Server";
        Font = new Font("Segoe UI", 9f);
        FormBorderStyle = FormBorderStyle.FixedSingle;
        MaximizeBox = false;
        ClientSize = new Size(360, 596);
        _depotFolder = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), "ElinTogetherServer");

        var y = 12;
        Add(_noGame, ref y, 22);
        Add(_withGame, ref y, 28);
        Add(_choice, ref y, 20);
        Add(_saves, ref y, 30);
        Add(_browse, ref y, 0);
        Add(_import, ref y, 34);
        _import.Left = 112;
        Add(_passwordTitle, ref y, 0);
        Add(_password, ref y, 0);
        _password.Left = 184;
        Add(_hidden, ref y, 28);
        Add(_toggle, ref y, 40);
        Add(_state, ref y, 26);
        Add(_info, ref y, 54);
        Add(_playersTitle, ref y, 20);
        Add(_players, ref y, 72);
        Add(new Label { Text = "Addresses to give to the players (double-click to copy):", AutoSize = true }, ref y, 20);
        Add(_addresses, ref y, 70);
        Add(new Label { Text = "In the game: Elin Together panel, Lobby tab,\n\"Join by address\", and type one of these addresses.", AutoSize = true }, ref y, 34);

        foreach (var save in Saves()) {
            _saves.Items.Add(save);
        }

        if (_saves.Items.Count > 0) {
            _saves.SelectedIndex = 0;
        }

        _addresses.DoubleClick += delegate {
            if (_addresses.SelectedItem != null) {
                Clipboard.SetText(((string)_addresses.SelectedItem).Split(' ')[0]);
            }
        };
        _browse.Click += delegate {
            using (var pick = new FolderBrowserDialog { Description = "Folder of an Elin save (the one that holds game.txt)" }) {
                if (pick.ShowDialog(this) == DialogResult.OK) {
                    _saves.Items.Insert(0, pick.SelectedPath);
                    _saves.SelectedIndex = 0;
                }
            }
        };
        _import.Click += delegate {
            var problem = _depot.Import(SavePath((string)_saves.SelectedItem));
            MessageBox.Show(this, problem ?? "This save is now the world of the server.\nThe previous world is kept beside it (world.1.zip).", Text);
            Refresh();
        };
        _noGame.CheckedChanged += delegate { Refresh(); };
        _toggle.Click += delegate { if (Running) { Stop(); } else { Start(); } };
        _timer.Tick += delegate { Refresh(); };
        _timer.Start();
        FormClosing += OnClosing;

        string import = null;
        for (var i = 0; i + 1 < args.Length; i++) {
            if (args[i] == "--import") { import = args[i + 1]; }
            if (args[i] == "--depot") { _depotFolder = args[i + 1]; }
            if (args[i] == "--port") { _depotPort = int.Parse(args[i + 1]); }
            if (args[i] == "--password") { _password.Text = args[i + 1]; }
        }

        Refresh();
        if (args.Contains("--depot")) {
            Start();
            if (import != null && _depot != null) {
                _depot.Import(import);
            }
        }
    }

    private bool Running
    {
        get { return _depot != null || (_game != null && !_game.HasExited); }
    }

    private void Add(Control control, ref int y, int height)
    {
        control.Location = new Point(14, y);
        Controls.Add(control);
        y += height;
    }

    private void Start()
    {
        if (_noGame.Checked) {
            try {
                _depot = new Depot(_depotFolder, _depotPort, _password.Text);
            } catch (SocketException ex) {
                MessageBox.Show(this, "Port " + _depotPort + " is already in use on this PC.\n" + ex.Message, Text);
            }

            Refresh();
            return;
        }

        if (_elin == null) {
            MessageBox.Show(this, "Elin was not found on this PC.", Text);
            return;
        }

        if (_saves.SelectedItem == null) {
            MessageBox.Show(this, "No save found.", Text);
            return;
        }

        try {
            File.Delete(StatusFile);
            File.Delete(StopFile);
        } catch (IOException) {
        }

        var id = ((string)_saves.SelectedItem).Split(' ')[0];
        if (id.Contains("\\")) {
            MessageBox.Show(this, "With Elin, the save must be one of the game's saves on this PC.", Text);
            return;
        }

        var window = _hidden.Checked ? "-batchmode -nographics" : "-screen-fullscreen 0 -screen-width 1280 -screen-height 720";
        _game = Process.Start(new ProcessStartInfo(Path.Combine(_elin, "Elin.exe"), window + " -empserver " + id) {
            WorkingDirectory = _elin,
            UseShellExecute = false,
        });
        Refresh();
    }

    private void Stop()
    {
        if (_depot != null) {
            _depot.Stop();
            _depot = null;
            Refresh();
            return;
        }

        // le serveur sauvegarde puis se ferme ; s'il ne repond pas en 45 secondes, il est ferme d'office
        Directory.CreateDirectory(Path.GetDirectoryName(StopFile));
        File.WriteAllText(StopFile, "stop");
        _stopAsked = DateTime.Now;
        Refresh();
    }

    private new void Refresh()
    {
        var noGame = _noGame.Checked;
        _noGame.Enabled = _withGame.Enabled = !Running;
        _hidden.Visible = !noGame;
        _browse.Visible = _import.Visible = _passwordTitle.Visible = _password.Visible = noGame;
        _hidden.Enabled = _password.Enabled = !Running;
        // sans Elin, la sauvegarde se choisit serveur en marche ; avec Elin, avant de le demarrer
        _saves.Enabled = noGame || !Running;
        _import.Enabled = _depot != null && _saves.SelectedItem != null;
        _choice.Text = noGame ? "Save to put on the server:" : "Save to host (it must have a home base):";
        _toggle.Text = Running ? "Stop" : "Start";
        _playersTitle.Text = noGame ? "Player hosting the world right now:" : "Connected players:";
        ShowAddresses(noGame ? _depotPort : 55556);

        var names = new string[0];
        if (noGame) {
            var holder = _depot == null ? null : _depot.Holder;
            _state.Text = _depot == null ? "Stopped" : "Running";
            _state.ForeColor = _depot == null ? Color.Firebrick : Color.ForestGreen;
            _info.Text = _depot == null
                ? "The first player to arrive loads the world and hosts it;\nthe others join that player through Steam, as usual."
                : (_depot.WorldSize == 0
                      ? "No world yet: pick a save above, then\n\"Put this save on the server\"."
                      : "World: " + (_depot.WorldSize / 1024) + " KB, received " + _depot.Received.ToString("yyyy-MM-dd HH:mm")) +
                  "\n" + (_depot.Last ?? "");
            names = holder == null ? names : new[] { holder };
        } else {
            var status = new Dictionary<string, string>();
            try {
                if (Running && File.Exists(StatusFile)) {
                    foreach (var line in File.ReadAllLines(StatusFile)) {
                        var at = line.IndexOf('=');
                        if (at > 0) {
                            status[line.Substring(0, at)] = line.Substring(at + 1);
                        }
                    }
                }
            } catch (IOException) {
                return;
            }

            var stopping = Running && _stopAsked != DateTime.MinValue;
            if (stopping && (DateTime.Now - _stopAsked).TotalSeconds > 45) {
                _game.Kill();
            }

            if (!Running) {
                _stopAsked = DateTime.MinValue;
            }

            string state, date, saved, players;
            status.TryGetValue("state", out state);
            status.TryGetValue("date", out date);
            status.TryGetValue("saved", out saved);
            status.TryGetValue("players", out players);
            _state.Text = !Running ? "Stopped" : stopping ? "Stopping: saving…" : state == "running" ? "Running" : "Starting (one or two minutes)…";
            _state.ForeColor = !Running ? Color.Firebrick : state == "running" && !stopping ? Color.ForestGreen : Color.DarkOrange;
            _toggle.Enabled = !stopping;
            _info.Text = Running && state == "running"
                ? "World date: " + date + "\nLast save: " + (saved == "-" ? "not yet" : saved)
                : !Running ? "Elin must be installed on this PC. Every player joins the\nworld; nobody has to host it." : "";
            names = string.IsNullOrEmpty(players) ? names : players.Split('|');
        }

        if (!names.SequenceEqual(_players.Items.Cast<string>())) {
            _players.Items.Clear();
            _players.Items.AddRange(names);
        }
    }

    private void ShowAddresses(int port)
    {
        var addresses = NetworkInterface.GetAllNetworkInterfaces()
            .Where(n => n.OperationalStatus == OperationalStatus.Up)
            .SelectMany(n => n.GetIPProperties().UnicastAddresses)
            .Where(a => a.Address.AddressFamily == AddressFamily.InterNetwork)
            .Select(a => a.Address.ToString())
            .Where(a => !a.StartsWith("169.254."))
            .Distinct()
            .Select(ip => ip + ":" + port + (ip.StartsWith("127.") ? "   (from this PC only)" : ""))
            .ToArray();
        if (!addresses.SequenceEqual(_addresses.Items.Cast<string>())) {
            _addresses.Items.Clear();
            _addresses.Items.AddRange(addresses);
        }
    }

    private void OnClosing(object sender, FormClosingEventArgs e)
    {
        if (!Running || _depot != null) {
            return;
        }

        if (MessageBox.Show(this, "The server is running. Stop it (it saves first)?", Text, MessageBoxButtons.YesNo) == DialogResult.Yes
            && _stopAsked == DateTime.MinValue) {
            Stop();
        }

        e.Cancel = true;
    }

    /// <summary>Le dossier d'une entree de la liste : un chemin choisi par "Parcourir", ou une sauvegarde du jeu.</summary>
    private static string SavePath(string item)
    {
        if (Directory.Exists(item) || File.Exists(item)) {
            return item;
        }

        var id = item.Split(' ')[0];
        return id.StartsWith("cloud:") ? Path.Combine(Data, "Cloud Save", id.Substring(6)) : Path.Combine(Data, "Save", id);
    }

    /// <summary>Les sauvegardes locales et celles du nuage Steam, la derniere ecrite en premier.</summary>
    private static IEnumerable<string> Saves()
    {
        var found = new List<KeyValuePair<DateTime, string>>();
        foreach (var root in new[] { new[] { "Save", "" }, new[] { "Cloud Save", "cloud:" } }) {
            var dir = Path.Combine(Data, root[0]);
            if (!Directory.Exists(dir)) {
                continue;
            }

            foreach (var save in Directory.GetDirectories(dir)) {
                var file = new[] { "game.txt", "cloud.zip" }.Select(f => Path.Combine(save, f)).FirstOrDefault(File.Exists);
                if (file != null) {
                    var written = File.GetLastWriteTime(file);
                    found.Add(new KeyValuePair<DateTime, string>(written,
                        root[1] + Path.GetFileName(save) + "   (" + written.ToString("yyyy-MM-dd HH:mm") + ")"));
                }
            }
        }

        return found.OrderByDescending(f => f.Key).Select(f => f.Value);
    }

    /// <summary>Le dossier d'Elin, par le registre de Steam et ses bibliotheques (comme install.ps1).</summary>
    private static string FindElin()
    {
        var steams = new List<string>();
        foreach (var key in new[] { @"HKEY_CURRENT_USER\Software\Valve\Steam", @"HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Valve\Steam" }) {
            foreach (var name in new[] { "SteamPath", "InstallPath" }) {
                var value = Registry.GetValue(key, name, null) as string;
                if (value != null) {
                    steams.Add(value.Replace('/', '\\'));
                }
            }
        }

        steams.Add(@"C:\Program Files (x86)\Steam");
        var libraries = new List<string>();
        foreach (var steam in steams.Distinct()) {
            libraries.Add(steam);
            var vdf = Path.Combine(steam, @"steamapps\libraryfolders.vdf");
            if (File.Exists(vdf)) {
                libraries.AddRange(Regex.Matches(File.ReadAllText(vdf), "\"path\"\\s+\"([^\"]+)\"").Cast<Match>()
                    .Select(m => m.Groups[1].Value.Replace(@"\\", @"\")));
            }
        }

        return libraries.Distinct().Select(l => Path.Combine(l, @"steamapps\common\Elin"))
            .FirstOrDefault(e => File.Exists(Path.Combine(e, "Elin.exe")));
    }

    [STAThread]
    private static void Main(string[] args)
    {
        Application.EnableVisualStyles();
        Application.Run(new ServerForm(args));
    }
}
