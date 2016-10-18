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

//To do: filter legend elements by agencies in the database passed.

//----------------------------------------------------------------------------------------//

//General Setup

d3.select(window).on("resize", throttle);

var zoom = d3.behavior.zoom()
                      .scaleExtent([1, 5000])
                      .on("zoom", zoomer);

// var width = document.getElementById("container").offsetWidth;
// var height = width / 2;

var	margin = {top: 0, right: 0, bottom: 0, left: 0},
	width  = document.getElementById("container").offsetWidth + 500 - margin.left - margin.right,
	height = document.getElementById("container").offsetWidth/2 + margin.bottom;

// Define the div for the tooltip
var div = d3.select("body").append("div")
                           .attr("class", "tooltip")
                           .style("opacity", 0);

//Init
// var topo, projection, path, svg, g;
var topo, projection, path, defs, filter, feMerge, text, legend, svgLwr, gLwr, svg, g;
var recipientRankings = {};
var funderGeoDict = {};
var dateRealTime = [];
var funderColors = {};
var fundingAgencyFlightStatus = {};

setup(width, height);
function setup(width, height){
    // dateRealTime = [];

    projection = d3.geo.mercator()
                       .translate([(width/1.45), (height/1)])
                       .scale(width / 1.35 / Math.PI);

    path = d3.geo.path().projection(projection);

    svg = d3.select("#container")
            .append("svg")
		    .attr("width", width + margin.left + margin.right)
		    .attr("height", height)
            .call(zoom)
            .on("click", click)
            .append("g");
            // .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    g = svg.append("g");

    svgLwr = d3.select("#container2")
        .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", 180)
        .on("click", click)
        .append("g");
    // .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    gLwr = svgLwr.append("g");

    //---------------------
    //Add Glow
    //See:
    // 1. http://www.visualcinnamon.com/2016/06/glow-filter-d3-visualization.html
    // 2. http://stackoverflow.com/a/19704735/4898004

    //Container for the gradients
    defs = svgLwr.append("defs");

    //Filter for the outside glow
    filter = defs.append("filter")
                    .attr("id","glow");

    filter.append("feGaussianBlur")
                    .attr("stdDeviation","5.5")
                    .attr("result","coloredBlur");

    feMerge = filter.append("feMerge");

    feMerge.append("feMergeNode")
                    .attr("in","coloredBlur");

    feMerge.append("feMergeNode")
                    .attr("in","SourceGraphic");

}

//----------------------------------------------------------------------------------------//

//Tooltip Functionality

var tooltip = d3.select("#container")
                .append("div")
                .attr("class", "tooltip hidden");

