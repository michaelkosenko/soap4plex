# -*- coding: utf-8 -*-

# created by sergio
# updated by kestl1st@gmail.com (@kestl) v.1.2.3 2016-08-01
# updated by sergio v.1.2.2 2014-08-28

import re,urllib2,base64,hashlib,md5,urllib
import calendar
from datetime import *
import time

VERSION = 2.0
PREFIX = "/video/soap4me"
TITLE = 'soap4.me'
ART = 'art.png'
ICON = 'icon.png'
BASE_URL = 'http://soap4.me/'
OLD_API_URL = 'http://soap4.me/api/'
API_URL = 'https://api.soap4.me/v2/'
LOGIN_URL = 'https://api.soap4.me/v2/auth/'
USER_AGENT = 'soap4.me plex plugin'
LOGGEDIN = False
TOKEN = False
SID = ''

# login : http -v --form POST https://api.soap4.me/v2/auth/ login=<username> password=<password> User-Agent:"soap4.me plex plugin"

def Start():
	ObjectContainer.art = R(ART)
	ObjectContainer.title1 = TITLE
	DirectoryObject.thumb = R(ICON)

	HTTP.CacheTime = CACHE_1HOUR
	HTTP.Headers['User-Agent'] = USER_AGENT
	HTTP.Headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
	HTTP.Headers['Accept-Encoding'] ='gzip,deflate,sdch'
	HTTP.Headers['Accept-Language'] ='ru-ru,ru;q=0.8,en-us;q=0.5,en;q=0.3'
	HTTP.Headers['x-api-token'] = TOKEN


def Login():
	global LOGGEDIN, SID, TOKEN

	if not Prefs['username'] and not Prefs['password']:
		return 2
	else:

		try:
			values = {
				'login' : Prefs["username"],
				'password' : Prefs["password"]}

			obj = JSON.ObjectFromURL(LOGIN_URL, values, encoding='utf-8', cacheTime=1,)
		except:
			obj=[]
			LOGGEDIN = False
			return 3
		SID = obj['sid']
		TOKEN = obj['token']
		if len(TOKEN) > 0:
			LOGGEDIN = True
			Dict['sid'] = SID
			Dict['token'] = TOKEN
			return 1
		else:
			LOGGEDIN = False
			Dict['sessionid'] = ""

			return 3


def Thumb(url):
	if url=='':
		return Redirect(R(ICON))
	else:
		try:
			data = HTTP.Request(url, cacheTime=CACHE_1WEEK).content
			return DataObject(data, 'image/jpeg')
		except:
			return Redirect(R(ICON))


@handler(PREFIX, TITLE, thumb=ICON, art=ART)
def MainMenu():

	oc = ObjectContainer()
	oc.add(DirectoryObject(key=Callback(Soaps, title2=u'Все сериалы', filter='all'), title=u'Все сериалы'))
	oc.add(DirectoryObject(key=Callback(Soaps, title2=u'Я смотрю', filter='watching'), title=u'Я смотрю'))
	oc.add(DirectoryObject(key=Callback(Soaps, title2=u'Новые эпизоды', filter='unwatched'), title=u'Новые эпизоды'))
	oc.add(PrefsObject(title=u'Настройки', thumb=R('settings.png')))

	return oc


@route(PREFIX+'/{filter}')
def Soaps(title2, filter):
	logged = Login()
	if logged == 2:
		return MessageContainer(
			"Ошибка",
			"Ведите пароль и логин"
		)

	elif logged == 3:
		return MessageContainer(
			"Ошибка",
			"Отказано в доступе"
		)
	else:

		dir = ObjectContainer(title2=title2.decode())
		if filter == 'all':
			url = API_URL + 'soap/'
		else:
			url = API_URL + 'soap/my/'
		obj = GET(url)

		obj=sorted(obj, key=lambda k: k['title_ru'])

		for items in obj:
			if filter == 'unwatched' and items["unwatched"] == None:
				continue
	
			soap_title = items["title_ru"]

			if filter != 'unwatched':
				title = soap_title
			else:
				title = items["title"]+ " (" +str(items["unwatched"])+ ")"
				
			if "description" in items:
				summary = items["description"]
			else:
				summary = ""

			poster = 'http://covers.s4me.ru/soap/big/'+items["sid"]+'.jpg'
			rating = float(items["imdb_rating"])
			summary = summary.replace('&quot;','"')
			fan = 'http://thetvdb.com/banners/fanart/original/'+items['tvdb_id']+'-1.jpg'
			id = items["sid"]
			thumb = Function(Thumb, url=poster)
			dir.add(TVShowObject(key=Callback(show_seasons, id = id, soap_title = soap_title, filter = filter, unwatched = filter=='unwatched'), rating_key = str(id), title = title, summary = summary, art = fan,rating = rating, thumb = thumb))
		return dir


