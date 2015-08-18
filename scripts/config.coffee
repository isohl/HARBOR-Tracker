prep = (x)->
	return x.replace(' ', '_SPACE_')

ca = (x)->
	return $(x).addClass('clickable')

displayFunction = (tag)->
	return (x) -> $(tag).val($(x.toElement).text())


filloutCallsignTable = (json)->
	if(json==undefined)
		$.getJSON('/tracks', filloutCallsignTable)
	else
		t = $('#associate-callsign-table')
		t.html('')

		for trackname of json 
			row = $('<tr>')
			row.append(ca('<td>'+trackname+'</td>').click(displayFunction('#associate-callsign-trackname')))
			cell = $('<td>')
			for x of json[trackname]
				callsign = json[trackname][x]
				close = ca('<span>x</span>').click((x)->
					$.getJSON('/removecallsign/'+$(x.toElement).attr('info'),filloutCallsignTable)
				)
				close.attr('info', callsign+'/'+trackname)
				cell.append($('<div>'+callsign+' (</div>').append(close).append(')'))
			row.append(cell)
			t.append(row)

filloutMetaTable = (json)->
	if(json==undefined)
		$.getJSON('/meta', filloutMetaTable)
	else
		t = $('#metadata-table')
		t.html('')
		for trackname of json 
			row = $('<tr>')
			cell = $('<td></td>')
			for key of json[trackname]
				cell.append(ca('<span>'+key+'</span>').click(displayFunction('#metadata-attribute')))
				cell.append(': ')
				cell.append(ca('<span>'+json[trackname][key]+'</span>').click(displayFunction('#metadata-value')))
				cell.append('<br>')
			row.append(ca('<td>'+trackname+'</td>').click(displayFunction('#metadata-trackname')))
			row.append(cell)
			t.append(row)

setup = ->
	filloutCallsignTable()
	filloutMetaTable()

$(document).ready(->
	setup()
	$('#associate-callsign-go').click(->
		trackname = prep($('#associate-callsign-trackname').val())
		callsign = prep($('#associate-callsign-callsign').val())
		$.getJSON('/addcallsign/'+callsign+'/'+trackname,filloutCallsignTable)
	)
	$('#metadata-go').click(->
		trackname = $('#metadata-trackname').val()
		attribute = $('#metadata-attribute').val()
		value = $('#metadata-value').val()
		data = {'name':trackname}
		data[attribute] = value
		$.post('/put', data,(dat)->filloutMetaTable($.parseJSON(dat)))
	)
	$('#reset-all').click(->
		$.get('/reset')
		setup()
	)
	$('#clear-tracks').click(->
		$.get('/clearpaths')
	)
)
