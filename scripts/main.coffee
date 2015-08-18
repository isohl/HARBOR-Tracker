map = L.map('map').setView([40.191484, -110.385534], 13)
L.tileLayer('../gmaps/lyrs=y&hl=en&x={x}&y={y}&z={z}.jpg', {
#L.tileLayer('http://mt0.google.com/vt/lyrs=y&hl=en&x={x}&y={y}&z={z}', {
	attribution: 'Imagery &copy <a href="http//maps.google.com">Google</a>',
	minZoom: 11, maxZoom: 17}).addTo(map)
lines = {}
count = 0
oldId = {}
play_html5_audio = false

mainLoop =  ->
	$.getJSON "/info", (json) ->
		$('#altitudereadout').text(json.readouts.altitude)
		$('#ascentreadout').text(json.readouts.ascent)
		$('#bearingreadout').text(json.readouts.bearing)
		$('#rangereadout').text(json.readouts.range)
		removeKeys = []
		if oldId[json.readouts.primary] == undefined and json.trackdata[json.readouts.primary] != undefined
			map.setView(json.trackdata[json.readouts.primary][json.trackdata[json.readouts.primary].length-1][1..2],13)
			$('#latitudereadout').text(parseFloat(parseInt(parseFloat(json.trackdata[json.readouts.primary][json.trackdata[json.readouts.primary].length-1][1])*1000000)/1000000))
			$('#longitudereadout').text(parseFloat(parseInt(parseFloat(json.trackdata[json.readouts.primary][json.trackdata[json.readouts.primary].length-1][2])*1000000)/1000000))
		for own key, value of json.trackdata
			#console.log json.trackdata[key], value.length
			removeKeys.push(key)
			if key of lines and oldId[key] == json.id
				for point in value[lines[key].getLatLngs().length..]
					lines[key].addLatLng(point[1..2])
			else
				if lines[key] != undefined
					map.removeLayer lines[key] 
				lines[key] = L.polyline(parseFloat(point[1..2] for point in value), json.trackmeta[key]).addTo(map).bindPopup(key)
			oldId[key] = json.id
		for key in (key for key of lines)
			unless key in removeKeys
				map.removeLayer lines[key]
		if count%60==0
			if count%120==0
				play_sound("/asc.mp3")
			else
				play_sound("/alt.mp3")
		count+=1
		setTimeout(mainLoop, 500)

html5_audio = ->
	a = document.createElement('audio')
	return !!(a.canPlayType && a.canPlayType('audio/mpeg;').replace(/no/, ''))
 
 
play_sound = (url) ->
	if(play_html5_audio)
		snd = new Audio(url);
		snd.load();
		snd.play();
	else
		$("#sound").remove();
		sound = $("<embed id='sound' type='audio/mpeg' />");
		sound.attr('src', url);
		sound.attr('loop', false);
		sound.attr('hidden', true);
		sound.attr('autostart', true);
		$('body').append(sound);
	

$(document).ready ->
	setBodyScale = ->
		scaleSource = $('body').width()
		scaleFactor = 0.20				
		maxScale = 600
		minScale = 30
		fontSize = scaleSource * scaleFactor;
		fontSize = maxScale if (fontSize > maxScale)
		fontSize = minScale if (fontSize < minScale)
		$('.alphareadout').css('font-size', fontSize + '%')
	
	$(window).resize setBodyScale
	setBodyScale()
	if html5_audio() 
		play_html5_audio = true
	mainLoop()


