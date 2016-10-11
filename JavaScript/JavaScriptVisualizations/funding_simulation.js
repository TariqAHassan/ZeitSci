/**
 * Created by Tariq on 2016-10-11.
 *
 * CURRENLY UNDER DEVELOPMENT.
 * BUG: Does not play nice with Safari (feature? :)
 */

// Sources:
// 1. http://techslides.com/d3-map-starter-kit
// 2. http://www.tnoda.com/blog/2014-04-02

d3.select(window).on("resize", throttle);

var zoomExtent = [1, 5000];
var zoom = d3.behavior.zoom()
                      .scaleExtent(zoomExtent)
                      .on("zoom", zoomer);

var width = document.getElementById('container').offsetWidth;
var height = width / 2;

// Define the div for the tooltip
var div = d3.select("body").append("div")
                           .attr("class", "tooltip")
                           .style("opacity", 0);

//Init
var topo, projection, path, svg, g;
var fundsDict = {};
var grantMovements = [];

setup(width, height);
function setup(width, height){
    projection = d3.geo.mercator()
                      .translate([(width/2), (height/1.2)])
                      .scale(width / 2 / Math.PI);

    path = d3.geo.path().projection(projection);

    svg = d3.select("#container").append("svg")
            .attr("width", width)
            .attr("height", height)
            .call(zoom)
            .on("click", click)
            .append("g");

    g = svg.append("g");
}

//----------------------------------------------------------------------------------------//

function transition(plane, route) {
    var l = route.node().getTotalLength();
    plane.transition()
        .duration(l * 50)
        .attrTween("transform", delta(plane, route.node()))
        .each("end", function() {
            route.remove();
        })
        .remove();
}

function delta(plane, path) {
    var l = path.getTotalLength();
    var plane = plane;
    return function(i) {
        return function(t) {
            var p = path.getPointAtLength(t * l);

            var t2 = Math.min(t + 0.05, 1);
            var p2 = path.getPointAtLength(t2 * l);

            var x = p2.x - p.x;
            var y = p2.y - p.y;
            var r = 90 - Math.atan2(-y, x) * 180 / Math.PI;

            var s = Math.min(Math.sin(Math.PI * t) * 0.7, 0.3);

            return "translate(" + p.x + "," + p.y + ") scale(" + s + ") rotate(" + r + ")";
        }
    }
}

function fly(origin, destination) {
    var route = g.append("path")
    //                   .attr("stroke", "black") // Odd scaling if this is turned on...but off, the simulation looks fine. Weird.
                   .attr("fill-opacity", 0)
                   .datum({type: "LineString", coordinates: [fundsDict[origin], fundsDict[destination]]})
                   .attr("class", "route")
                   .attr("d", path);

    var plane = g.append("path")
                    .attr("class", "plane")
                    .attr("id", [30, 30])
                    .attr("d", "m25.21488,3.93375c-0.44355,0 -0.84275,0.18332 -1.17933,0.51592c-0.33397,0.33267 -0.61055," +
                            "0.80884 -0.84275,1.40377c-0.45922,1.18911 -0.74362,2.85964 -0.89755,4.86085c-0.15655," +
                            "1.99729 -0.18263,4.32223 -0.11741,6.81118c-5.51835,2.26427 -16.7116,6.93857 -17.60916," +
                            "7.98223c-1.19759,1.38937 -0.81143,2.98095 -0.32874,4.03902l18.39971,-3.74549c0.38616," +
                            "4.88048 0.94192,9.7138 1.42461,13.50099c-1.80032,0.52703 -5.1609,1.56679 -5.85232," +
                            "2.21255c-0.95496,0.88711 -0.95496,3.75718 -0.95496,3.75718l7.53,-0.61316c0.17743," +
                            "1.23545 0.28701,1.95767 0.28701,1.95767l0.01304,0.06557l0.06002,0l0.13829,0l0.0574," +
                            "0l0.01043,-0.06557c0,0 0.11218,-0.72222 0.28961,-1.95767l7.53164,0.61316c0,0 0," +
                            "-2.87006 -0.95496,-3.75718c-0.69044,-0.64577 -4.05363,-1.68813 -5.85133,-2.21516c0.48009," +
                            "-3.77545 1.03061,-8.58921 1.42198,-13.45404l18.18207,3.70115c0.48009,-1.05806 0.86881," +
                            "-2.64965 -0.32617,-4.03902c-0.88969,-1.03062 -11.81147,-5.60054 -17.39409,-7.89352c0.06524," +
                            "-2.52287 0.04175,-4.88024 -0.1148,-6.89989l0,-0.00476c-0.15655,-1.99844 -0.44094," +
                            "-3.6683 -0.90277,-4.8561c-0.22699,-0.59493 -0.50356,-1.07111 -0.83754,-1.40377c-0.33658," +
                            "-0.3326 -0.73578,-0.51592 -1.18194,-0.51592l0,0l-0.00001,0l0,0z");

    transition(plane, route);
}

function flyMaster(inputData, movementRate){
        var i = 0;
        setInterval(function() {
            if (i > inputData.length - 1) {
                i = 0;
                console.log("loop complete")
            }
            var od = inputData[i];
            fly(od[0], od[1]);
            i++;
        }, movementRate);
}

//----------------------------------------------------------------------------------------//

