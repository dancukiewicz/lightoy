function createWebSocket() {
    var loc = window.location;
    var ws = new WebSocket('ws://' + loc.host + '/ws');
    ws.onopen = function() {
	console.log("connection started");
    }
    ws.onclose = function(event) {
	if (event.wasClean) {
	    console.log("connection ended (clean)");
	} else {
	    console.warn("connection ended (unclean)");
	}
    }
    return ws;
}

var ws = createWebSocket();

document.body.addEventListener('touchstart', function(ev) {
    var out = {
	'ev': 'touchStart',
	'touches': Array.prototype.map.call(ev.touches, function(t) {
	    return {
		'x': t.pageX,
		'y': t.pageY
	    };
	})
    };
    console.log(out);
    ws.send(JSON.stringify(out));
});
