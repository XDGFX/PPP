# EXAMPLE VARIABLES
# Rename to variables.py and fill out all required variables

# The url to your server; relative to PPP (may be localhost if running on the same machine as PPP)
# e.g. 192.168.1.96:32400
server_url = ''

# Where do I find this? Here: bit.ly/2p7RtOu
# e.g. P6X4rFdFhcTssbA6pXoT
plex_token = ''

# Path to your local playlists; relative to PPP on
# e.g. /mnt/Playlists
local_playlists = ''

# The path to this PPP install folder; relative to Plex (must be accessible by your Plex machine, but you can run this program on any machine on the network)
# e.g. /mnt/PPP
install_directory = ''

# The media section containing all your music (Google search 'find Plex section ID')
# e.g. 11
section_id = ''

# Use only if your local playlists and Plex playlists have different directories (e.g. if they are not from the same machine) and so have different paths at the start
# If your directories include backslashes (they probably will) you need to escape it with a second backslash... 'D:\' becomes 'D:\\'
# Leave blank ('') if your directories are the same
# e.g. \\\\uluru\\Uluru\\ or D:\\
local_prepend = ''
plex_prepend = ''

# NOTES: If you have used the Plex Playlist PUSH api in the past, existing playlists will be duplicated when running this program.
#        This is because the playlist .m3u files are located in a different place. Delete the old playlists from Plex and run PPP again.
#
#		 USE AT YOUR OWN RISK: I TAKE NO RESPONSIBILITY IF YOU BREAK SOMETHING AND YOU DON'T HAVE BACKUPS!
