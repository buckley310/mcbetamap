L.control.beds = function (opts) {

    let ctrl = L.Control.extend({
        onAdd: map => {
            var c = L.DomUtil.create('select');
            c.innerHTML = '<option>Select a bed...</option>';

            L.DomEvent.on(c, 'change', e => {
                let coord = e.target.value.split(',');
                map.setView([-parseInt(coord[1]), parseInt(coord[0])]);
            });

            for (let b of opts.beds.sort((a, b) => a.z - b.z)) {
                let op = L.DomUtil.create('option');
                op.value = b.x + ',' + b.z;
                op.textContent =
                    new Date(b.time * 1000).toLocaleDateString() +
                    ` - (${b.x}, ${b.z})`;
                c.appendChild(op);
            }

            return c;
        }
    });

    return new ctrl(opts);
};
