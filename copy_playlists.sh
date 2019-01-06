# Copies playlists from one directory to a folder, as long as the file is a .m3u
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $SCRIPTDIR/variables.sh;

rm -f $plex_playlists/* && cd $playlists && find -iname '*.m3u' -exec cp -prv {} "$plex_playlists" ";"