function showTooltip(d, i, info, offsetL, offsetT){
    if (d === 'void'){return;}
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
function addDate(startDate) {

    var xWidthAdjust = 50;
    var startingContainerWidth = document.getElementById("container").offsetWidth;

    text = svg.append("text")
                .attr("class", "datebox")
                .attr("x", startingContainerWidth - 300)         // make these
                .attr("y", (startingContainerWidth / 2) - 80)    // more robust.
                .attr("dy", ".35em")
                .attr("text-anchor", "middle")
                .style("font", "Lucida Grande")
                .style("font-size", "85px")
                .style("opacity", 0)
                .text(startDate);

    var bbox = text[0][0].getBBox();

    svg.insert('rect', 'text')
        .attr("class", "datebox")
        .attr('x', bbox.x - xWidthAdjust/2)
        .attr('y', bbox.y)
        .attr('width', bbox.width + xWidthAdjust)
        .attr('height', bbox.height)
        .style("fill", "white")
        .style("opacity", 0.35);

    svg.append("text")
        .attr("class", "datebox")
        .attr("x", startingContainerWidth - 300)         // make these
        .attr("y", (startingContainerWidth / 2) - 80)    // more robust.
        .attr("dy", ".35em")
        .attr("text-anchor", "middle")
        .style("font", "Lucida Grande")
        .style("opacity", 1)
        .style("font-size", "85px")
        .text(startDate);
}

function dateChecker(newDate, oldDate) {
    //Checks if 'newDate' is more recent
    //than 'oldDate'. If so, returns `true`.
    //Otherwise, returns `false`.
    //Format: DD-MM-YYYY.

    //Working Correctly?
    var oldSplit = oldDate.split("/").map(parseFloat);
    var newSplit = newDate.split("/").map(parseFloat);

    if (newSplit[2] > oldSplit[2]) {
        return true;
    } else if (newSplit[1] > oldSplit[1]) {
        return true;
    } else if (newSplit[0] > oldSplit[0]) {
        return true;
    }
    return false;
}

//----------------------------------------------------------------------------------------//

//Tooltip Funders Summary

function uniqueCountPreseve(inputList) {
    //See: http://stackoverflow.com/a/22011372/4898004
    //This is a very nice little algorithm for sorting
    //array elements by the number of their occurences
    //Returns an array of uniques.
    var map = inputList.reduce(function (p, c) {
        p[c] = (p[c] || 0) + 1;
        return p;
    }, {});
    var countArray = Object.keys(map).sort(function (a, b) {
        return map[a] < map[b];
    });
    return countArray
}

function orgListFormatter(orgList){

    var d = {};
    var tail = "";
    var uniqueOrgList = uniqueCountPreseve(orgList);
    var uniqueOrgListLast = uniqueOrgList[uniqueOrgList.length - 1];

    for (i in orgList){
        if (d[orgList[i]] === undefined){
            d[orgList[i]] = 1
        } else {
            d[orgList[i]] += 1
        }
    }

    var summaryString = "";
    var insetBreakSpent = false;
    for (i in uniqueOrgList){
        if (uniqueOrgList[i] === uniqueOrgListLast) {
            tail = ")";
        } else if ((i == 3) && (insetBreakSpent === false)){
            tail = ")" + "</br>"
            insetBreakSpent = true;
        } else {
            tail = "), ";
        }
        summaryString += uniqueOrgList[i] + " (" + d[uniqueOrgList[i]] + tail;
    }
    return summaryString;
}

function tooltipInfoFormater(destination, realTimeInfo, locID){
    var info = "<strong>" + destination + "</strong>" + " (#" + recipientRankings[destination] + ")" +"<br/>" +
                "<em>" + "Total Grants: " + "</em>" + accounting.formatMoney(parseFloat(realTimeInfo[locID][0])) +
                " USD" + "<br/>" + "<em>" + "Grants Awarded by: " + orgListFormatter(realTimeInfo[locID][1]) + "</em>"
    return info;
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

            //correct for the current zoom level.
            var sZoom = pointScale(s, zoom.scale());

            return "translate(" + p.x + "," + p.y + ") scale(" + sZoom + ")";
        }
    }
}

function terrestrialPoints(newDraw, grantToDraw, realTimeInfo, largestTotalGrantByOrg){

    //Model Params
    var c = 2.9; //drop to 2.7
    var k = 0.5; //increase to 0.8
    var sizeFloor = 1.5;

    //Get the current zoom level
    var s = zoom.scale();

    //Set unique ID and the name of final location
    var locID = grantToDraw["recipientUniqueGeo"];
    var destination = grantToDraw["grantRecipientOrg"];

    var funderAbbreiv = grantToDraw["funderName"].match(/\((.*?)\)/)[1];
    //Construct the info for the Point

    // var s = d3.event.scale; //Add to adjust radius based on current zoom
    var idClean = "loc" + locID.replace(/[^0-9a-z]/gi, "");

    //Scale the funding using the logistic function
    var scaledRadius = logistic_fn(x = realTimeInfo[locID][0], sizeFloor, largestTotalGrantByOrg, k, c)
    // if (scaledRadius < sizeFloor){scaledRadius += sizeFloor}

    if (newDraw === true) {
        var institution = g.append("g").attr("class", "institution");
        var location = projection(funderGeoDict[destination]);
        institution = g.append("g").attr("class", "institution");
        institution.append("svg:circle")
                    .attr("cx", location[0])
                    .attr("cy", location[1])
                    .attr("class", "point")
                    .attr("id", idClean)
                    .attr("r", pointScale(scaledRadius, s))
                    .datum(scaledRadius)
                    .style("fill", "white")
                    .style("opacity", 0.25)
                    .on("mousemove", function(d, i) {
                        showTooltip(d
                                    , i
                                    , tooltipInfoFormater(destination, realTimeInfo, locID)
                                    , document.getElementById('container').offsetLeft-20
                                    , document.getElementById('container').offsetTop+20
                    )})
                    .on("mouseout",  function(d, i) {
                        hideTooltip(d, i)
                    });
    } else {
        d3.selectAll(".institution")
            .select("#" + idClean)
            .attr("r", pointScale(scaledRadius, s))
            .datum(scaledRadius);
    }
}

