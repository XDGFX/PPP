# Uses the Plex Playlist API to add your .m3u playlists to your server
source variables.sh

for entry in $plex_playlists/* # Gets all playlist paths
do
  playlist=${entry##*/} # Removes the path bit so just the file name is left
  echo "Updating Playlist $playlist"

  playlist=${playlist// /%20} # Removes spaces and replaces with %20 (needed for URLs)

  # Sends a POST request to the Plex Playlist API using curl
  curl -X POST "${server_url}/playlists/upload?sectionID=${section_id}&path=${server_playlists_path}${playlist}&X-Plex-Token=${token}" -H 'cache-control: no-cache'
done