function drawMain(simulationSpeed) {
    var routesToDraw = [];

    d3.json("data/starter_kit/data/world-topo-min.json", function(error, world) {
        var countries = topojson.feature(world, world.objects.countries).features;
        topo = countries;

        var country = g.selectAll(".country").data(topo);
        country.enter().insert("path")
                .attr("class", "country")
                .attr("d", path)
                .style("fill", "gray");

        d3.csv("data/funder_db.csv", function(error, funder){
            funder.forEach(function (i) {
                addPoints(i['lng'], i['lat'], 4.5, i['funder'], colorOverride = 'black', infoOverride = true);
                fundsDict[i['funder']] = [i['lng'], i['lat']].map(parseFloat);
            })

            d3.csv("data/funding_sample.csv", function(error, funder){
                funder.forEach(function (i) {

                    var fromPoint = [i['lng'], i['lat']];
                    var toPoint = [i['lngFunder'], i['latFunder']];
                    routesToDraw.push(fromPoint);
                    routesToDraw.push(toPoint);

                    //Add Org
                    fundsDict[i['OrganizationName']] = [i['lng'], i['lat']].map(parseFloat);

                    //Add Movement of Fund
                    grantMovements.push([i['FunderNameFull'], i['OrganizationName']]);

                })

                // ***Run the Simulation*** ///
                flyMaster(grantMovements, simulationSpeed);

            });
        });
    });
}

// Execute Draw
drawMain(simulationSpeed = 0.25)

function dotColor(amount){
  if (parseFloat(amount) < 10000000){
      return 'darkred'
  } else if (parseFloat(amount) >  10000000 && parseFloat(amount)  < 100000000){
      return 'red'
  } else if (parseFloat(amount) >= 100000000 && parseFloat(amount) < 500000000){
      return 'yellow'
  } else if (parseFloat(amount) >= 500000000 && parseFloat(amount) < 1000000000){
      return 'lightgreen'
  } else if (parseFloat(amount) >= 1000000000){
      return 'green'
  }
}

//function to add points and text to the map (used in plotting grants)
function addPoints(lat, lon, amount, name, colorOverride, infoOverride) {

    var gpoint = g.append("g").attr("class", "gpoint");

    var location = projection([lat, lon]);
    var x = location[0];
    var y = location[1];

    if (infoOverride != false) {
        var amountInitialScale = amount;
        var objectInfo = name;
    } else if (infoOverride == false) {
        var amountInitialScale = Math.sqrt(parseFloat(amount) * 0.0000099);
        var objectInfo = name + "<br/>" + "Grant Amount: " + accounting.formatMoney(parseFloat(amount)) + " USD";
    }

    if (colorOverride == false) {
        var toColor = dotColor(parseFloat(amount));
    } else {
        var toColor = colorOverride;
    }

    gpoint.append("svg:circle")
        .attr("cx", x)
        .attr("cy", y)
        .attr("class","point")
        .style("fill", toColor)
        .style("opacity", 0.55)
        .attr("id", amountInitialScale)
        .attr("r", amountInitialScale)
        .on("mouseover", function(){
            div.transition()
                .duration(500)
                .style("opacity", .85);
            div.html(objectInfo)
                .style("left", (d3.event.pageX) + "px")
                .style("top", (d3.event.pageY - 28) + "px");
                })
        .on("mouseout", function(d){
            div.transition()
                .duration(500)
                .style("opacity", 0);
        });
}

function redraw() {
    width = document.getElementById('container').offsetWidth;
    height = width / 2;
    d3.select('svg').remove();
    setup(width, height);
//    drawMain();
}

function pointScale(amount, zoomScale){
    var rawFloor = 0.01;
    var sizeFloor = rawFloor*amount;
    var size = 0.5 * amount * (100/zoomScale*0.05);

    if (size > amount){
        return amount;
    //        } else if (size < rawFloor){
    //            return sizeFloor;
    } else {
        return size;
    }
}

function zoomer() {
    var t = d3.event.translate;
    var s = d3.event.scale;
    var h = height/4;

    t[0] = Math.min(
      (width/height)  * (s - 1),
       Math.max(width * (1 - s), t[0])
    );

    t[1] = Math.min(
      h * (s - 1) + h * s,
      Math.max(height  * (1 - s) - h * s, t[1])
    );

    var transformCmd = "translate(" + t + ")scale(" + s + ")"
    g.attr("transform", transformCmd);

    //circle size based on zoom level
    d3.selectAll('circle').attr('r', function (d, i){
    //        TO DO: only scale points in view
    //        console.log(d3.geo.bounds(topo[0]))
    //        var x = d3.select(this).attr('cx');
    //        var y = d3.select(this).attr('cy');
        var amount = d3.select(this).attr('id');
        return pointScale(amount, s);
    });

//    d3.selectAll('plane').attr('', function (d, i){
//        var amount = d3.select(this).attr('id');
//        return pointScale(amount, s);
//    });

    //Correct the routes for zooming and panning
    g.selectAll(".route")
        .attr("transform", transformCmd)
        .attr("d", path.projection(projection));
}

var throttleTimer;
function throttle() {
    window.clearTimeout(throttleTimer);
    throttleTimer = window.setTimeout(function() {
    redraw();
    }, 200);
}

//geo translation on mouse click in map
function click() {
//    console.log(projection(d3.mouse(this)));
    console.log(projection.invert(d3.mouse(this)));
}