function legendCircleActivityScaler(grantToDraw){
        d3.selectAll('#container2')
        .select("#" + grantToDraw["funderName"].match(/\((.*?)\)/)[1] + "_legend_circle_glower")
        .transition()
        .duration(500)
        .attr("r", function (d, i){
            var radius = d3.select(this).datum();
            if (fundingAgencyFlightStatus[grantToDraw['funderName']] > 0) {
                return radius*1.5;
            }
            else {return 0;}
        })
        .style("filter", "url(#glow)");
}


function transition(grantMovement, route, grantToDraw, newDraw, largestTotalGrantByOrg, realTimeInfo) {

    var l = route.node().getTotalLength();

    grantMovement.transition()
        .duration(l * 12)
        .attrTween("transform", delta(grantMovement, route.node()))
        .each("end", function() {
            //Delete the spent route.
            route.remove();

            if (fundingAgencyFlightStatus[grantToDraw['funderName']] > 0){
                 fundingAgencyFlightStatus[grantToDraw['funderName']] -= 1
            }

            //Scale the circles in the legend by circles current in flight
            legendCircleActivityScaler(grantToDraw)

            //Add points on the Earth when the grants lands
            setTimeout(terrestrialPoints(newDraw, grantToDraw, realTimeInfo, largestTotalGrantByOrg), 125);

        }).remove(); //remove the moving circle
}

function grantTranslate(grantToDraw, newDraw, largestTotalGrantByOrg, realTimeInfo) {

    var from = funderGeoDict[grantToDraw["funderName"]];
    var to = funderGeoDict[grantToDraw["grantRecipientOrg"]];

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

    transition(grantMovement, route, grantToDraw, newDraw, largestTotalGrantByOrg, realTimeInfo);
}

function grantTranslateMaster(arrayOfGrantsToDraw, largestTotalGrantByOrg, largestIndividualGrant, movementRate, funderNameAbbreviation){
    var newDraw = false;
    var priorFundingRecipients = [];
    var realTimeInfo = {};

    var i = 0;
    var complete = false;
    var animationIntervalID = setInterval(function(){
        if (i > arrayOfGrantsToDraw.length - 2) {complete = true;}

        newDraw = false;
        var grantToDraw = arrayOfGrantsToDraw[i];
        var grantAmount = grantToDraw["grantAmount"];
        var funderAbrev = funderNameAbbreviation[grantToDraw["funderName"]];

        if (priorFundingRecipients.indexOf(grantToDraw["recipientUniqueGeo"]) === -1){
            newDraw = true;

            priorFundingRecipients.push(grantToDraw["recipientUniqueGeo"]);
            realTimeInfo[grantToDraw["recipientUniqueGeo"]] = [grantAmount, [funderAbrev]];
        } else {
            var previousAmount = realTimeInfo[grantToDraw["recipientUniqueGeo"]][0]
            var previousOrgs  = realTimeInfo[grantToDraw["recipientUniqueGeo"]][1]

            realTimeInfo[grantToDraw["recipientUniqueGeo"]] = [
                   previousAmount + grantAmount
                ,  previousOrgs.concat(funderAbrev)
            ];
        }

        //Update Record of Airborn Grants
        if (!(grantToDraw['funderName'] in fundingAgencyFlightStatus)){
            fundingAgencyFlightStatus[grantToDraw['funderName']] = 1
        } else {
            fundingAgencyFlightStatus[grantToDraw['funderName']] += 1
        }

        grantTranslate(grantToDraw, newDraw, largestTotalGrantByOrg, realTimeInfo);

        //Update Date
        //This is here to insure a linear flow for the time stamp. Pretty rigorous procedure.
        //It is a bit of a fudge factor, but as the input funding csv will always be
        //in proper descending order prior to export from pandas in python, this *should* act to smooth
        //out erroneous date time updates which emerge from variability in d3 rendering.
        var newDateToDraw = grantToDraw["startDate"];
        if (dateRealTime.indexOf(newDateToDraw) === -1){
            dateRealTime.push(newDateToDraw)
            svg.selectAll('text').text(function(d){
                var currentDate = d3.select(this).text()
                if (dateChecker(newDateToDraw, currentDate)){
                    return newDateToDraw;
                } else{
                    return currentDate;
                }
            });
        }

        // Stop when complete...
        if (complete === true){
            //Remove all glow on exit.
            for (var key in fundingAgencyFlightStatus){
                d3.selectAll('#container2')
                    .select("#" + key.match(/\((.*?)\)/)[1] + "_legend_circle_glower")
                    .attr("r", 0)
            }
            clearInterval(animationIntervalID);
        }

        //Pump counter.
        i++;
    }
    , movementRate);
}

