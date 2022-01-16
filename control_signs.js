L.control.signs = function (opts) {

    let ctrl = L.Control.extend({
        onAdd: map => {
            var c = L.DomUtil.create('select');
            c.innerHTML = '<option>Select a sign...</option>';

            L.DomEvent.on(c, 'change', e => {
                let coord = e.target.value.split(',');
                map.setView([-parseInt(coord[1]), parseInt(coord[0])]);
            });

            for (let s of opts.signs.sort((a, b) => a.z - b.z)) {
                let op = L.DomUtil.create('option');
                op.value = s.x + ',' + s.z;
                op.textContent =
                    new Date(s.time * 1000).toLocaleDateString() +
                    ` - (${s.x}, ${s.z}) - ` +
                    s.text.join(', ');
                c.appendChild(op);
            }

            return c;
        }
    });

    return new ctrl(opts);
};