@route(PREFIX+'/{filter}/{id}', unwatched=bool)
def show_seasons(id, soap_title, filter, unwatched = False):
	dir = ObjectContainer(title2 = soap_title)
	url = API_URL + 'episodes/'+id
	data = GET(url)
	season = {}
	useason = {}
	s_length = {}

	covers = dict(
        (int(cover['season']), cover['big'])
        for cover in data.get('covers', list())
    )

	if unwatched:
		for episode in data:
			if episode['watched'] == None:
				if int(episode['season']) not in season:
					season[int(episode['season'])] = episode['season']
				if int(episode['season']) not in useason.keys():
					useason[int(episode['season'])] = []
					useason[int(episode['season'])].append(int(episode['episode']))
				elif int(episode['episode']) not in useason[int(episode['season'])]:
					useason[int(episode['season'])].append(int(episode['episode']))
	else:
		for episode in data['episodes']:
			if int(episode['season']) not in season:
				season[int(episode['season'])] = episode['season']
				s_length[int(episode['season'])] = [episode['episode'],]
			else:
				if episode['episode'] not in s_length[int(episode['season'])]:
					s_length[int(episode['season'])].append(episode['episode'])
	for row in season:
		if unwatched:
			title = "%s сезон (%s)" % (row, len(useason[row]))
		else:
			title = "%s сезон" % (row)
		season_id = str(row)
		poster = covers[row]
		thumb=Function(Thumb, url=poster)

		dir.add(SeasonObject(key=Callback(show_episodes, sid = id, season = season_id, filter=filter, soap_title=soap_title, unwatched = unwatched), episode_count=len(s_length[row]) if s_length else len(useason[row]), show=soap_title, rating_key=str(row), title = title, thumb = thumb))
	return dir

@route(PREFIX+'/{filter}/{sid}/{season}', allow_sync=True, unwatched=bool)
def show_episodes(sid, season, filter, soap_title, unwatched = False):
	dir = ObjectContainer(title2 = u'%s - %s сезон ' % (soap_title, season))
	url = API_URL + 'episodes/'+sid
	data = GET(url)
	quality = Prefs["quality"]
	sort = Prefs["sorting"]
	show_only_hd = False

	if quality == "HD":
		for episode in data:
			if season == episode['season']:
				if episode['quality'] == '720p':
					show_only_hd = True
					break

	for row in data['episodes']:
		if season == row['season']:
			if quality == "HD" and show_only_hd == True and row['quality'] != '720p':
				continue
			elif quality == "SD" and show_only_hd == False and row['quality'] != 'SD':
				continue
			else:
				if row['watched'] != None and unwatched:
					continue
				else:

					eid = ''
					ehash = ''
					q = 0
					translate = 0

					files = row['files']
					files = sorted(files, key=lambda k: k['quality'], reverse=True)
					for file in files:
						if int(file["quality"]) <= get_quality(quality):
							eid = file["eid"]
							ehash = file['hash']
							q = file['quality']
							translate = file['translate']
							break

					row['quality'] = q
					title = ''
					if not row['watched'] and not unwatched:
						title += '* '
					title += str(row['episode']) + " - " \
							+ row['title_ru'].encode('utf-8').replace('&#039;', "'").replace("&amp;", "&").replace('&quot;','"') \
							+ " (" + name_quality(q).encode('utf-8') + "  " \
							+ name_translate(translate).encode('utf-8') + ")"
					poster = row['screenshots']['big']
					summary = row['spoiler']
					thumb = Function(Thumb, url=poster)
					parts = [PartObject(key=Callback(episode_url, sid=sid, eid=eid, ehash=ehash, part=0))]
					if Prefs["mark_watched"]=='да':
						parts.append(PartObject(key=Callback(episode_url, sid=sid, eid=eid, ehash=ehash, part=1)))
					dir.add(EpisodeObject(
						key=Callback(play_episode, sid = sid, eid = eid, ehash = ehash, row=row),
						rating_key='soap4me' + eid,
						title=title,
						index=int(row['episode']),
						thumb=thumb,
						summary=summary,
						items=[MediaObject(parts=parts)]
					))
	return dir