//----------------------------------------------------------------------------------------//

// Constructing the initial Map

function valuesFromObject(inputObject){
    //See: http://stackoverflow.com/a/25797464/4898004.
    return Object.keys(inputObject).map(function(key){return inputObject[key]})
}

function legendGenerator(legend, currentWidth, numberOfFunders){

    var legendCircleSize = 30;
    var spaceIncrement = currentWidth/numberOfFunders;
    var spacer = (currentWidth - currentWidth/spaceIncrement)/25;

    for (var key in funderColors) {
        var abbreiv = key.match(/\((.*?)\)/)[1];
        var fColor = funderColors[key];

        var legendCircleTypes = ['glower', 'reg'];

        for (var t in legendCircleTypes){
            legend.attr("class", "legend")
                .append("svg:circle")
                .attr("cx", 0 + spacer)
                .attr("cy", 75)
                .attr("class", "point")
                .style("fill", fColor)
                .attr("id", abbreiv + "_legend_circle_" + legendCircleTypes[t])
                .attr("r", legendCircleSize)
                .datum(legendCircleSize)
                .on("mousemove", function(d, i) {
                    var name = d3.select(this).attr("id").split("_")[0]
                    console.log(name)
                    if (t == 'glower'){d = 'void'}
                    showTooltip(d
                                , i
                                , name
                                , document.getElementById('container2').offsetLeft+20
                                , document.getElementById('container').offsetTop+20
                )})
                .on("mouseout",  function(d, i) {
                    hideTooltip(d, i)
                });
            }

            legend.attr("class", "legend")
                .append("text")
                .attr("x", 0 + spacer)
                .attr("y", 75 + 75)
                .attr("id", abbreiv + "_legend_text")
                .attr("dy", ".35em")
                .attr("text-anchor", "middle")
                .style("font", "Lucida Grande")
                .style("font-size", "40px")
                .style("opacity", 1)
                .text(abbreiv);

            spacer += spaceIncrement
    }
}

function individualGrantExtractor(d, amount, recipientUniqueGeo, orgFundingInfoTemp){

    //Add the lng and lat of an Org; to do: first check if it already exists.
    var orgLocation = [d["lng"], d["lat"]].map(parseFloat);

    //Add Movement of Fund
    var gmovement = {
            "funderName"         : d["FunderNameFull"],
            "grantRecipientOrg"  : d["OrganizationName"],
            "startDate"          : d["StartDate"],
            "uID"                : d["uID"],
            "movingGrantRadius"  : Math.sqrt(amount/Math.PI) * 0.05,
            "grantAmount"        : amount,
            "recipientUniqueGeo" : recipientUniqueGeo
    };
    return {"gmovement" : gmovement, "orgLocation" : orgLocation}
}

