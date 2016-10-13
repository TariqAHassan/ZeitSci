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

var zoom = d3.behavior.zoom()
                      .scaleExtent([1, 5000])
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
    var startingWidth = document.getElementById('container').offsetWidth
    var text = svg.append("text")
                    .attr("x", startingWidth - 300)
                    .attr("y", (startingWidth / 2) - 80)
                    .attr("dy", ".35em")
                    .attr("text-anchor", "middle")
                    .style("font", "300 100px Helvetica Neue")
                    .text("Starting");
}

//----------------------------------------------------------------------------------------//

//Simulation Machinery

function logistic_fn(x, minValue, maxValue, curveSteepness){
    // Algorithm to scale points using a Logistic Function.

    // See: https://en.wikipedia.org/wiki/Logistic_function
    // Notes:
    //     (a) x *must* be >= 0.
    //     (b) x_0 is left as 0 to center the function about x = 0.
    //     (c) '-L/2' was added to center the function about y = 0.
    //     (d) curveSteepness should be set to be ~= 1.

    // maxAmount (Order of Magitude) / 10
    var maxOrderOfMag = Math.pow(10, parseInt(Math.log10(maxValue)) - 1);
    var scaleBy = maxOrderOfMag * 2

    var k = curveSteepness;
    var L = maxValue/scaleBy;
    var denominator = 1 + Math.pow(Math.E, -1 * k * (x/scaleBy));

    return L/denominator - L/2 + minValue
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

var institution = g.append("g").attr("class", "institution");;
function transition(grantMovement, route, id, dest, doDraw, largestTotalGrants, realTimeFundingInfo) {
    var l = route.node().getTotalLength();
    grantMovement.transition()
        .duration(l * 10)
        .attrTween("transform", delta(grantMovement, route.node()))
        .each("end", function() {

            var sizeFloor = 1.5
            // var s = d3.event.scale; //Add to adjust radius based on current zoom
            var idClean = "loc" + id.replace(/[^0-9a-z]/gi, '');

            //Scale the funding using the logistic function
            var scaledRadius = logistic_fn(x = realTimeFundingInfo[id], sizeFloor, largestTotalGrants, 0.5)
            var zoomAdjustRadius = scaledRadius;

            if (doDraw === true) {
                var location = projection(fundsDict[dest]);
                institution = g.append("g").attr("class", "institution");
                institution.append("svg:circle")
                            .attr("cx", location[0])
                            .attr("cy", location[1])
                            .attr("class", "point")
                            .attr("id", idClean)
                            .attr("r", zoomAdjustRadius)
                            .datum(zoomAdjustRadius)
                            .style("fill", "white")
                            .style("opacity", 0.25);
            } else {
                d3.selectAll(".institution")
                    .select("#" + idClean)
                    .attr('r', zoomAdjustRadius)
                    .datum(zoomAdjustRadius);
            }
            route.remove();
        })
        .remove(); //applies to the route
}

function fly(origin, destination, color, id, r, doDraw, largestTotalGrants, realTimeFundingInfo) {
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

    transition(grantMovement, route, id, destination, doDraw, largestTotalGrants, realTimeFundingInfo);
}

function flyMaster(inputData, largestTotalGrants, movementRate){

    var doDraw = false;
    var priorReceps = [];
    var realTimeFundingInfo = {};

    var i = 0;
    setInterval(function()
    {
        if (i > inputData.length - 1) {
            i = 0;
            // var realTimeFundingInfo = {};
        }
        doDraw = false;
        var od = inputData[i];
        if (priorReceps.indexOf(od[5]) == -1){
            priorReceps.push(od[5]);
            doDraw = true;
            realTimeFundingInfo[od[5]] = od[4]
        } else {
            realTimeFundingInfo[od[5]] += od[4]
        }
        fly(od[0], od[1], funderColors[od[0]], od[5], od[3], doDraw, largestTotalGrants, realTimeFundingInfo);

        //Update Date
        d3.selectAll('text').text(od[2]);
        i++;
    }
    , movementRate);
}

//----------------------------------------------------------------------------------------//

function valuesFromObject(inputObject){
    //See: http://stackoverflow.com/a/25797464/4898004.
    return Object.keys(inputObject).map(function(key){return inputObject[key]})
}


function drawMain(simulationSpeed) {
    var routesToDraw = [];
    var orgFundingInfoTemp = {};

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
                addFunderPoints(i['lng'], i['lat'], 10, i['funder'], colorOverride = i['colour'], infoOverride = true, opacityOveride = 1);
                fundsDict[i['funder']] = [i['lng'], i['lat']].map(parseFloat);
                funderColors[i['funder']] = i['colour']
            })

            d3.csv("data/funding_sample.csv", function(error, funder){
                funder.forEach(function (d) {

                    var amount = parseFloat(d['NormalizedAmount']);
                    var uniqueToGeo = (d['lng'] + d['lat']).replace(/ /g,'')

                    //Update Grants in the database.
                    if (orgFundingInfoTemp[uniqueToGeo] = undefined){
                        orgFundingInfoTemp[uniqueToGeo] = amount
                    } else {
                        orgFundingInfoTemp[uniqueToGeo] += amount
                    }

                    var fromPoint = [d['lng'], d['lat']];
                    var toPoint = [d['lngFunder'], d['latFunder']];
                    routesToDraw.push(fromPoint);  // these must be
                    routesToDraw.push(toPoint);    // left as strings

                    //Add Org
                    fundsDict[d['OrganizationName']] = [d['lng'], d['lat']].map(parseFloat);

                    //Add Movement of Fund
                    grantMovements.push([d['FunderNameFull'],
                                         d['OrganizationName'],
                                         d['StartDate'],
                                         Math.sqrt(amount/Math.PI) * 0.009,
                                         amount,
                                         uniqueToGeo
                    ]);
                })
                //Add DateBox
                addDate();

                //Work out the largest grant for a single Org.
                var largestGrantSingleOrg = Math.max.apply(null, valuesFromObject(orgFundingInfoTemp))

                // ***Run the Simulation*** ///
                flyMaster(grantMovements, 4415802947.2, simulationSpeed);

                //Clear orgFundingInfoTemp from memory
                orgFundingInfoTemp = [];
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
function addFunderPoints(lat, lon, amount, name, colorOverride, infoOverride, opacityOverride) {

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
        var opacity = 0.70;
    } else if (opacityOverride != false){
        var opacity = opacityOverride;
    }

    circleDomAppend(gpoint, x, y, toColor, opacity, amountInitialScale, amountInitialScale, objectInfo);
}

function redraw() {
    //TO DO:
    //Add Time Box scaling
    //Correct window resize (i.e., edit setup
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

    // circle size based on zoom level.
    // TO DO: only scale points in view
    d3.selectAll('.gpoint').selectAll('circle').attr('r', function (d, i){
        var currentAmount = d3.select(this).attr('id');
        return pointScale(currentAmount, s);
    });

    d3.selectAll('.institution').selectAll('circle').attr('r', function (d, i){
        var currentAmount = d3.select(this).datum();
        // console.log(d3.select(this).datum());
        return pointScale(currentAmount, s);
    });

    //Correct the routes for zooming and panning
    g.selectAll(".route")
        .attr("transform", transformCmd)
        .attr("d", path.projection(projection));

    return s
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
//     console.log(projection.invert(d3.mouse(this)));
}


// Execute Draw
drawMain(simulationSpeed = 0.01) //smaller = faster.











