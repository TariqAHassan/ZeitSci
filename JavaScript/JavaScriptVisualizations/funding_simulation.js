/**
 * Created by Tariq on 2016-10-11.
 *
 * CURRENLY UNDER DEVELOPMENT.
 * BUG: Does not play nice with Safari (feature? :)
 */

//----------------------------------------------------------------------------------------//

// Sources:
// 1. http://techslides.com/d3-map-starter-kit
// 2. http://www.tnoda.com/blog/2014-04-02

//----------------------------------------------------------------------------------------//

//General Setup

d3.select(window).on("resize", throttle);

var zoom = d3.behavior.zoom()
                      .scaleExtent([1, 5000])
                      .on("zoom", zoomer);

var width = document.getElementById("container").offsetWidth;
var height = width / 2;

// Define the div for the tooltip
var div = d3.select("body").append("div")
                           .attr("class", "tooltip")
                           .style("opacity", 0);

//Init
var topo, projection, path, svg, g;
var fundsDict = {};
var funderColors = {};

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

//Tooltip Functionality

var tooltip = d3.select("#container")
                .append("div")
                .attr("class", "tooltip hidden");

function showTooltip(d, i, info, offsetL, offsetT){
    var mouse = d3.mouse(svg.node()).map(function(d) {
        return parseInt(d);
    });
    tooltip.classed("hidden", false)
        .attr("style", "left:"+(mouse[0]-offsetL)+"px;" +
                        "top:"+(mouse[1]+offsetT)+"px")
        .html(info)
        .style("font-size", "35px");
}

function hideTooltip(d, i){
     tooltip.classed("hidden", true);
}

//----------------------------------------------------------------------------------------//

//DateBox

//Pass the starting date
function addDate() {
    var startingContainerWidth = document.getElementById("container").offsetWidth
    var text = svg.append("text")
                    .attr("x", startingContainerWidth - 300)         // make these
                    .attr("y", (startingContainerWidth / 2) - 80)    // more robust.
                    .attr("dy", ".35em")
                    .attr("text-anchor", "middle")
                    .style("font", "Lucida Grande")
                    .style("font-size", "100px")
                    .text("01/01/2000");

    bbox = text[0][0].getBBox()

    var xWidthAdjust = 50;

    svg.insert('rect','text')
        .attr('x', bbox.x - xWidthAdjust/2)
        .attr('y', bbox.y)
        .attr('width', bbox.width + xWidthAdjust)
        .attr('height', bbox.height)
        .style("fill", "white")
        .style("opacity", 0.35);

    svg.append("text")
        .attr("x", startingContainerWidth - 300)         // make these
        .attr("y", (startingContainerWidth / 2) - 80)    // more robust.
        .attr("dy", ".35em")
        .attr("text-anchor", "middle")
        .style("font", "Lucida Grande")
        .style("font-size", "100px")
        .text("Starting");
}

//----------------------------------------------------------------------------------------//

//Dot Movement Machinery