function drawMain(simulationSpeed) {
    var startDate = "";
    var largestIndividualGrant = 0;

    var routesToDraw = [];
    var grantMovements = [];
    var orgFundingInfoTemp = {};
    var funderNameAbbreviation = {};

    d3.json("data/starter_kit/data/world-topo-min.json", function(error, world) {
        var countries = topojson.feature(world, world.objects.countries).features;
        topo = countries;

        var country = g.selectAll(".country").data(topo);
        country.enter().insert("path")
                        .attr("class", "country")
                        .attr("d", path)
                        .style("fill", "#383838");

        var offsetL = document.getElementById("container").offsetLeft+0;
        var offsetT = document.getElementById("container").offsetTop+10;

        var numberOfFunders = 0;
        d3.csv("data/funder_db.csv", function(error, funder){
            funder.forEach(function (d) {
                addFunderPoints(d["lng"], d["lat"], funderCircleSize(10.5), d["funder"], d["colour"], true, 1, offsetL, offsetT);
                funderGeoDict[d["funder"]] = [d["lng"], d["lat"]].map(parseFloat);
                funderColors[d["funder"]] = d["colour"]
                funderNameAbbreviation[d['funder']] = d['funder'].match(/\((.*?)\)/)[1]
                numberOfFunders += 1
            });

            d3.csv("data/organization_rankings.csv", function(error, recipient) {
                recipient.forEach(function (d) {
                    recipientRankings[d['OrganizationName']] = parseInt(d['OrganizationRank'])
                })
            });

            //Add Legend
            var currentWidth = document.getElementById("container2").offsetWidth;
            legend = gLwr.append("g").attr("class", "legend");
            legendGenerator(legend, currentWidth, numberOfFunders)

            //Add Funding Information
            d3.csv("data/funding_sample.csv", function(error, grant){
                grant.forEach(function (d) {

                    //Get the Current Grant
                    var amount = parseFloat(d["NormalizedAmount"]);

                    if (!(isNaN(amount))) {

                        //Save the first date in the database
                        if (startDate === "") {
                            startDate = d["StartDate"];
                        }

                        var fromPoint = funderGeoDict[d['FunderNameFull']].map(String);
                        var toPoint = [d["lng"], d["lat"]];

                        //If this is the largest grant, update.
                        if (amount > largestIndividualGrant) {
                            largestIndividualGrant = amount;
                        }

                        var recipientUniqueGeo = (d["lng"] + d["lat"]).replace(/ /g, "") + d['OrganizationName']

                        //Update Grants by Orginization in the database.
                        if (orgFundingInfoTemp[recipientUniqueGeo] === undefined) {
                            orgFundingInfoTemp[recipientUniqueGeo] = amount
                        } else {
                            orgFundingInfoTemp[recipientUniqueGeo] += amount
                        }

                        var singleGrant = individualGrantExtractor(d, amount, recipientUniqueGeo, orgFundingInfoTemp);
                        grantMovements.push(singleGrant['gmovement']);

                        funderGeoDict[d["OrganizationName"]] = singleGrant['orgLocation'];
                        routesToDraw.push(fromPoint);
                        routesToDraw.push(toPoint);
                    }
                });
                //Add DateBox
                addDate(startDate);

                //Work out the largest grant for a single Org.
                var largestTotalGrantByOrg = Math.max.apply(null, valuesFromObject(orgFundingInfoTemp))

                // ***Run the Simulation*** ///
                grantTranslateMaster(grantMovements,
                                     largestTotalGrantByOrg,
                                     largestIndividualGrant,
                                     simulationSpeed,
                                     funderNameAbbreviation
                );

                //Clear orgFundingInfoTemp from memory
                orgFundingInfoTemp = {};
            });
        });
    });
}

//----------------------------------------------------------------------------------------//

// Tools for plotting funders

function funderCircleSize(circleSize){
    //build out.
    return circleSize;
}

function funderRedraw() {
    //refine to use already cached data.
    //not working...yet.
    g.selectAll(".point").remove()
    var offsetL = document.getElementById("container").offsetLeft+0;
    var offsetT = document.getElementById("container").offsetTop+10;
    d3.csv("data/funder_db.csv", function(error, funder) {
        funder.forEach(function (d) {
            addFunderPoints(d["lng"], d["lat"], funderCircleSize(11), d["funder"], d["colour"], true, 1, offsetL, offsetT);
        })
    })
}

function funderCircleAppend(appendTo, x, y, color, opacity, id, r, info, offsetL, offsetT){
    appendTo.append("svg:circle")
        .attr("cx", x)
        .attr("cy", y)
        .attr("class","point") //change to funderpoints?
        .style("fill", color)
        // .style("stroke", "white")
        // .style("opacity", opacity)
        .attr("id", id)
        .attr("r", r)
        .on("mousemove", function(d, i) {
            showTooltip(d
                        , i
                        , "<strong>" + info + "</strong>"
                        , document.getElementById('container').offsetLeft+0
                        , offsetT = document.getElementById('container').offsetTop+10
        )})
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
    d3.select("#container").select("svg").remove();
    d3.select("#container2").select("svg").remove();
    // svg.selectAll("*").remove()
    // d3.select("svgLwr").remove();
    // legend.remove()
    // gLwr.remove();
    setup(width, height);
    drawMain();
}

function pointScale(amount, zoomScale){
    // var rawFloor = 0.09;
    var size = amount * (5/zoomScale);

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
        (width/height) * (s - 1),
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
    d3.selectAll(".funderpoints")
        .selectAll("circle")
        .attr("r", function (d, i){
            var currentAmount = d3.select(this).attr("id");
            return pointScale(currentAmount, s);
    });

    d3.selectAll(".institution")
        .selectAll("circle")
        .attr("r", function (d, i){
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
    }, 100);
}

//geo translation on mouse click in map
function click() {
    // console.log(d3.mouse(this))
//    console.log(projection(d3.mouse(this)));
//     console.log(projection.invert(d3.mouse(this)));
}

//----------------------------------------------------------------------------------------//

//Execute Draw

drawMain(simulationSpeed = 0.01) //smaller = faster.

















































