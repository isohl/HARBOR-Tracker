
main = function(){
  var map = L.map('map').setView([40.191484, -110.385534], 13);
  L.tileLayer('/gmaps/lyrs=y&hl=en&x={x}&y={y}&z={z}.jpg', {
    attribution: 'Imagery &copy <a href="http//maps.google.com">Google</a>',
    minZoom: 11,
    maxZoom: 17
  }).addTo(map);

  var play_html5_audio = false;
  if (html5_audio()) {
    play_html5_audio = true;
  }

  var count = 0;
  var lines = {};
  var meta = {};

  mainLoop = function() {
    $.getJSON("/readouts", function(json) {
      var key, point, removeKeys, value, _i, _j, _len, _len1, _ref, _ref1, _ref2;
      $('#altitudereadout').text(json.tracked.altitude);
      $('#ascentreadout').text(json.tracked.ascent);
      $('#bearingreadout').text(json.tracked.bearing);
      $('#rangereadout').text(json.tracked.range);
      // map.setView(json.trackdata[json.readouts.primary][json.trackdata[json.readouts.primary].length - 1].slice(1, 3), 13);
      // $('#latitudereadout').text(parseFloat(parseInt(parseFloat(json.trackdata[json.readouts.primary][json.trackdata[json.readouts.primary].length - 1][1]) * 1000000) / 1000000));
      // $('#longitudereadout').text(parseFloat(parseInt(parseFloat(json.trackdata[json.readouts.primary][json.trackdata[json.readouts.primary].length - 1][2]) * 1000000) / 1000000));
    });

    $.getJSON("/paths", function(json) {
      for (callsign in json){
        var path = json[callsign];
        if (callsign in lines){
          existing = lines[callsign];
          if (existing[existing.length-1] == path[path.length-1]){
            continue;
          }
          map.removeLayer(lines[key]);
        }
        var points = []
        for (point in path){
          points.push([parseFloat(point.latitude), parseFloat(point.longitude)])
        }
        lines[callsign] = L.polyline(points, meta[callsign]).addTo(map).bindPopup(key);
      }
      
      _ref2 = (function() {
        var _results;
        _results = [];
        for (key in lines) {
          _results.push(key);
        }
        return _results;
      })();
      for (_j = 0, _len1 = _ref2.length; _j < _len1; _j++) {
        key = _ref2[_j];
        if (__indexOf.call(removeKeys, key) < 0) {
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
    });

    count += 1;
    return setTimeout(mainLoop, 500);
  };

  return mainLoop();
}

html5_audio = function() {
  var a = document.createElement('audio');
  return !!(a.canPlayType && a.canPlayType('audio/mpeg;').replace(/no/, ''));
};

play_sound = function(url, play_html5_audio) {
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

initialize = function() {
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
  return main();
}

$(document).ready(initialize());

(function() {
  var count, html5_audio, lines, mainLoop, map, oldId, play_html5_audio, play_sound,
    __hasProp = {}.hasOwnProperty,
    __indexOf = [].indexOf || function(item) { for (var i = 0, l = this.length; i < l; i++) { if (i in this && this[i] === item) return i; } return -1; };

  map = L.map('map').setView([40.191484, -110.385534], 13);

  L.tileLayer('../gmaps/lyrs=y&hl=en&x={x}&y={y}&z={z}.jpg', {
    attribution: 'Imagery &copy <a href="http//maps.google.com">Google</a>',
    minZoom: 11,
    maxZoom: 17
  }).addTo(map);

  lines = {};

  count = 0;

  oldId = {};

  play_html5_audio = false;

  mainLoop = function() {
    return $.getJSON("/info", function(json) {
      var key, point, removeKeys, value, _i, _j, _len, _len1, _ref, _ref1, _ref2;
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
      _ref = json.trackdata;
      for (key in _ref) {
        if (!__hasProp.call(_ref, key)) continue;
        value = _ref[key];
        removeKeys.push(key);
        if (key in lines && oldId[key] === json.id) {
          _ref1 = value.slice(lines[key].getLatLngs().length);
          for (_i = 0, _len = _ref1.length; _i < _len; _i++) {
            point = _ref1[_i];
            lines[key].addLatLng(point.slice(1, 3));
          }
        } else {
          if (lines[key] !== void 0) {
            map.removeLayer(lines[key]);
          }
          lines[key] = L.polyline(parseFloat((function() {
            var _j, _len1, _results;
            _results = [];
            for (_j = 0, _len1 = value.length; _j < _len1; _j++) {
              point = value[_j];
              _results.push(point.slice(1, 3));
            }
            return _results;
          })()), json.trackmeta[key]).addTo(map).bindPopup(key);
        }
        oldId[key] = json.id;
      }
      _ref2 = (function() {
        var _results;
        _results = [];
        for (key in lines) {
          _results.push(key);
        }
        return _results;
      })();
      for (_j = 0, _len1 = _ref2.length; _j < _len1; _j++) {
        key = _ref2[_j];
        if (__indexOf.call(removeKeys, key) < 0) {
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

}).call(this);
