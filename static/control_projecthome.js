L.control.projecthome = function (opts) {
	let ctrl = L.Control.extend({
		onAdd: (map) => {
			let d = L.DomUtil.create("div");
			d.innerHTML = `
				<a href="https://github.com/buckley310/mcbetamap">MCBetaMap</a>
			`;
			d.style.margin = 0;
			d.style.padding = "0 5px";
			d.style.background = "rgba(255, 255, 255, 0.8)";
			return d;
		},
	});

	return new ctrl(opts);
};
