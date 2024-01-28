L.Marker.addInitHook(function () {
	let onAdd = function () {
		this._updateIconVisibility = function () {
			let inBounds = this._map.getBounds().contains(this.getLatLng());
			let display = inBounds ? "" : "none";
			this._icon.style.display = display;
			this._shadow.style.display = display;
		};
		this._map.on("resize moveend zoomend", this._updateIconVisibility, this);
		this._updateIconVisibility();
	};
	this.on("add", onAdd, this);
});
