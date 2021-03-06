'use strict';

let viewX = 0;
let viewY = 0;
let viewZoomOut = 1;
let viewZoomIn = 1;

let tiles;
let signs;
let beds;

let map_view = document.getElementById('map_view');

let dragActive = false;
let dragMouseStartX = 0;
let dragMouseStartY = 0;
let dragViewStartX = 0;
let dragViewStartY = 0;

let flyInterval;

function findTilesInsideViewport() {
    let viewTop = viewY / viewZoomOut - map_view.clientHeight / 2 / viewZoomIn;
    let viewLeft = viewX / viewZoomOut - map_view.clientWidth / 2 / viewZoomIn;
    let viewRight = viewX / viewZoomOut + map_view.clientWidth / 2 / viewZoomIn;
    let viewBottom = viewY / viewZoomOut + map_view.clientHeight / 2 / viewZoomIn;

    let vtiles = {};

    for (let x = Math.floor(viewLeft / 512); x <= Math.floor(viewRight / 512); x++) {
        for (let y = Math.floor(viewTop / 512); y <= Math.floor(viewBottom / 512); y++) {
            vtiles[`${x},${y}`] = [x, y];
        }
    }
    return vtiles;
}

function render() {
    document.getElementById('map_coords').textContent = `${parseInt(viewX)}, ${parseInt(viewY)}`;
    document.getElementById('zoom_value').textContent = `${viewZoomIn / viewZoomOut}x zoom`;

    let wantedTiles = findTilesInsideViewport();

    // add tiles that should be on-screen, if they dont already exist
    for (let i in wantedTiles) {
        let x = wantedTiles[i][0];
        let y = wantedTiles[i][1];
        if (tiles[`${x} ${y} ${viewZoomOut}`] && !document.getElementById(`map_tile,${x},${y},${viewZoomOut}`)) {

            let ph = document.createElement('img');
            ph.src = './tile_placeholder.png';
            ph.id = `map_tile,${x},${y},${viewZoomOut},placeholder`;
            ph.className = "map_tile";
            map_view.appendChild(ph);

            let im = document.createElement('img');
            im.addEventListener('load', () => { ph.outerHTML = ''; });
            im.src = `./data/tiles_${viewZoomOut}/r.${x}.${y}.png`;
            im.id = `map_tile,${x},${y},${viewZoomOut}`;
            im.className = "map_tile";
            map_view.appendChild(im);
        }
    }

    // remove tiles that are off-screen
    let removeTiles = [];
    for (let tile of document.getElementsByClassName('map_tile')) {
        let tid = tile.id.split(',');
        let x = parseInt(tid[1]);
        let y = parseInt(tid[2]);
        let zoom = parseInt(tid[3]);

        if (zoom != viewZoomOut || !wantedTiles[`${x},${y}`]) {
            removeTiles.push(tile);
        }
    }
    for (let tile of removeTiles) tile.outerHTML = '';

    map_view.style.transform = `scale(${viewZoomIn})`;
    let origin_left = map_view.clientWidth / 2 - viewX / viewZoomOut;
    let origin_top = map_view.clientHeight / 2 - viewY / viewZoomOut;
    for (let tile of document.getElementsByClassName('map_tile')) {
        let tid = tile.id.split(',');
        let x = parseInt(tid[1]);
        let y = parseInt(tid[2]);
        tile.style.left = origin_left + 512 * x + 'px';
        tile.style.top = origin_top + 512 * y + 'px';
    }
}

function fly_to(dstX, dstY) {
    if (!Number.isFinite(dstX) || !Number.isFinite(dstY)) return;

    if (flyInterval) clearInterval(flyInterval);

    if (Math.abs(dstX - viewX) > 10000 * viewZoomOut || Math.abs(dstY - viewY) > 10000 * viewZoomOut) {
        // flying really far might download a lot of tiles. just teleport.
        viewX = dstX;
        viewY = dstY;
        return render();
    }

    let animTime = 500;
    let flycb;
    let flyStartTime = (new Date).getTime();
    let flyStartX = viewX;
    let flyStartY = viewY;
    flycb = () => {
        let now = (new Date).getTime();
        if (flyStartTime + animTime < now) {
            clearInterval(flyInterval);
            viewX = dstX;
            viewY = dstY;
            render();
        } else {
            let animProgress = 1 - Math.pow(1 - (now - flyStartTime) / animTime, 3);
            viewX = flyStartX + animProgress * (dstX - flyStartX);
            viewY = flyStartY + animProgress * (dstY - flyStartY);
            render();
        }
    };
    flyInterval = setInterval(flycb, 1);
}