def name_quality(quality):
	if int(quality) == 1:
		return 'SD'
	elif int(quality) == 2:
		return '720p'
	elif int(quality) == 3:
		return 'FullHD'
	elif int(quality) == 4:
		return '4K'
	else:
		return 'X3'

def name_translate(translate):
	if int(translate) == 1:
		return 'Оригинал'
	elif int(translate) == 2:
		return 'Субтитры'
	elif int(translate) == 3:
		return 'РусСуб'
	elif int(translate) == 4:
		return 'Перевод'
	else:
		return ''

def get_quality(quality):
	if quality == 'SD':
            return 1
        elif quality == '720p':
            return 2
        elif quality == 'FullHD':
            return 3
        elif quality == '4K':
            return 4

def get_resolution(quality):
	if int(quality) == 1:
		return '400'
	elif int(quality) == 2:
		return '720'
	elif int(quality) == 3:
		return '1080'
	elif int(quality) == 4:
		return '2160'
	else:
		return '400'

def play_episode(sid, eid, ehash, row, *args, **kwargs):
	Log.Debug("--- PLAY EPISODE")	
	oc = ObjectContainer()
	parts = [PartObject(key=Callback(episode_url, sid=sid, eid=eid, ehash=ehash, part=0))]
	if Prefs["mark_watched"] == 'да':
		parts.append(PartObject(key=Callback(episode_url, sid=sid, eid=eid, ehash=ehash, part=1)))
	oc.add(EpisodeObject(
		key=Callback(play_episode, sid = sid, eid = eid, ehash = ehash, row=row),
		rating_key='soap4me' + eid,
		items=[MediaObject(
			video_resolution = get_resolution(row['quality']).encode('utf-8'),
			video_codec = VideoCodec.H264,
			audio_codec = AudioCodec.AAC,
			container = Container.MP4,
			optimized_for_streaming = True,
			audio_channels = 2,
			parts = parts
		)]
	))
	return oc

def episode_url(sid, eid, ehash, part):
	Log.Debug("--- EPISODE URL")
	token = Dict['token']
	if part == 1:
		params = {"what": "mark_watched", "eid": eid, "token": token}
		data = JSON.ObjectFromURL("http://soap4.me/callback/", params, headers = {'x-api-token': Dict['token'], 'Cookie': 'PHPSESSID='+Dict['sid']})
		return Redirect('https://soap4.me/assets/blank/blank1.mp4')

	myhash = hashlib.md5(str(token)+str(eid)+str(sid)+str(ehash)).hexdigest()



	params = {"eid":eid, "hash":myhash}
	Log('*** ' + str(params))
	data = JSON.ObjectFromURL("https://api.soap4.me/v2/play/episode/{eid}/".format(eid=eid), params, headers = {'x-api-token': Dict['token'], 'Cookie': 'PHPSESSID='+Dict['sid']})
	Log('*** ' + str(data))
	if data["ok"] == 1:
		return Redirect(data['stream'])

def GET(url):
	return JSON.ObjectFromURL(url, headers = {'x-api-token': Dict['token'], 'Cookie': 'PHPSESSID='+Dict['sid']}, cacheTime = 0)
