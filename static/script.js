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
    ws.onmessage = function(event) {
	var msg = JSON.parse(event.data);
	refresh(msg.pos);
    }
    return ws;
}

var ws = createWebSocket();


function refresh(pos) {
    var crossClassName = "cross";
    var crosses = document.getElementsByClassName(crossClassName);
    Array.prototype.forEach.call(crosses, function(cross) {
	cross.parentNode.removeChild(cross);
    });
    Array.prototype.forEach.call(pos, function(p) {
	var el = document.createElement("div");
	el.className = crossClassName;
	el.innerHTML = "+";
	el.style.width = "40";
	el.style.height = "40";
	el.style.position = "absolute";
	el.style.left = p.x;
	el.style.top = p.y;
	document.body.append(el);
    });
}


/* TODO: clearly, these handlers need to be refactored */

document.body.addEventListener('touchstart', function(ev) {
    ev.preventDefault();
    var out = {
	'ev': 'touchstart',
	'touches': Array.prototype.map.call(ev.touches, function(t) {
	    return {
		'x': t.pageX,
		'y': t.pageY
	    };
	})
    };
    ws.send(JSON.stringify(out));
    ws.send(JSON.stringify(out));
});

document.body.addEventListener('touchmove', function(ev) {
    ev.preventDefault();
    var out = {
	'ev': 'touchmove',
	'touches': Array.prototype.map.call(ev.touches, function(t) {
	    return {
		'x': t.pageX,
		'y': t.pageY
	    };
	})
    };
    ws.send(JSON.stringify(out));
});

document.body.addEventListener('touchend', function(ev) {
    ev.preventDefault();
    var out = {
	'ev': 'touchend',
	'touches': Array.prototype.map.call(ev.touches, function(t) {
	    return {
		'x': t.pageX,
		'y': t.pageY
	    };
	})
    };
    ws.send(JSON.stringify(out));
});

document.body.addEventListener('touchcancel', function(ev) {
    ev.preventDefault();
    var out = {
	'ev': 'touchcancel',
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
