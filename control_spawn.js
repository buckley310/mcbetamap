L.control.spawn = function (opts) {
	let ctrl = L.Control.extend({
		onAdd: (map) => {
			var c = L.DomUtil.create("button");
			L.DomEvent.on(c, "click", () => map.setView([0, 0], 0));
			c.textContent = "Go to spawn";
			return c;
		},
	});

	return new ctrl(opts);
};