function logistic_fn(x, minValue, maxValue, k, c){
    // Algorithm to scale points using a Logistic Function.
    // See: https://en.wikipedia.org/wiki/Logistic_function
    // Notes:
    //     (a) x *must* be >= 0.
    //     (b) x_0 is left as 0 to center the function about x = 0.
    //     (c) '-L/2' was added to center the function about y = 0.
    //     (d) curveSteepness (k) should be set to be ~= 1.
    // maxAmount (Order of Magnitude) / 10
    var maxOrderOfMag = Math.pow(10, parseInt(Math.log10(maxValue)) - 1);
    var scaleBy = maxOrderOfMag * c;

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

function terrestrialPoints(doDraw, grantToDraw, realTimeFundingInfo, largestTotalGrantByOrg){

    //Model Params
    var c = 0.8
    var k = 0.5
    var sizeFloor = 1.5

    //Set unique ID and the name of final location
    var locID = grantToDraw["recipientUniqueGeo"];
    var destination = grantToDraw["grantRecipientOrg"];

    //Construct the info for the Point
    var info = "<strong>" + destination + "</strong>" + "<br/>" +
                "<em>" + "Total Grants: " + "</em>" + accounting.formatMoney(parseFloat(grantToDraw["grantAmount"])) + " USD" + "<br/>" +
                "<em>" + "Date of Last Grant: " + "</em>" + grantToDraw["startDate"];

    // var s = d3.event.scale; //Add to adjust radius based on current zoom
    var idClean = "loc" + locID.replace(/[^0-9a-z]/gi, "");

    //Scale the funding using the logistic function
    var scaledRadius = logistic_fn(x = realTimeFundingInfo[locID], sizeFloor, largestTotalGrantByOrg, k, c)

    if (doDraw === true) {
        var institution = g.append("g").attr("class", "institution");
        var location = projection(fundsDict[destination]);
        institution = g.append("g").attr("class", "institution");
        institution.append("svg:circle")
                    .attr("cx", location[0])
                    .attr("cy", location[1])
                    .attr("class", "point")
                    .attr("id", idClean)
                    .attr("r", scaledRadius)
                    .datum(scaledRadius)
                    .style("fill", "white")
                    .style("opacity", 0.25)
                    .on("mousemove", function(d, i) {
                        showTooltip(d
                                    , i
                                    , info
                                    , document.getElementById('container').offsetLeft+20
                                    , document.getElementById('container').offsetTop+10
                    )})
                    .on("mouseout",  function(d, i){
                        hideTooltip(d, i)
                    });
    } else {
        d3.selectAll(".institution")
            .select("#" + idClean)
            .attr("r", scaledRadius)
            .datum(scaledRadius);
    }
}

function transition(grantMovement, route, grantToDraw, doDraw, largestTotalGrantByOrg, realTimeFundingInfo) {

    var l = route.node().getTotalLength();

    grantMovement.transition()
        .duration(l * 20)
        .attrTween("transform", delta(grantMovement, route.node()))
        .each("end", function() {
            //Delete the spent route.
            route.remove(); //remove the route used to guide the circle.

            //Add points on the Earth when the grants lands
            setTimeout(terrestrialPoints(doDraw, grantToDraw, realTimeFundingInfo, largestTotalGrantByOrg), 150);
        }).remove(); //remove the moving circle
}

function grantTranslate(grantToDraw, funderAbrev, doDraw, largestTotalGrantByOrg, realTimeFundingInfo) {
    
    var from = fundsDict[grantToDraw["funderName"]];
    var to = fundsDict[grantToDraw["grantRecipientOrg"]];
    
    var route = g.append("path")
                   .attr("fill-opacity", 0)
                   .datum({type: "LineString", coordinates: [from, to]})
                   .attr("class", "route")
                   .attr("d", path);

    var grantMovement = g.append("svg:circle")
                            .attr("class", "grantMovement")
                            .attr("fill", funderColors[grantToDraw["funderName"]])
                            .attr("r", grantToDraw["movingGrantRadius"])
                            .attr("fill-opacity", 0.85);

    transition(grantMovement, route, grantToDraw, doDraw, largestTotalGrantByOrg, realTimeFundingInfo);
}

function grantTranslateMaster(inputData, largestTotalGrantByOrg, largestIndividualGrant, movementRate, funderNameAbreviation){

    var doDraw = false;
    var priorReceps = [];
    var realTimeFundingInfo = {};

    var i = 0;
    var complete = false;
    var refreshIntervalId = setInterval(function(){
        if (i > inputData.length - 2) {
            // i = 0;
            complete = true;
        }

        doDraw = false;
        var grantToDraw = inputData[i];
        var funderAbrev = funderNameAbreviation[grantToDraw['funderName']];
        //merge this in


        if (priorReceps.indexOf(grantToDraw["recipientUniqueGeo"]) == -1){
            doDraw = true;
            priorReceps.push(grantToDraw["recipientUniqueGeo"]);

            realTimeFundingInfo[grantToDraw["recipientUniqueGeo"]] = grantToDraw["grantAmount"]
        } else {
            realTimeFundingInfo[grantToDraw["recipientUniqueGeo"]] += grantToDraw["grantAmount"]
        }

        grantTranslate(grantToDraw, funderAbrev, doDraw, largestTotalGrantByOrg, realTimeFundingInfo);

        //Update Date -- To Do: chec if it's the same first.
        d3.selectAll("text").text(grantToDraw["startDate"]);
        i++;

        // Stop when complete...still needs some tinkering.
        if (complete){
            clearInterval(refreshIntervalId);
        }
    }
    , movementRate);
}

//----------------------------------------------------------------------------------------//

// Constructing the initial Map

function valuesFromObject(inputObject){
    //See: http://stackoverflow.com/a/25797464/4898004.
    return Object.keys(inputObject).map(function(key){return inputObject[key]})
}

function individualGrantExtractor(d, amount, recipientUniqueGeo, orgFundingInfoTemp){

    var fromPoint = [d["lng"], d["lat"]];
    var toPoint = [d["lngFunder"], d["latFunder"]];

    //Add the lng and lat of an Org; to do: first check if it already exists.
    var orgLocation = [d["lng"], d["lat"]].map(parseFloat);

    //Add Movement of Fund
    var gmovement = {
            "funderName"         : d["FunderNameFull"],
            "grantRecipientOrg"  : d["OrganizationName"],
            "startDate"          : d["StartDate"],
            "movingGrantRadius"  : Math.sqrt(amount/Math.PI) * 0.009,
            "grantAmount"        : amount,
            "recipientUniqueGeo" : recipientUniqueGeo
    };

    return {"fromPoint" : fromPoint, "toPoint" : toPoint,
            "gmovement" : gmovement, "orgLocation" : orgLocation
    }
}

function drawMain(simulationSpeed) {
    var largestIndividualGrant = 0;
    var routesToDraw = [];
    var grantMovements = [];
    var funderNameAbreviation = {};
    var orgFundingInfoTemp = {};

    d3.json("data/starter_kit/data/world-topo-min.json", function(error, world) {
        var countries = topojson.feature(world, world.objects.countries).features;
        topo = countries;

        var country = g.selectAll(".country").data(topo);
        country.enter().insert("path")
                .attr("class", "country")
                .attr("d", path)
                .style("fill", "#383838");

        var offsetL = document.getElementById('container').offsetLeft+0;
        var offsetT = document.getElementById('container').offsetTop+10;

        d3.csv("data/funder_db.csv", function(error, funder){
            funder.forEach(function (d)
            {
                addFunderPoints(d["lng"], d["lat"], 10, d["funder"], d["colour"], true, 1, offsetL, offsetT);
                fundsDict[d["funder"]] = [d["lng"], d["lat"]].map(parseFloat);
                funderColors[d["funder"]] = d["colour"]

                funderNameAbreviation[d['funder']] = d['funder'].match(/\((.*?)\)/)[1]
            });

            d3.csv("data/funding_sample.csv", function(error, grant){
                grant.forEach(function (d)
                {
                    //Get the Current Grant
                    var amount = parseFloat(d["NormalizedAmount"]);

                    if (!(isNaN(amount))) {

                        //If this is the largest grant, update.
                        if (amount > largestIndividualGrant) {
                            largestIndividualGrant = amount;
                        }

                        var recipientUniqueGeo = (d["lng"] + d["lat"]).replace(/ /g, '')

                        //Update Grants by Orginization in the database.
                        if (orgFundingInfoTemp[recipientUniqueGeo] === undefined) {
                            orgFundingInfoTemp[recipientUniqueGeo] = amount
                        } else {
                            orgFundingInfoTemp[recipientUniqueGeo] += amount
                        }

                        var singleGrant = individualGrantExtractor(d, amount, recipientUniqueGeo, orgFundingInfoTemp);

                        grantMovements.push(singleGrant['gmovement'])
                        fundsDict[d["OrganizationName"]] = singleGrant['orgLocation']
                        routesToDraw.push(singleGrant['fromPoint'])
                        routesToDraw.push(singleGrant['toPoint'])

                    }
                });
                //Add DateBox
                addDate();

                //Work out the largest grant for a single Org.
                var largestTotalGrantByOrg = Math.max.apply(null, valuesFromObject(orgFundingInfoTemp))

                // ***Run the Simulation*** ///
                grantTranslateMaster(grantMovements,
                                    largestTotalGrantByOrg,
                                    largestIndividualGrant,
                                    simulationSpeed,
                                    funderNameAbreviation
                );

                //Clear orgFundingInfoTemp from memory
                orgFundingInfoTemp = {};
            });
        });
    });
}

//----------------------------------------------------------------------------------------//

// Tools for plotting funders

function dotColor(amount){
    if (parseFloat(amount) < 10000000){
        return "darkred"
    } else if (parseFloat(amount) >  10000000 && parseFloat(amount)  < 100000000){
        return "red"
    } else if (parseFloat(amount) >= 100000000 && parseFloat(amount) < 500000000){
        return "yellow"
    } else if (parseFloat(amount) >= 500000000 && parseFloat(amount) < 1000000000){
        return "lightgreen"
    } else if (parseFloat(amount) >= 1000000000){
        return "green"
    }
}

function funderCircleAppend(appendTo, x, y, color, opacity, id, r, info, offsetL, offsetT){
    appendTo.append("svg:circle")
            .attr("cx", x)
            .attr("cy", y)
            .attr("class","point")
            .style("fill", color)
            // .style("stroke", "white")
            .style("opacity", opacity)
            .attr("id", id)
            .attr("r", r)
            .on("mousemove", function(d, i) {
                showTooltip(d
                            , i
                            , "<strong>" + info + "</strong>"
                            , offsetL
                            , offsetT)
            })
            .on("mouseout",  function(d, i){
                hideTooltip(d, i)
            });
}

//function to add points and text to the map (used in plotting grants)
function addFunderPoints(lat, lon, amount, name, color, infoOverride, opacity, offsetL, offsetT) {

    var funderpoints = g.append("g").attr("class", "funderpoints");

    var location = projection([lat, lon]);
    var x = location[0];
    var y = location[1];
    var amountInitialScale = amount;
    var objectInfo = name;

    funderCircleAppend(funderpoints, x, y, color, opacity, amountInitialScale, amountInitialScale, objectInfo, offsetL, offsetT);
}

//----------------------------------------------------------------------------------------//

//General Mechanics

function redraw() {
    //to do:
    //Add Time Box scaling
    //Correct window resize (i.e., edit setup())
    width = document.getElementById("container").offsetWidth;
    height = width / 2;
    d3.select("svg").remove();
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

    // Change circle size based on zoom level.//

    //to dO: only scale points in view
    d3.selectAll(".funderpoints").selectAll("circle").attr("r", function (d, i){
        var currentAmount = d3.select(this).attr("id");
        return pointScale(currentAmount, s);
    });

    d3.selectAll(".institution").selectAll("circle").attr("r", function (d, i){
        var currentAmount = d3.select(this).datum();
        return pointScale(currentAmount, s);
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
//     console.log(projection.invert(d3.mouse(this)));
}

//----------------------------------------------------------------------------------------//

//Execute Draw

drawMain(simulationSpeed = 0.01) //smaller = faster.











