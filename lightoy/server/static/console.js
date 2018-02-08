function createWebSocket() {
  // TODO: code duplication with touch ws thing
  var loc = window.location;
  var ws = new WebSocket('ws://' + loc.host + '/console_ws');
  ws.onopen = function() {
    console.log("connection started");
    document.body.style.backgroundColor = "#ddf";
  }
  ws.onclose = function(event) {
  document.body.style.backgroundColor = "#fff";
    if (event.wasClean) {
      console.log("connection ended (clean)");
    } else {
      console.warn("connection ended (unclean)");
    }
  }
  ws.onmessage = function(event) {
    var msg = JSON.parse(event.data);
    updateConsole(msg);
  }
  return ws;
}

var ws = createWebSocket();

function updateConsole(msg) {
  console.log("updating console but not really", msg);
}

function activateSlider(el) {
  var name = el.getAttribute("name");
  var isGlobal = (el.getAttribute("global") == "global");
  var width = el.offsetWidth;
  var tabEl = el.getElementsByClassName('slider-tab')[0];
  var tabWidth = tabEl.offsetWidth;
  var min = parseFloat(el.getAttribute("min"));
  var max = parseFloat(el.getAttribute("max"));
  // TODO: hack
  if (!isGlobal) {
    max = max / 10;
  }
  var range = max - min;
  var defaultValue = parseFloat(el.getAttribute("value"));
  var dragging = false;
  console.log("activating slider:", name, min, max, defaultValue);

  function setLocation(value) {
    var left = parseInt((value / range - min) * width - tabWidth / 2.);
    tabEl.style.left = left;
  }

  function setLocationFromEvent(e) {
    var value = e.clientX / width * range + min;
    setLocation(value);
    onUpdate(name, value);
  }

  el.addEventListener("mousedown", function(e) {
    dragging = true;
    setLocationFromEvent(e);
  });
  el.addEventListener("mousemove", function(e) {
    if (dragging) {
      setLocationFromEvent(e);
    }
  });
  el.addEventListener("mouseup", function(e) {
    dragging = false;
    setLocationFromEvent(e);
  });

  function onUpdate(name, value) {
    console.log(name, value);
    ws.send(JSON.stringify({
      ev: "sliderUpdate",
      name: name,
      value: value,
      global: isGlobal
    }));
  }

  setLocation(defaultValue);
}

function activateAllSliders() {
  var sliders = document.getElementsByClassName('slider');
  for (var i = 0; i < sliders.length; i++) {
    var el = sliders[i];
    activateSlider(el);
  }
}

activateAllSliders();
