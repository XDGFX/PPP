# Copies playlists from one directory to a folder, as long as the file is a .m3u
source variables.sh

rm -f $plex_playlists/* && cd $playlists && find -iname '*.m3u' -exec cp -prv {} "$plex_playlists" ";"

