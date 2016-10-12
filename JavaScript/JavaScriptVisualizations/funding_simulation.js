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

// Execute Draw
drawMain(simulationSpeed = 0.01) //smaller = faster.

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
var institution;

// var currentUniFund = {};
var fundsDict = {};
var funderColors = {};
var grantMovements = [];

setup(width, height);
function setup(width, height){
    projection = d3.geo.mercator()
                       .translate([(width/1.45), (height/1)])
                       .scale(width / 1.35 / Math.PI);

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

//DateBox

function addDate() {
    var text = svg.append("text")
        .attr("x", 2000)
        .attr("y", 1050)
        .attr("dy", ".35em")
        .attr("text-anchor", "middle")
        .style("font", "300 100px Helvetica Neue")
        .text("Starting");
}

//----------------------------------------------------------------------------------------//

//Simulation Machinery



function transition(grantMovement, route, dest, newAmountRaw, doDraw) {
    var l = route.node().getTotalLength();
    grantMovement.transition()
        .duration(l * 40)
        .attrTween("transform", delta(grantMovement, route.node()))
        .each("end", function() {
            console.log("try")
            if (doDraw == true) {
                console.log("win")

                var institution = g.append("g").attr("class", "institution");
                var location = projection(fundsDict[dest]);
                var trueSize;
                var trueSizeScale = 0.000000001;

                institution.append("svg:circle")
                    .attr("cx", location[0])
                    .attr("cy", location[1])
                    .attr("class", "point")
                    .style("fill", "white")
                    .style("opacity", 0.05)
                    .attr("r", function (d, i) {
                        var oldAmount = d3.select(this).attr('id');
                        trueSize = (oldAmount + newAmountRaw);
                        if (trueSize * trueSizeScale < 0.5) {
                            return 0.5;
                        } else {
                            return trueSize * trueSizeScale;
                        }
                    })
                    .attr("id", newAmountRaw)
                    .on("mouseover", function () {
                        div.transition()
                            .duration(500)
                            .style("opacity", .85); //opacity of the tooltip
                        div.html(dest + "</br>" + "Total Funding to Date: " + accounting.formatMoney(trueSize) + " USD")
                            .style("left", (d3.event.pageX) + "px")
                            .style("top", (d3.event.pageY - 28) + "px");
                    })
                    .on("mouseout", function (d) {
                        div.transition()
                            .duration(500)
                            .style("opacity", 0);
                    });
            } else{
                console.log("lose")
            }
            route.remove();
        })
        .remove();
}

function delta(grantMovement, path) {
    var l = path.getTotalLength();
    var grantMovement = grantMovement;
    return function(i) {
        return function(t) {
            var p = path.getPointAtLength(t * l);

            var t2 = Math.min(t + 0.05, 1);
            var p2 = path.getPointAtLength(t2 * l);

            var x = p2.x - p.x;
            var y = p2.y - p.y;

            var s = Math.min(Math.sin(Math.PI * t) * 0.7, 0.3);

            return "translate(" + p.x + "," + p.y + ") scale(" + s + ")";
        }
    }
}

function fly(origin, destination, color, r, newAmountRaw, doDraw) {
    var route = g.append("path")
                   .attr("fill-opacity", 0)
                   .datum({type: "LineString", coordinates: [fundsDict[origin], fundsDict[destination]]})
                   .attr("class", "route")
                   .attr("d", path);

    var grantMovement = g.append("svg:circle")
                            .attr("class", "grantMovement")
                            .attr("fill", color)
                            .attr("r", r)
                            .attr("fill-opacity", 0.85);

    transition(grantMovement, route, destination, newAmountRaw, doDraw);
}

function flyMaster(inputData, movementRate){
    var i = 0;
    var priorReceps = [];
    var doDraw = false;
    setInterval(function() {
        if (i > inputData.length - 1) {
            // console.log("Complete")
            i = 0;
        }
        doDraw = false;
        var od = inputData[i];
        if ($.inArray(od[0], priorReceps) == -1){
            priorReceps.push(od[1])
            doDraw = true
        }
        fly(od[0], od[1], funderColors[od[0]], od[3], od[4], doDraw);

        //Update Date
        d3.selectAll('text').text(od[2]);
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
                .style("fill", "#383838");

        d3.csv("data/funder_db.csv", function(error, funder){
            funder.forEach(function (i) {
                addPoints(i['lng'], i['lat'], 8, i['funder'], colorOverride = i['colour'], infoOverride = true, opacityOveride = 1);
                fundsDict[i['funder']] = [i['lng'], i['lat']].map(parseFloat);
                funderColors[i['funder']] = i['colour']
            })

            d3.csv("data/funding_sample.csv", function(error, funder){
                funder.forEach(function (i) {

                    var amount = parseFloat(i['NormalizedAmount']);
                    
                    var fromPoint = [i['lng'], i['lat']];
                    var toPoint = [i['lngFunder'], i['latFunder']];
                    routesToDraw.push(fromPoint);  // must be left
                    routesToDraw.push(toPoint);    // as strings

                    //Add Org
                    fundsDict[i['OrganizationName']] = [i['lng'], i['lat']].map(parseFloat);

                    //Add Movement of Fund
                    grantMovements.push([i['FunderNameFull'],
                                         i['OrganizationName'],
                                         i['StartDate'],
                                         Math.sqrt(amount/Math.PI) * 0.009,
                                         amount
                    ]);
                })
                //Add DateBox
                addDate();

                // ***Run the Simulation*** ///
                flyMaster(grantMovements, simulationSpeed);
            });
        });
    });
}

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

function circleDomAppend(appendTo, x, y, color, opacity, id, r, info){
    appendTo.append("svg:circle")
            .attr("cx", x)
            .attr("cy", y)
            .attr("class","point")
            .style("fill", color)
            // .style("stroke", "white")
            .style("opacity", opacity)
            .attr("id", id)
            .attr("r", r)
            .on("mouseover", function(){
                div.transition()
                    .duration(500)
                    .style("opacity", .85); //opacity of the tooltip
                div.html(info)
                    .style("left", (d3.event.pageX) + "px")
                    .style("top", (d3.event.pageY - 28) + "px");
                    })
            .on("mouseout", function(d){
                div.transition()
                    .duration(500)
                    .style("opacity", 0);
            });
}

//function to add points and text to the map (used in plotting grants)
function addPoints(lat, lon, amount, name, colorOverride, infoOverride, opacityOverride) {

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

    if (opacityOverride == false){
        var opacity = 0.55;
    } else if (opacityOverride != false){
        var opacity = opacityOverride;
    }

    // gpoint.append("svg:circle")
    //     .attr("cx", x)
    //     .attr("cy", y)
    //     .attr("class","point")
    //     .style("fill", toColor)
    //     .style("opacity", opacity)
    //     .attr("id", amountInitialScale)
    //     .attr("r", amountInitialScale)
    //     .on("mouseover", function(){
    //         div.transition()
    //             .duration(500)
    //             .style("opacity", .85);
    //         div.html(objectInfo)
    //             .style("left", (d3.event.pageX) + "px")
    //             .style("top", (d3.event.pageY - 28) + "px");
    //             })
    //     .on("mouseout", function(d){
    //         div.transition()
    //             .duration(500)
    //             .style("opacity", 0);
    //     });

    circleDomAppend(gpoint, x, y, toColor, opacity, amountInitialScale, amountInitialScale, objectInfo);
}

function redraw() {
    width = document.getElementById('container').offsetWidth;
    height = width / 2;
    d3.select('svg').remove();
    setup(width, height);
//    drawMain();
}

function pointScale(amount, zoomScale){
    var rawFloor = 0.09;
    var size = amount * (100/zoomScale*0.05);

    if (size > amount) {
        return amount;
        // } else if (size < rawFloor){
        //         return rawFloor*amount;
        //  }
    } else {
        return size;
    }
}

var bbox;
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

    // circle size based on zoom level.
    // TO DO: only scale points in view
    d3.selectAll('.gpoint').selectAll('circle').attr('r', function (d, i){
        var amount = d3.select(this).attr('id');
        return pointScale(amount, s);
    });

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