function init() {
    addEventListener('resize', render);
    render();

    {//handle drag-panning
        document.getElementById('map_view').addEventListener('touchstart', e => {
            console.log(e);
            dragActive = true;
            dragMouseStartX = e.touches[0].clientX;
            dragMouseStartY = e.touches[0].clientY;
            dragViewStartX = viewX;
            dragViewStartY = viewY;
        });
        document.getElementById('map_view').addEventListener('mousedown', e => {
            e.preventDefault();
            dragActive = true;
            dragMouseStartX = e.clientX;
            dragMouseStartY = e.clientY;
            dragViewStartX = viewX;
            dragViewStartY = viewY;
        });

        addEventListener('mouseup', e => { dragActive = false; });
        addEventListener('touchend', e => { dragActive = false; });

        addEventListener('touchmove', e => {
            if (dragActive) {
                viewX = dragViewStartX + (dragMouseStartX - e.touches[0].clientX) * viewZoomOut / viewZoomIn;
                viewY = dragViewStartY + (dragMouseStartY - e.touches[0].clientY) * viewZoomOut / viewZoomIn;
                render();
            }
        });
        addEventListener('mousemove', e => {
            if (dragActive) {
                viewX = dragViewStartX + (dragMouseStartX - e.clientX) * viewZoomOut / viewZoomIn;
                viewY = dragViewStartY + (dragMouseStartY - e.clientY) * viewZoomOut / viewZoomIn;
                render();
            }
        });
    }

    document.getElementById('gotospawn').addEventListener('click', () => {
        fly_to(0, 0);
    });

    { // Populate drop-downs
        for (let s of signs.sort((a, b) => a.time - b.time)) {
            let op = document.createElement('option');
            op.value = s.x + ',' + s.z;
            op.textContent =
                new Date(s.time * 1000).toLocaleDateString() +
                ` - (${s.x}, ${s.z}) - ` +
                s.text.join(', ');
            document.getElementById('map_signs').appendChild(op);
        }
        document.getElementById('map_signs').addEventListener('change', e => {
            let coord = e.target.value.split(',');
            fly_to(parseInt(coord[0]), parseInt(coord[1]));
        });

        for (let b of beds.sort((a, b) => a.time - b.time)) {
            let op = document.createElement('option');
            op.value = b.x + ',' + b.z;
            op.textContent =
                new Date(b.time * 1000).toLocaleDateString() +
                ` - (${b.x}, ${b.z})`;
            document.getElementById('map_beds').appendChild(op);
        }
        document.getElementById('map_beds').addEventListener('change', e => {
            let coord = e.target.value.split(',');
            fly_to(parseInt(coord[0]), parseInt(coord[1]));
        });
    }

    { // handle drop-down previous/next buttons
        document.getElementById('prevsign').addEventListener('click', () => {
            let sel = document.getElementById('map_signs');
            if (sel.selectedIndex) {
                sel.selectedIndex--;
                sel.dispatchEvent(new Event('change'));
            }
        });
        document.getElementById('nextsign').addEventListener('click', () => {
            let sel = document.getElementById('map_signs');
            if (sel.selectedIndex < sel.childElementCount - 1) {
                sel.selectedIndex++;
                sel.dispatchEvent(new Event('change'));
            }
        });
        document.getElementById('prevbed').addEventListener('click', () => {
            let sel = document.getElementById('map_beds');
            if (sel.selectedIndex) {
                sel.selectedIndex--;
                sel.dispatchEvent(new Event('change'));
            }
        });
        document.getElementById('nextbed').addEventListener('click', () => {
            let sel = document.getElementById('map_beds');
            if (sel.selectedIndex < sel.childElementCount - 1) {
                sel.selectedIndex++;
                sel.dispatchEvent(new Event('change'));
            }
        });
    }

    { // handle zoom buttons
        let zoomIn = () => {
            if (viewZoomOut > 1) {
                viewZoomOut >>= 1;
            }
            else if (viewZoomIn < 32) {
                viewZoomIn <<= 1;
            }
            render();
        };
        let zoomOut = () => {
            if (viewZoomIn > 1) {
                viewZoomIn >>= 1;
            }
            else if (viewZoomOut < 256) {
                viewZoomOut <<= 1;
            }
            render();
        };
        document.getElementById('zoom_in').addEventListener('click', zoomIn);
        document.getElementById('zoom_out').addEventListener('click', zoomOut);
        addEventListener('wheel', e => (e.deltaY < 0 ? zoomIn : zoomOut)());
    }
}

addEventListener('load', function () {
    fetch('./data/data.json')
        .then(r => r.json())
        .then(j => {
            signs = j.signs;
            beds = j.beds;
            tiles = {};
            for (let zoom in j.tiles) {
                j.tiles[zoom].map(x => { tiles[`${x[0]} ${x[1]} ${zoom}`] = true; });
            }
            init();
        });
});