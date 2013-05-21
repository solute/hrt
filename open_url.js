var page = require('webpage').create();
var system = require('system');

page.viewportSize = { width: 800, height : 600 };

setTimeout(function() {
	phantom.exit();
}, 20000);

page.open(system.args[1], function(status){
	window.setTimeout(function() {
	        phantom.exit();
	}, 5000);
});

