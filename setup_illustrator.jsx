// Miko Studio Slicer: Illustrator workspace builder (ExtendScript)
#target illustrator
(function () {
    var W = 1920, H = 1080;
    var d = app.documents.add(DocumentColorSpace.RGB, W, H);
    d.rulerUnits = RulerUnits.Pixels;
    var names = ["Guides", "Text", "Shapes", "Cutouts", "Source"];
    for (var i = 0; i < names.length; i++) {
        var l = (i === 0) ? d.layers[0] : d.layers.add();
        l.name = names[i];
    }
    var g = d.layers.getByName("Guides");
    function guide(x, y, w, h) {
        var r = g.pathItems.rectangle(-y, x, w, h);
        r.filled = false; r.stroked = false; r.guides = true;
    }
    guide(0, 0, W, H);
    guide(W * 0.05, H * 0.05, W * 0.9, H * 0.9);
    guide(W * 0.1, H * 0.1, W * 0.8, H * 0.8);
    g.locked = true;
    d.layers.getByName("Source").locked = false;
    alert("Miko Studio Slicer workspace ready: " + W + " x " + H + " with action-safe and title-safe guides.");
})();
