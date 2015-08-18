filloutTable = (json)->
	if(json==undefined)
		$.getJSON('/log', filloutTable)
	else
		t = $('#associate-callsign-table')
		t.html('')

		for trackname of json 
			row = $('<tr>')
			row.append('<td>'+trackname+'</td>')
			cell = $('<td>')
			cell.append(json[trackname])
			row.append(cell)
			t.append(row)

setup = ->
	filloutTable()

$(document).ready(->
	setup()
)