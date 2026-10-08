#!/bin/bash
# Installe le mod ElinTogether (version "independance") dans un Elin qui tourne sur Mac par CrossOver, Whisky ou Wine.
# Ne modifie que : Elin/Package/Mod_ElinTogether et Elin/loadorder.txt (sauvegardes dans Elin/_ElinTogether_sauvegarde).
# Desinstaller : relancer avec le mot "retirer" :  bash Installer-Mac.command retirer
MOD_ID='dk.elinplugins.elintogether'
YK='3400020753'
cd "$(dirname "$0")" || exit 1

echo
echo "=== ElinTogether (version independance) pour Mac ==="
echo

if [ ! -f "Mod_ElinTogether/ElinTogether.dll" ]; then
    echo "Le dossier Mod_ElinTogether est introuvable a cote de ce fichier : dezippe tout le dossier d'abord."
    exit 1
fi

if pgrep -f 'Elin\.exe' >/dev/null 2>&1; then
    echo "Elin est ouvert : ferme le jeu puis relance l'installateur."
    exit 1
fi

elin=''
for root in "$HOME/Library/Application Support/CrossOver/Bottles" \
            "$HOME/Library/Containers/com.isaacmarovitz.Whisky/Bottles" \
            "$HOME/Library/Application Support/Whisky" \
            "$HOME/Library/Application Support/Kegworks" \
            "$HOME/Applications" "$HOME/Games" "$HOME/.wine" "/Volumes"; do
    [ -d "$root" ] || continue
    found=$(find "$root" -maxdepth 14 -type f -name 'Elin.exe' -path '*steamapps/common/Elin/Elin.exe' 2>/dev/null | head -n 1)
    if [ -n "$found" ]; then
        elin=$(dirname "$found")
        break
    fi
done

if [ -z "$elin" ]; then
    echo "Elin n'a pas ete trouve automatiquement."
    echo "Fais glisser ici le dossier d'Elin (celui qui contient Elin.exe), puis appuie sur Entree :"
    read -r typed
    # un dossier glisse dans le Terminal arrive avec des \ devant les espaces
    elin=$(printf '%s' "$typed" | sed 's/\\\(.\)/\1/g; s/^ *//; s/ *$//; s/^"//; s/"$//; s/^'"'"'//; s/'"'"'$//')
    elin=${elin%/}
    if [ ! -f "$elin/Elin.exe" ]; then
        echo "Elin.exe est introuvable dans ce dossier. Rien n'a ete change."
        exit 1
    fi
fi
echo "Elin trouve : $elin"

dest="$elin/Package/Mod_ElinTogether"
backup="$elin/_ElinTogether_sauvegarde"
stamp=$(date +%Y%m%d-%H%M%S)
order="$elin/loadorder.txt"

# le meme dossier, comme le jeu l'ecrit dans sa liste (chemin Windows de la bouteille)
case "$elin" in
    */drive_c/*) win="C:\\$(printf '%s' "${elin#*/drive_c/}" | tr '/' '\\')\\Package\\Mod_ElinTogether" ;;
    *) win='' ;;
esac

# $1 : 1 = cette version allumee et les autres copies du mod eteintes ; 0 = l'inverse
set_order() {
    [ -f "$order" ] || return 1
    [ -n "$win" ] || return 1
    mkdir -p "$backup" && cp "$order" "$backup/loadorder-$stamp.txt"
    DEST="$win" ID="$MOD_ID" ON="$1" awk '
        BEGIN { dest = ENVIRON["DEST"]; id = ENVIRON["ID"]; on = ENVIRON["ON"]; n = length(id) + 3; found = 0 }
        { sub(/\r$/, "") }
        length($0) > n && (substr($0, length($0) - n + 1) == ",0," id || substr($0, length($0) - n + 1) == ",1," id) {
            path = substr($0, 1, length($0) - n)
            if (tolower(path) == tolower(dest)) { found = 1; if (on == 1) print dest ",1," id; next }
            print path "," (on == 1 ? 0 : 1) "," id
            next
        }
        { print }
        END { if (!found && on == 1) print dest ",1," id }
    ' "$backup/loadorder-$stamp.txt" > "$order.tmp" && mv "$order.tmp" "$order"
}

if [ "$1" = "retirer" ]; then
    if [ -d "$dest" ]; then
        mkdir -p "$backup" && mv "$dest" "$backup/Mod_ElinTogether-$stamp"
        echo "Mod retire (mis de cote dans $backup)."
    else
        echo "Cette version n'etait pas installee."
    fi
    set_order 0 && echo "Liste des mods : la version du Workshop est reactivee."
    exit 0
fi

library=$(dirname "$(dirname "$(dirname "$elin")")")
if [ ! -d "$library/steamapps/workshop/content/2135150/$YK" ]; then
    echo
    echo "Il manque le mod \"YK Framework\", dont ElinTogether a besoin."
    echo "Abonne-toi sur le Workshop Steam, laisse Steam le telecharger, puis relance cet installateur :"
    echo "  https://steamcommunity.com/sharedfiles/filedetails/?id=$YK"
    exit 1
fi

if [ -d "$dest" ]; then
    mkdir -p "$backup" && mv "$dest" "$backup/Mod_ElinTogether-$stamp" || exit 1
    echo "Ancienne version mise de cote."
fi
mkdir -p "$elin/Package" && cp -R "Mod_ElinTogether" "$dest" || { echo "La copie a echoue. Rien d'autre n'a ete change."; exit 1; }
echo "Mod copie dans Elin/Package/Mod_ElinTogether."

if set_order 1; then
    echo "Liste des mods mise a jour (cette version allumee, version du Workshop eteinte)."
elif [ ! -f "$order" ]; then
    echo "La liste des mods (loadorder.txt) n'existe pas encore : lance Elin une fois, quitte, puis relance cet installateur."
else
    echo "Ce dossier n'est pas dans une bouteille Wine (pas de drive_c) : la liste des mods n'a pas ete touchee."
    echo "Dans Elin, ouvre la liste des mods et eteins la version du Workshop d'Elin Together s'il y en a une."
fi

echo
echo "Installation terminee. Lance Elin comme d'habitude : le bouton Elin Together est sur l'ecran titre."
echo "Si ce bouton n'apparait pas, aucun mod ne se charge : dans les reglages de la bouteille (Wine Configuration,"
echo "onglet Libraries), ajoute \"winhttp\" en \"native, builtin\", puis relance Elin."
echo "Tous les joueurs doivent avoir la meme version de ce mod et d'Elin (canal Nightly)."
