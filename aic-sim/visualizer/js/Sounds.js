var Sample = Class.create({
    initialize: function(url) {
	this.url = url;
	this.loaded = false;
	this.buffer = null;
    },
    load: function(context) {
	var request = new XMLHttpRequest();
	request.open("GET", this.url, true);
	request.responseType = "arraybuffer";
	
	request.onload = function() { 
            this.buffer = context.createBuffer(request.response, false);
	    this.loaded = true;
	}.bind(this);

	request.onerror = function() { 
            alert("error loading sample: " + this.url);
	}.bind(this);

	request.send();
    },
    play: function(context, time) {
	if (this.loaded) {
	    var src = context.createBufferSource();
	    src.buffer = fireball.buffer;
	    src.connect(context.destination);
	    src.noteOn(time);
	}
    }
});
