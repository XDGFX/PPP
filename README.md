# PPP (Bash version)
Plex Playlist Pusher
https://github.com/XDGFX/PPP for Python re-write

Some simple bash scripts used to automatically:
- take .m3u files from a location (maybe your MusicBee Library)
- move them to another location (temporary for Plex)
- replace characters if needed (the m3u path must be relative to the server machine, so if your playlist making computer and plex computer are different, you likely need this)
- push the playlists to Plex using the Plex Playlist API (https://forums.plex.tv/t/can-plexamp-read-and-use-m3u-playlists/234179/21)

Disclaimer: I am completely new to bash / Linux in general so these scripts are probably terrible / inefficient / wrong or all of the above. My use case is that this script runs on an Ubuntu Server VM on the same network as my Plex Server, but they're different machines. Advice is welcome!

How to use: 
1. Edit variables.sh to reflect your own variables (pay attention to the example naming schemes)
2. Edit diredit_playlists.sh if you need it OR remove the line from update_playlists.sh if you don't
3. Run update_playlists.sh
4. Work out why it didn't work (probably)
