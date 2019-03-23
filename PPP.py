#!/usr/bin/python3

## PPP (Plex Playlist Pusher) v2.1.2
# Synchronises playlists between local files (.m3u) and Plex playlists.
# If there are differences between local and Plex playlists, both will be merged and duplicates deleted; meaning tracks
# can be added on one and updated on both... but must be deleted on BOTH to remove completely (the same goes for new playlists).

# XDGFX 2019

# 17/03/19 Started working on script
# 19/03/19 Original v2.0 Release
# 20/03/19 v2.1 Updated to use tempfile module temporary directory
# 22/03/19 v2.1.1 General improvements and bug fixes
# 23/03/19 v2.1.2 Fixed v2.1 and v2.1.1 releases, no longer using tempfile

# Uses GNU General Public License

# VARIABLES GO HERE
server_url = '192.168.1.96:32400'				# The url to your server (may be localhost)
plex_token = 'P6X4rFdFhcTssbA6pXoT'				# Where do I find this? Here: bit.ly/2p7RtOu
local_playlists = '/mnt/Playlists'				# Path (relative to the machine you're running this on)
install_directory = 'D:\\Media\\PPP'				# The path to this PPP folder; as seen by your Plex machine (must be accessible by your Plex machine, but you can run this program on any machine on the network)
section_id = '11'						# The media section containing all your music (Google 'find Plex section ID')

# Use only if your local playlists and plex playlists have different directories (e.g. if they are not from the same machine) and so have different paths at the start
# If your directories include backslashes (they probably will) you need to escape it with a second backslash... 'D:\' becomes 'D:\\'
# Leave blank ('') if your directories are the same
local_prepend = '\\\\uluru\\Uluru\\'
plex_prepend = 'D:\\'

# NOTES: If you have used the Plex Playlist PUSH api in the past, existing playlists will be duplicated when running this program.
#        This is because the playlist .m3u files are located in a different place. Delete the old playlists from Plex and run PPP again.
#
#		 USE AT YOUR OWN RISK: I TAKE NO RESPONSIBILITY IF YOU BREAK SOMETHING AND YOU DON'T HAVE BACKUPS!

#---- No need to edit below here ----

print("\nPPP Copyright (C) 2019 XDGFX \nThis program comes with ABSOLUTELY NO WARRANTY. \nThis is free software, and you are welcome to redistribute it \nunder certain conditions\n")

print(('I\'ll ignore \"' + local_prepend + '\" from local playlists and \"' + plex_prepend + '\" from Plex playlists\n'))

# Import modules
from xml.dom import minidom			# for xml
import urllib.request				# for xml
from urllib.request import urlopen		# for xml
import shutil					# for deleting files
import os					# for folder and file management
import io					# character encoding
from collections import OrderedDict		# url ordering
import requests					# HTTP POST requests

if not plex_token:
	print('ERROR: Hmm... looks like you haven\'t set your variables! Do this by editing getPlaylists.py with a text editor')
	raise SystemExit

if os.path.isdir('tmp/'):
	try:
		shutil.rmtree('tmp/')
	except:
		print('RIP: I couldn\'t remove tmp folder. Try deleting manually?')
		raise SystemExit

if not os.path.isdir('local_backups') and not os.path.isfile('NOBACKUPS'):		
	os.makedirs('local_backups')
	
try:
	os.makedirs('tmp/')
	os.makedirs('tmp/plex/')
	os.makedirs('tmp/local/')
	os.makedirs('tmp/merged/')
	
	if not os.path.isfile('NOBACKUPS'):
		i = 1
		while os.path.exists('local_backups/%s' % i):
			i += 1
		if i > 10:
			size = sum(os.path.getsize(os.path.join(dirpath,filename)) for dirpath, dirnames, filenames in os.walk('local_backups') for filename in filenames ) / 1024 / 1024
			print('You have 10+ backups in your install directory, taking up %sMB of space... You might want to remove some old ones.\n' % round(size, 2))
			print("Alternatively, create an empty file 'NOBACKUPS' in your PPP/ directory")
	
		# Backup local playlists
		try:
			print('Backing up local playlists...\n')
			shutil.copytree(local_playlists, 'local_backups/%s' % i)
			print(('Backed up local playlists to local_backups/%s/\n' % i))
		except shutil.Error as e:
			print(('Directory not copied. Error: %s' % e))
		except OSError as e:
			print(('Directory not copied. Error: %s' % e))
	else:
		print('Not backing up local playlists. If this was NOT intentional, exit the program immediately\n')

except:
	print('OH NO: Couldn\'t make tmp directories... check your permissions or make sure you don\'t have them open elsewhere')
	raise SystemExit
		
# Get list of playlist IDs
url = 'http://' + str(server_url) + '/playlists/?X-Plex-Token=' + str(plex_token)
print(('Getting playlists from ' + str(url) + '\n'))

dom = minidom.parse(urlopen(url)) # Parse the data

# Extract key from each Playlist item as long as it's not a smart playlist
key = dom.getElementsByTagName('Playlist')
key = [items.attributes['key'].value for items in key if items.attributes['smart'].value == "0"]

# Copies Plex playlists to tmp/plex/ folder
for item in key:
	url = 'http://' + str(server_url) + str(item) + '?X-Plex-Token=' + str(plex_token)
	print(('Accessing ' + str(url)))

	dom = minidom.parse(urlopen(url)) # Parse the data (for each playlist)
	
	# Get title of playlist
	title = dom.getElementsByTagName('MediaContainer')
	title = [items.attributes['title'].value for items in title] # Extract playlist title
	
	print(('Saving Plex playlist: ' + str(title[0]) + '\n'))

	# Get each track and save to file
	file = open('tmp/plex/' + str(title[0]) + '.m3u', 'w+')
	
	path = dom.getElementsByTagName('Part')
	path = [items.attributes['file'].value for items in path] # Extract disk path to music file
	
	# Writes music path to .m3u file, repeating for each track
	for i in range(len(path)):
		file.write(path[i] + '\n')
	file.close()

