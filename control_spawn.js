L.Control.Spawn = L.Control.extend({
    onAdd: function (map) {
        var d = L.DomUtil.create('button');
        L.DomEvent.on(d, 'click', () => map.setView([0, 0], 0));
        d.textContent = 'Go to spawn';
        return d;
    },
    onRemove: function (map) { }
});

L.control.spawn = function (opts) {
    return new L.Control.Spawn(opts);
}
