var baseLayers, count, html5_audio, lines, localMap, mainLoop, map, oldId, onlineMap, play_html5_audio, play_sound,
  hasProp = {}.hasOwnProperty,
  indexOf = [].indexOf || function(item) { for (var i = 0, l = this.length; i < l; i++) { if (i in this && this[i] === item) return i; } return -1; };

localMap = L.tileLayer('../gmaps/lyrs=y&hl=en&x={x}&y={y}&z={z}.jpg', {
  attribution: 'Imagery &copy <a href="http//maps.google.com">Google</a>',
  minZoom: 11,
  maxZoom: 17
});

onlineMap = L.tileLayer('http://mt0.google.com/vt/lyrs=y&hl=en&x={x}&y={y}&z={z}', {
  attribution: 'Imagery &copy <a href="http//maps.google.com">Google</a>',
  minZoom: 11,
  maxZoom: 17
});

map = L.map('map', {
  layers: [localMap]
}).setView([40.191484, -110.385534], 13);

baseLayers = {
  "Local Data": localMap,
  "Online Data": onlineMap
};

L.control.layers(baseLayers).addTo(map);

lines = {};

count = 0;

oldId = {};

play_html5_audio = false;

mainLoop = function() {
  return $.getJSON("/info", function(json) {
    var i, j, key, len, len1, point, ref, ref1, ref2, removeKeys, value;
    $('#altitudereadout').text(json.readouts.altitude);
    $('#ascentreadout').text(json.readouts.ascent);
    $('#bearingreadout').text(json.readouts.bearing);
    $('#rangereadout').text(json.readouts.range);
    removeKeys = [];
    if (oldId[json.readouts.primary] === void 0 && json.trackdata[json.readouts.primary] !== void 0) {
      map.setView(json.trackdata[json.readouts.primary][json.trackdata[json.readouts.primary].length - 1].slice(1, 3), 13);
      $('#latitudereadout').text(parseFloat(parseInt(parseFloat(json.trackdata[json.readouts.primary][json.trackdata[json.readouts.primary].length - 1][1]) * 1000000) / 1000000));
      $('#longitudereadout').text(parseFloat(parseInt(parseFloat(json.trackdata[json.readouts.primary][json.trackdata[json.readouts.primary].length - 1][2]) * 1000000) / 1000000));
    }
    ref = json.trackdata;
    for (key in ref) {
      if (!hasProp.call(ref, key)) continue;
      value = ref[key];
      removeKeys.push(key);
      if (key in lines && oldId[key] === json.id) {
        ref1 = value.slice(lines[key].getLatLngs().length);
        for (i = 0, len = ref1.length; i < len; i++) {
          point = ref1[i];
          lines[key].addLatLng(point.slice(1, 3));
        }
      } else {
        if (lines[key] !== void 0) {
          map.removeLayer(lines[key]);
        }
        lines[key] = L.polyline(parseFloat((function() {
          var j, len1, results;
          results = [];
          for (j = 0, len1 = value.length; j < len1; j++) {
            point = value[j];
            results.push(point.slice(1, 3));
          }
          return results;
        })()), json.trackmeta[key]).addTo(map).bindPopup(key);
      }
      oldId[key] = json.id;
    }
    ref2 = (function() {
      var results;
      results = [];
      for (key in lines) {
        results.push(key);
      }
      return results;
    })();
    for (j = 0, len1 = ref2.length; j < len1; j++) {
      key = ref2[j];
      if (indexOf.call(removeKeys, key) < 0) {
        map.removeLayer(lines[key]);
      }
    }
    if (count % 60 === 0) {
      if (count % 120 === 0) {
        play_sound("/asc.mp3");
      } else {
        play_sound("/alt.mp3");
      }
    }
    count += 1;
    return setTimeout(mainLoop, 500);
  });
};

html5_audio = function() {
  var a;
  a = document.createElement('audio');
  return !!(a.canPlayType && a.canPlayType('audio/mpeg;').replace(/no/, ''));
};

play_sound = function(url) {
  var snd, sound;
  if (play_html5_audio) {
    snd = new Audio(url);
    snd.load();
    return snd.play();
  } else {
    $("#sound").remove();
    sound = $("<embed id='sound' type='audio/mpeg' />");
    sound.attr('src', url);
    sound.attr('loop', false);
    sound.attr('hidden', true);
    sound.attr('autostart', true);
    return $('body').append(sound);
  }
};

$(document).ready(function() {
  var setBodyScale;
  setBodyScale = function() {
    var fontSize, maxScale, minScale, scaleFactor, scaleSource;
    scaleSource = $('body').width();
    scaleFactor = 0.20;
    maxScale = 600;
    minScale = 30;
    fontSize = scaleSource * scaleFactor;
    if (fontSize > maxScale) {
      fontSize = maxScale;
    }
    if (fontSize < minScale) {
      fontSize = minScale;
    }
    return $('.alphareadout').css('font-size', fontSize + '%');
  };
  $(window).resize(setBodyScale);
  setBodyScale();
  if (html5_audio()) {
    play_html5_audio = true;
  }
  return mainLoop();
});