# Copies local playlists to tmp/local/ folder
for root, dirs, files in os.walk(local_playlists):
	for file in files:
		file_path = os.path.join(root, file)
	
		if file.endswith('.m3u'):
			print(('Copying local playlist: ' + file_path))
			shutil.copy2(file_path, 'tmp/local/')
			
# Checks for unique playlists to tmp/plex/, and copies them to tmp/merged/
for filename in os.listdir('tmp/plex/'):
	if not os.path.isfile(os.path.join('tmp/local/', filename)):
		print(('Found new Plex playlist: ' + filename))
		plex_tracks = open(os.path.join('tmp/plex/', filename), 'r').read().splitlines()
		os.remove(os.path.join('tmp/plex/', filename))
		file = open('tmp/merged/' + filename, 'w+')
		for i in range(len(plex_tracks)):
			plex_tracks[i] = plex_tracks[i].strip(plex_prepend) # Strips plex_prepend
			file.write(plex_tracks[i] + '\n')

# Checks for unique playlists to tmp/local/, and copies them to tmp/merged/
for filename in os.listdir('tmp/local/'):
	if not os.path.isfile(os.path.join('tmp/plex/', filename)):
		print(('Found new local playlist: ' + filename))
		local_tracks = open(os.path.join('tmp/local/', filename), 'r').read().splitlines()
		os.remove(os.path.join('tmp/local/', filename))
		file = open('tmp/merged/' + filename, 'w+')
		for i in range(len(local_tracks)):
			if not local_tracks[i].startswith('#'): #Skips m3u tags beginning with #
				local_tracks[i] = local_tracks[i].strip(local_prepend) # Strips local_prepend
				file.write(local_tracks[i] + '\n')
		file.close()

# Merges playlists from tmp/local/ and tmp/plex/ and puts the output in tmp/merged			
for filename in os.listdir('tmp/local/'):
	
	print(('Merging: ' + filename))

	local_tracks = open(os.path.join('tmp/local/', filename), 'r').read().splitlines()

	for i in range(len(local_tracks)): # Strips local_prepend
		local_tracks[i] = local_tracks[i].strip(local_prepend)

	plex_tracks = open(os.path.join('tmp/plex/', filename), 'r').read().splitlines()

	for i in range(len(plex_tracks)): # Strips plex_prepend
		plex_tracks[i] = plex_tracks[i].strip(plex_prepend)

	file = io.open(os.path.join('tmp/merged/', filename), 'w+', encoding='utf8')
	
	for line in local_tracks: # Writes local_tracks to merged playlist
		
		if not line.startswith('#'): # Skips m3u tags beginning with #
			file.write(line + '\n')
	
		if line in plex_tracks: # Remove duplicates
			plex_tracks.remove(line)
		
	for line in plex_tracks: # Writes plex_tracks to merged playlist
		file.write(line + '\n')
		
	file.close()
		
# Copy merged playlists back into tmp/plex/ and tmp/local/ with prepends re-added
for filename in os.listdir('tmp/merged/'):
	new_tracks = open(os.path.join('tmp/merged/', filename), 'r+').read().splitlines()
	plex_tracks = []
	local_tracks = []
	
	for i in range(len(new_tracks)): # Re-adds prepends and writes to files
		plex_tracks.append(plex_prepend + new_tracks[i])
		local_tracks.append(local_prepend + new_tracks[i])

	file = io.open(os.path.join('tmp/local/', filename), 'w+', encoding='utf8')
		
	for line in local_tracks: # Writes local_tracks to merged playlist
		file.write(line + '\n')

	file.close()
		
	file = io.open(os.path.join('tmp/plex/', filename), 'w+', encoding='utf8')
		
	for line in plex_tracks: # Writes local_tracks to merged playlist
		file.write(line + '\n')
		
	file.close()
			
# POST new playlists to Plex
url = 'http://' + server_url + '/playlists/upload?'
headers = {'cache-control': "no-cache"}

for filename in os.listdir('tmp/plex/'):
	print('Sending updated playlist to Plex: ' + filename)
	
	current_playlist = install_directory + '\\tmp\\plex\\' + filename
	
	querystring = urllib.parse.urlencode(OrderedDict([("sectionID", section_id), ("path", current_playlist), ("X-Plex-Token", plex_token)]))
	response = requests.post(url, data = "", headers = headers, params = querystring)
	print(response.text) # Should return nothing but if there's an issue there may be an error shown
	
# Copy updated local playlists back to local_playlists
for root, dirs, files in os.walk(local_playlists):
	for file in files:
		if file.endswith('.m3u'):
			print('Copying updated playlist to local playlists: ' + file)
			file_path = os.path.join(root, file)
			if os.path.isfile('tmp/local/' + file):
				shutil.copy2('tmp/local/' + file, file_path)
				os.remove('tmp/local/' + file)
			else:
				print('FAIL: A playlist from local_playlists was there earlier and now it isn\'t. I am very confused.')
				raise SystemExit

for filename in os.listdir('tmp/local/'):
	shutil.copy2('tmp/local/' + filename, local_playlists)
	
try:
	shutil.rmtree('tmp/')
	print('Complete!\n')
except shutil.Error as e:
	print('Program complete, but I had trouble cleaning tmp/ directory. Check it\'s not open somewhere else \n Error: %s' % e)
	raise SystemExit
