SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $SCRIPTDIR/variables.sh;

cd $plex_playlists && sed -i 's|\\\\server\\Uluru|D:|g' *
# This many backslashes are needed to 'escape' each initial backslash. The things to change here are:
# '\\\\server\\Uluru' is the path you want to remove from the .m3u text
# ... to replace it with 'D:'
